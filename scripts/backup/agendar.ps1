<#
.SYNOPSIS
    Agenda o backup diário e o teste semanal de restauração no Agendador de
    Tarefas do Windows.

.DESCRIPTION
    Rode UMA vez, na máquina onde o sistema está instalado, logado com o
    mesmo usuário que usa o Docker Desktop. Cria duas tarefas:

    - Backup diário, no horário de -Horario.
    - Teste semanal de restauração (segunda-feira, no horário de
      -HorarioTeste): restaura o backup mais recente num banco temporário,
      para provar que os backups continuam servindo.

    Se o computador estiver desligado no horário marcado, a tarefa roda
    assim que ele for ligado (opção "executar o mais cedo possível").

.PARAMETER Horario
    Horário do backup diário. Prefira um horário em que a máquina costuma
    estar ligada — o fim do expediente pega o trabalho do dia inteiro.

.PARAMETER HorarioTeste
    Horário do teste semanal de restauração (segunda-feira).

.PARAMETER Remover
    Apaga as duas tarefas.

.EXAMPLE
    .\agendar.ps1
    .\agendar.ps1 -Horario 17:30
    .\agendar.ps1 -Remover
#>
param(
    [string]$Horario = "18:00",
    [string]$HorarioTeste = "12:00",
    [switch]$Remover
)

$nomeBackup = "Recanto Mini Dogs - Backup diario"
$nomeTeste = "Recanto Mini Dogs - Teste semanal de restauracao"

if ($Remover) {
    foreach ($nome in @($nomeBackup, $nomeTeste)) {
        if (Get-ScheduledTask -TaskName $nome -ErrorAction SilentlyContinue) {
            Unregister-ScheduledTask -TaskName $nome -Confirm:$false
            Write-Host "Removida: $nome"
        }
    }
    exit 0
}

if (-not (Test-Path (Join-Path $PSScriptRoot "backup.config.json"))) {
    Write-Host "Crie primeiro o backup.config.json (copie backup.config.example.json e ajuste os caminhos)." -ForegroundColor Red
    exit 1
}

$backup = Join-Path $PSScriptRoot "backup.ps1"
$restaurar = Join-Path $PSScriptRoot "restaurar.ps1"

# Roda com o usuário logado (o Docker Desktop precisa da sessão dele).
$opcoes = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

$acaoBackup = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$backup`""
Register-ScheduledTask -TaskName $nomeBackup -Force `
    -Action $acaoBackup `
    -Trigger (New-ScheduledTaskTrigger -Daily -At $Horario) `
    -Settings $opcoes `
    -Description "Gera o backup do banco do Recanto Mini Dogs e copia para os destinos configurados." | Out-Null

$acaoTeste = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$restaurar`" -Teste"
Register-ScheduledTask -TaskName $nomeTeste -Force `
    -Action $acaoTeste `
    -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At $HorarioTeste) `
    -Settings $opcoes `
    -Description "Restaura o backup mais recente num banco temporário para confirmar que ele funciona." | Out-Null

Write-Host "Tarefas criadas:" -ForegroundColor Green
Write-Host "  - $nomeBackup  (todo dia às $Horario)"
Write-Host "  - $nomeTeste  (segundas às $HorarioTeste)"
Write-Host "Confira no 'Agendador de Tarefas' do Windows. Para testar agora:"
Write-Host "  Start-ScheduledTask -TaskName '$nomeBackup'"
