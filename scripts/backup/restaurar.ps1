<#
.SYNOPSIS
    Restaura um backup do banco de dados do Recanto Mini Dogs.

.DESCRIPTION
    Modo teste (-Teste): restaura o backup num banco temporário, mostra a
    quantidade de registros de cada tabela ao lado do banco atual e apaga o
    temporário. NÃO toca nos dados reais — serve para provar que o backup
    realmente restaura. É o que o teste semanal agendado executa.

    Modo real (sem -Teste): substitui os dados do banco pelos do backup.
    Antes disso, faz um backup de segurança do estado atual
    (pre-restauracao_*.dump) e para o backend, para ninguém gravar no meio
    da troca.

.PARAMETER Arquivo
    Dump a restaurar. Se omitido, usa o backup mais recente da pasta local.

.PARAMETER Teste
    Restaura num banco temporário, sem tocar nos dados reais.

.PARAMETER Forcar
    Pula a confirmação digitada do modo real. Use com cuidado.

.PARAMETER BancoDestino
    Avançado: restaura em outro banco em vez do configurado no .env.

.EXAMPLE
    .\restaurar.ps1 -Teste
    Confere se o backup mais recente restaura.

.EXAMPLE
    .\restaurar.ps1 -Arquivo "G:\Meu Drive\Backups Recanto Mini Dogs\recanto_2026-10-20_1800.dump"
    Substitui os dados atuais pelos do backup de 20/10.
#>
param(
    [string]$Arquivo,
    [switch]$Teste,
    [switch]$Forcar,
    [string]$BancoDestino,
    [string]$Config = (Join-Path $PSScriptRoot "backup.config.json")
)

# Ver comentário em backup.ps1 sobre 'Continue' no PowerShell 5.1.
$ErrorActionPreference = "Continue"
. (Join-Path $PSScriptRoot "comum.ps1")

function Restore-Dump {
    param([object]$Ctx, [string]$ArquivoLocal, [string]$Banco, [switch]$Limpar)

    $tmp = "/tmp/restaurar.dump"
    & docker cp $ArquivoLocal "$($Ctx.ContainerBanco):$tmp" *> $null
    if ($LASTEXITCODE -ne 0) { throw "Falha ao enviar o arquivo para o container." }

    $argumentos = @("exec", $Ctx.ContainerBanco, "pg_restore", "-U", $Ctx.Usuario, "-d", $Banco,
        "--no-owner", "--exit-on-error")
    if ($Limpar) { $argumentos += @("--clean", "--if-exists") }
    $argumentos += $tmp

    & docker @argumentos
    $codigo = $LASTEXITCODE
    & docker exec $Ctx.ContainerBanco rm -f $tmp *> $null
    if ($codigo -ne 0) { throw "pg_restore falhou (código $codigo)." }
}

function Write-Contagem {
    param([System.Collections.IDictionary]$Principal, [System.Collections.IDictionary]$Comparar,
          [string]$Titulo1, [string]$Titulo2)
    Write-Log ("  {0,-26} {1,12} {2,12}" -f "Tabela", $Titulo1, $Titulo2)
    foreach ($t in $Principal.Keys) {
        $outro = if ($Comparar -and $Comparar.Contains($t)) { $Comparar[$t] } else { "-" }
        Write-Log ("  {0,-26} {1,12} {2,12}" -f $t, $Principal[$t], $outro)
    }
}

