@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Recanto Mini Dogs
echo.
echo  ==========================================
echo     Recanto Mini Dogs - abrindo o sistema
echo  ==========================================
echo.

if not exist ".env" (
    echo  [!] Nao encontrei o arquivo de configuracao ^(.env^) nesta pasta.
    echo      Chame quem cuida do sistema para ajudar.
    echo.
    pause
    exit /b 1
)

where docker >nul 2>&1
if errorlevel 1 (
    echo  [!] O Docker Desktop nao esta instalado neste computador.
    echo      Chame quem cuida do sistema para ajudar.
    echo.
    pause
    exit /b 1
)

REM ---------- 1. Docker ligado? ----------
docker info >nul 2>&1
if not errorlevel 1 goto docker_ok

echo  [1/4] Ligando o Docker Desktop... isso pode levar ate 2 minutos.
start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
set /a tentativas=0
:esperar_docker
timeout /t 5 /nobreak >nul
docker info >nul 2>&1
if not errorlevel 1 goto docker_ok
set /a tentativas+=1
if %tentativas% lss 48 goto esperar_docker
echo.
echo  [!] O Docker nao ligou. Reinicie o computador e tente de novo.
echo.
pause
exit /b 1

:docker_ok
echo  [1/4] Docker ligado.

REM ---------- 2. Subir o sistema ----------
REM Use "Abrir Sistema.bat atualizar" depois de receber uma versao nova do sistema
set OPCAO=
if /i "%~1"=="atualizar" set OPCAO=--build
echo  [2/4] Iniciando o sistema... na primeira vez pode demorar alguns minutos.
docker compose -f docker-compose.local.yml up -d %OPCAO% >"%TEMP%\recanto_docker.log" 2>&1
if errorlevel 1 (
    echo.
    echo  [!] Nao consegui iniciar o sistema. Detalhes em: %TEMP%\recanto_docker.log
    echo      Mande esse arquivo para quem cuida do sistema.
    echo.
    pause
    exit /b 1
)

REM ---------- 3. Esperar o site responder ----------
echo  [3/4] Aguardando o sistema ficar pronto...
set /a tentativas=0
:esperar_site
curl -s -f -o nul http://localhost/ >nul 2>&1
if not errorlevel 1 goto site_ok
set /a tentativas+=1
if %tentativas% geq 60 goto site_demorou
timeout /t 3 /nobreak >nul
goto esperar_site

:site_demorou
echo.
echo  [!] O sistema demorou demais para responder.
echo      Espere um minuto e abra este atalho de novo.
echo.
pause
exit /b 1

:site_ok

REM ---------- 4. Copia de seguranca (1 por dia) ----------
echo  [4/4] Verificando a copia de seguranca...
for /f "tokens=1,* delims==" %%A in ('findstr /b "POSTGRES_USER=" .env') do set PGUSUARIO=%%B
for /f %%D in ('powershell -nologo -noprofile -command "Get-Date -Format yyyy-MM-dd"') do set HOJE=%%D
set PASTA_BACKUP=%USERPROFILE%\Documents\Backups Recanto Mini Dogs
if not exist "%PASTA_BACKUP%" mkdir "%PASTA_BACKUP%"
set ARQ_BACKUP=%PASTA_BACKUP%\backup_%HOJE%.sql
if not exist "%ARQ_BACKUP%" (
    docker exec postgres_db pg_dumpall -U %PGUSUARIO% >"%ARQ_BACKUP%" 2>nul
    for %%F in ("%ARQ_BACKUP%") do if %%~zF equ 0 del "%ARQ_BACKUP%"
)
REM apaga copias com mais de 30 dias
forfiles /p "%PASTA_BACKUP%" /m backup_*.sql /d -30 /c "cmd /c del @path" >nul 2>&1

echo.
echo  Tudo pronto! Abrindo o sistema no navegador...
start "" http://localhost
timeout /t 3 /nobreak >nul
exit /b 0
