@echo off
chcp 65001 >nul
REM Roda uma vez: cria o icone "Recanto Mini Dogs" na Area de Trabalho
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\Recanto Mini Dogs.lnk'); $s.TargetPath='%~dp0Abrir Sistema.bat'; $s.WorkingDirectory='%~dp0'; $s.IconLocation='%SystemRoot%\System32\shell32.dll,13'; $s.Description='Abrir o sistema do Recanto Mini Dogs'; $s.Save()"
if errorlevel 1 (
    echo Nao consegui criar o atalho.
) else (
    echo Pronto! O icone "Recanto Mini Dogs" foi criado na Area de Trabalho.
)
pause