try {
    $ctx = Get-Contexto -Config $Config -NomeLog "restauracao.log"
    $bancoAlvo = if ($BancoDestino) { $BancoDestino } else { $ctx.Banco }

    if (-not $Arquivo) {
        $ultimo = Get-ChildItem -Path $ctx.PastaLocal -Filter "recanto_*.dump" -File -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending | Select-Object -First 1
        if (-not $ultimo) { throw "Nenhum backup encontrado em $($ctx.PastaLocal)." }
        $Arquivo = $ultimo.FullName
    }
    if (-not (Test-Path $Arquivo)) { throw "Arquivo não encontrado: $Arquivo" }
    $Arquivo = (Resolve-Path $Arquivo).Path

    $modo = if ($Teste) { "TESTE" } else { "REAL" }
    Write-Log "==== Restauração ($modo) de $(Split-Path $Arquivo -Leaf) ===="

    Confirm-Docker
    Confirm-Banco -Container $ctx.ContainerBanco -Usuario $ctx.Usuario -Banco $ctx.Banco

    # ── Modo teste ──────────────────────────────────────────────────────────
    if ($Teste) {
        $bancoTeste = "recanto_teste_restauracao"
        Invoke-Psql $ctx "postgres" "drop database if exists $bancoTeste;" | Out-Null
        Invoke-Psql $ctx "postgres" "create database $bancoTeste;" | Out-Null
        try {
            Restore-Dump -Ctx $ctx -ArquivoLocal $Arquivo -Banco $bancoTeste
            $doBackup = Get-ContagemTabelas $ctx $bancoTeste
            $atual = Get-ContagemTabelas $ctx $ctx.Banco
        }
        finally {
            # O banco temporário sai sempre, mesmo se a restauração falhar.
            Invoke-Psql $ctx "postgres" "drop database if exists $bancoTeste;" | Out-Null
        }

        if ($doBackup.Count -eq 0) { throw "O backup restaurou, mas não trouxe nenhuma tabela." }
        Write-Log "Backup restaurado num banco temporário (já apagado). Registros por tabela:"
        Write-Contagem -Principal $doBackup -Comparar $atual -Titulo1 "No backup" -Titulo2 "Hoje"
        Write-Log "==== Teste de restauração OK ===="
        exit 0
    }

    # ── Modo real ───────────────────────────────────────────────────────────
    if (-not $Forcar) {
        Write-Host ""
        Write-Host "ATENÇÃO: os dados atuais do banco '$bancoAlvo' serão SUBSTITUÍDOS pelos do backup:" -ForegroundColor Yellow
        Write-Host "  $Arquivo" -ForegroundColor Yellow
        Write-Host "Antes disso, um backup de segurança do estado atual será feito." -ForegroundColor Yellow
        $resposta = Read-Host "Digite RESTAURAR para continuar"
        if ($resposta -ne "RESTAURAR") {
            Write-Log "Restauração cancelada pelo usuário."
            exit 0
        }
    }

    # Rede de segurança: se o backup escolhido for o errado, dá para voltar.
    # Nome fora do padrão recanto_* de propósito, para a rotação não apagá-lo.
    $nomeSeguranca = "pre-restauracao_{0}.dump" -f (Get-Date -Format "yyyy-MM-dd_HHmmss")
    $seguranca = New-Dump -Ctx $ctx -Banco $bancoAlvo -Nome $nomeSeguranca
    Write-Log "Backup de segurança do estado atual: $seguranca"

    $backendParado = $false
    $estadoBackend = & docker inspect -f "{{.State.Running}}" $ctx.ContainerBackend 2>$null
    if ($LASTEXITCODE -eq 0 -and "$estadoBackend".Trim() -eq "true") {
        & docker stop $ctx.ContainerBackend *> $null
        $backendParado = $true
        Write-Log "Backend parado durante a restauração."
    }
    try {
        Restore-Dump -Ctx $ctx -ArquivoLocal $Arquivo -Banco $bancoAlvo -Limpar
    }
    finally {
        if ($backendParado) {
            & docker start $ctx.ContainerBackend *> $null
            Write-Log "Backend reiniciado."
        }
    }

    Write-Log "Dados restaurados. Registros por tabela:"
    Write-Contagem -Principal (Get-ContagemTabelas $ctx $bancoAlvo) -Titulo1 "Registros" -Titulo2 ""
    Write-Log "==== Restauração concluída ===="
    Write-Log "Para desfazer, restaure o backup de segurança: $seguranca"
    exit 0
}
catch {
    Write-Log $_.Exception.Message "ERRO"
    Write-Log "==== Restauração FALHOU ====" "ERRO"
    exit 1
}
