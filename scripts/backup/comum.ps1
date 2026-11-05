<#
    Funções compartilhadas pelos scripts de backup e restauração.
    Carregado com dot-source:  . (Join-Path $PSScriptRoot "comum.ps1")
#>

$script:arquivoLog = $null

function Write-Log {
    param([string]$Mensagem, [string]$Nivel = "INFO")
    $linha = "{0} [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Nivel, $Mensagem
    Write-Host $linha
    if ($script:arquivoLog) { Add-Content -Path $script:arquivoLog -Value $linha -Encoding UTF8 }
}

function Read-EnvFile {
    param([string]$Caminho)
    $vars = @{}
    foreach ($linha in Get-Content -Path $Caminho -Encoding UTF8) {
        if ($linha -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
            $vars[$Matches[1]] = $Matches[2].Trim().Trim('"').Trim("'")
        }
    }
    return $vars
}

function Expand-Caminho {
    param([string]$Caminho)
    return [Environment]::ExpandEnvironmentVariables($Caminho)
}

function Get-Contexto {
    <#
        Lê o backup.config.json e o .env do projeto e devolve tudo que os
        scripts precisam. Usuário e nome do banco vêm do .env, para não
        duplicar configuração — e nenhuma senha fica nos scripts.
    #>
    param([string]$Config, [string]$NomeLog)

    if (-not (Test-Path $Config)) {
        throw "Configuração não encontrada: $Config. Copie backup.config.example.json para backup.config.json e ajuste os caminhos."
    }
    $cfg = Get-Content -Path $Config -Raw -Encoding UTF8 | ConvertFrom-Json

    $pastaLocal = Expand-Caminho $cfg.pastaLocal
    New-Item -ItemType Directory -Force -Path $pastaLocal | Out-Null
    $script:arquivoLog = Join-Path $pastaLocal $NomeLog

    $raiz = Resolve-Path (Join-Path $PSScriptRoot "..\..")
    $arquivoEnv = Join-Path $raiz ".env"
    if (-not (Test-Path $arquivoEnv)) { throw "Arquivo .env não encontrado em $raiz" }
    $vars = Read-EnvFile $arquivoEnv
    if (-not $vars["POSTGRES_USER"] -or -not $vars["POSTGRES_DB"]) {
        throw "POSTGRES_USER ou POSTGRES_DB ausente no .env"
    }

    return [pscustomobject]@{
        Cfg              = $cfg
        PastaLocal       = $pastaLocal
        Destinos         = @($cfg.destinos | Where-Object { $_ } | ForEach-Object { Expand-Caminho $_ })
        Diarios          = $(if ($cfg.manterDiarios) { [int]$cfg.manterDiarios } else { 30 })
        Mensais          = $(if ($cfg.manterMensais) { [int]$cfg.manterMensais } else { 12 })
        ContainerBanco   = $(if ($cfg.containerBanco) { $cfg.containerBanco } else { "postgres_db" })
        ContainerBackend = $(if ($cfg.containerBackend) { $cfg.containerBackend } else { "petshop_backend" })
        Usuario          = $vars["POSTGRES_USER"]
        Banco            = $vars["POSTGRES_DB"]
    }
}

function Test-Docker {
    & docker info --format "{{.ServerVersion}}" *> $null
    return ($LASTEXITCODE -eq 0)
}

function Confirm-Docker {
    # A máquina pode ter reiniciado e o Docker Desktop ainda não ter aberto.
    if (Test-Docker) { return }
    Write-Log "Docker não respondeu; iniciando o Docker Desktop..." "AVISO"
    $exe = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
    if (-not (Test-Path $exe)) { throw "Docker Desktop não encontrado em $exe" }
    Start-Process -FilePath $exe
    $limite = (Get-Date).AddMinutes(4)
    while ((Get-Date) -lt $limite) {
        Start-Sleep -Seconds 5
        if (Test-Docker) { Write-Log "Docker pronto."; return }
    }
    throw "O Docker não ficou pronto em 4 minutos."
}

function Confirm-Banco {
    param([string]$Container, [string]$Usuario, [string]$Banco)
    $estado = & docker inspect -f "{{.State.Running}}" $Container 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "O container '$Container' não existe. O sistema foi instalado com 'docker compose up -d'?"
    }
    if ("$estado".Trim() -ne "true") {
        Write-Log "Container '$Container' estava parado; iniciando..." "AVISO"
        & docker start $Container *> $null
    }
    $limite = (Get-Date).AddMinutes(2)
    while ((Get-Date) -lt $limite) {
        & docker exec $Container pg_isready -U $Usuario -d $Banco *> $null
        if ($LASTEXITCODE -eq 0) { return }
        Start-Sleep -Seconds 3
    }
    throw "O banco não ficou pronto em 2 minutos."
}

function New-Dump {
    <#
        Gera um dump compactado e já conferido, e devolve o caminho local.

        O dump é gerado DENTRO do container e depois copiado com 'docker cp'.
        Encadear a saída binária do pg_dump pelo PowerShell 5.1 corromperia o
        arquivo, porque ele converte o fluxo para texto.
    #>
    param([object]$Ctx, [string]$Banco, [string]$Nome)

    $tmp = "/tmp/$Nome"
    & docker exec $Ctx.ContainerBanco pg_dump -U $Ctx.Usuario -d $Banco -Fc -Z 9 -f $tmp
    if ($LASTEXITCODE -ne 0) { throw "pg_dump falhou (código $LASTEXITCODE)." }

    # Um backup que não restaura não serve: confere a integridade já aqui.
    & docker exec $Ctx.ContainerBanco pg_restore --list $tmp *> $null
    if ($LASTEXITCODE -ne 0) { throw "O dump gerado está corrompido (pg_restore --list falhou)." }

    $local = Join-Path $Ctx.PastaLocal $Nome
    & docker cp "$($Ctx.ContainerBanco):$tmp" $local *> $null
    $codigo = $LASTEXITCODE
    & docker exec $Ctx.ContainerBanco rm -f $tmp *> $null
    if ($codigo -ne 0 -or -not (Test-Path $local)) { throw "Falha ao copiar o dump para fora do container." }
    if ((Get-Item $local).Length -le 0) { throw "O dump saiu vazio." }
    return $local
}

function Invoke-Psql {
    # Executa uma consulta e devolve as linhas sem cabeçalho nem formatação.
    param([object]$Ctx, [string]$Banco, [string]$Sql)
    $saida = & docker exec $Ctx.ContainerBanco psql -U $Ctx.Usuario -d $Banco -t -A -c $Sql 2>$null
    if ($LASTEXITCODE -ne 0) { throw "Falha na consulta ao banco '$Banco'." }
    return @($saida | Where-Object { "$_".Trim() -ne "" })
}

function Get-ContagemTabelas {
    # Quantidade de registros por tabela — usado para conferir uma restauração.
    param([object]$Ctx, [string]$Banco)
    $tabelas = Invoke-Psql $Ctx $Banco "select tablename from pg_tables where schemaname = 'public' order by tablename;"
    $contagem = [ordered]@{}
    foreach ($t in $tabelas) {
        $nome = "$t".Trim()
        # Sem aspas no nome de propósito: o PowerShell 5.1 corrompe aspas duplas
        # em argumentos de programas externos, e as tabelas do sistema são todas
        # identificadores simples em minúsculas.
        $contagem[$nome] = [int]((Invoke-Psql $Ctx $Banco "select count(*) from $nome;") | Select-Object -First 1)
    }
    return $contagem
}
