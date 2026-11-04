<#
.SYNOPSIS
    Backup do banco de dados do Recanto Mini Dogs.

.DESCRIPTION
    1. Garante que o Docker e o container do Postgres estão no ar.
    2. Gera um dump compactado do banco e confere se ele é íntegro.
    3. Guarda na pasta local e copia para cada destino configurado — a pasta
       sincronizada do Google Drive/OneDrive, um HD externo etc.
    4. Rotação: mantém os últimos N backups e o último de cada mês.

    Destinos e retenção ficam em backup.config.json (ver LEIAME.md).

.PARAMETER Config
    Caminho do arquivo de configuração. Padrão: backup.config.json ao lado deste script.

.NOTES
    Códigos de saída: 0 = sucesso; 1 = falha; 2 = backup feito, mas algum destino falhou.
#>
param(
    [string]$Config = (Join-Path $PSScriptRoot "backup.config.json")
)

# 'Continue' de propósito: no Windows PowerShell 5.1, com 'Stop', qualquer
# texto que o docker escreva no stderr vira erro fatal. Os erros dos comandos
# nativos são tratados pelo $LASTEXITCODE.
$ErrorActionPreference = "Continue"
. (Join-Path $PSScriptRoot "comum.ps1")

function Invoke-Rotacao {
    <#
        Mantém os $Diarios backups mais recentes e, além deles, o último
        backup de cada um dos $Mensais meses mais recentes. Assim há histórico
        detalhado do último mês e um backup por mês do último ano, sem a pasta
        crescer para sempre. Só mexe em arquivos no padrão recanto_AAAA-MM-DD_HHMM.dump.
    #>
    param([string]$Pasta, [int]$Diarios, [int]$Mensais)

    $arquivos = @(Get-ChildItem -Path $Pasta -Filter "recanto_*.dump" -File -ErrorAction SilentlyContinue |
        ForEach-Object {
            if ($_.BaseName -match '^recanto_(\d{4}-\d{2}-\d{2})_(\d{4})$') {
                [pscustomobject]@{
                    Arquivo = $_
                    Data    = [datetime]::ParseExact("$($Matches[1]) $($Matches[2])", "yyyy-MM-dd HHmm", $null)
                }
            }
        } | Sort-Object Data -Descending)

    if ($arquivos.Count -eq 0) { return }

    $manter = @{}
    $arquivos | Select-Object -First $Diarios | ForEach-Object { $manter[$_.Arquivo.FullName] = $true }
    $arquivos |
        Group-Object { $_.Data.ToString("yyyy-MM") } |
        Sort-Object Name -Descending |
        Select-Object -First $Mensais |
        ForEach-Object {
            $ultimoDoMes = $_.Group | Sort-Object Data -Descending | Select-Object -First 1
            $manter[$ultimoDoMes.Arquivo.FullName] = $true
        }

    foreach ($item in $arquivos) {
        if (-not $manter.ContainsKey($item.Arquivo.FullName)) {
            Remove-Item -Path $item.Arquivo.FullName -Force
            Write-Log "Rotação: removido $($item.Arquivo.Name) de $Pasta"
        }
    }
}

try {
    $ctx = Get-Contexto -Config $Config -NomeLog "backup.log"
    Write-Log "==== Início do backup ===="

    Confirm-Docker
    Confirm-Banco -Container $ctx.ContainerBanco -Usuario $ctx.Usuario -Banco $ctx.Banco

    $nome = "recanto_{0}.dump" -f (Get-Date -Format "yyyy-MM-dd_HHmm")
    $arquivoLocal = New-Dump -Ctx $ctx -Banco $ctx.Banco -Nome $nome
    $tamanho = (Get-Item $arquivoLocal).Length
    Write-Log ("Dump gerado e conferido: {0} ({1:N0} KB)" -f $nome, ($tamanho / 1KB))

    # Destinos: um que falhe não impede os outros nem invalida o backup local.
    $falhas = 0
    foreach ($pasta in $ctx.Destinos) {
        $unidade = [IO.Path]::GetPathRoot($pasta)
        if ($unidade -and -not (Test-Path $unidade)) {
            # Caso normal de HD externo desconectado: avisa, mas não é erro.
            Write-Log "Destino indisponível (unidade $unidade não conectada): $pasta" "AVISO"
            continue
        }
        try {
            New-Item -ItemType Directory -Force -Path $pasta -ErrorAction Stop | Out-Null
            Copy-Item -Path $arquivoLocal -Destination $pasta -Force -ErrorAction Stop
            $copia = Join-Path $pasta $nome
            if ((Get-Item $copia -ErrorAction Stop).Length -ne $tamanho) { throw "o tamanho da cópia não confere" }
            Write-Log "Copiado para: $pasta"
            Invoke-Rotacao -Pasta $pasta -Diarios $ctx.Diarios -Mensais $ctx.Mensais
        }
        catch {
            $falhas++
            Write-Log "Falha ao copiar para ${pasta}: $($_.Exception.Message)" "ERRO"
        }
    }

    Invoke-Rotacao -Pasta $ctx.PastaLocal -Diarios $ctx.Diarios -Mensais $ctx.Mensais

    # Marcador simples para conferir rapidamente quando foi o último sucesso.
    Set-Content -Path (Join-Path $ctx.PastaLocal "ultimo_backup_ok.txt") -Encoding UTF8 `
        -Value ("{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm"), $nome)

    if ($falhas -gt 0) {
        Write-Log "==== Backup concluído, mas $falhas destino(s) falharam ====" "AVISO"
        exit 2
    }
    Write-Log "==== Backup concluído com sucesso ===="
    exit 0
}
catch {
    Write-Log $_.Exception.Message "ERRO"
    Write-Log "==== Backup FALHOU ====" "ERRO"
    exit 1
}
