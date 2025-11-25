@echo off
REM ========================================
REM Criar Atalho do Sistema de Boletos
REM na Area de Trabalho
REM ========================================

echo.
echo ========================================
echo   CRIAR ATALHO - SISTEMA DE BOLETOS
echo ========================================
echo.

REM Caminho do sistema no servidor (ajuste se necessário)
SET CAMINHO_SISTEMA=Z:\COBRANÇA\EnvioDeBoletosAutomatico\SistemaBoletosJotaJota.exe

REM Caminho da área de trabalho do usuário
SET DESKTOP=%USERPROFILE%\Desktop

REM Nome do atalho
SET NOME_ATALHO=Sistema de Boletos - Jota Jota.lnk

echo [INFO] Criando atalho em: %DESKTOP%
echo [INFO] Apontando para: %CAMINHO_SISTEMA%
echo.

REM Criar atalho usando PowerShell
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\%NOME_ATALHO%'); $Shortcut.TargetPath = '%CAMINHO_SISTEMA%'; $Shortcut.WorkingDirectory = 'Z:\COBRANÇA\EnvioDeBoletosAutomatico'; $Shortcut.IconLocation = 'shell32.dll,165'; $Shortcut.Description = 'Sistema de Envio de Boletos - Jota Jota'; $Shortcut.Save()"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo   ATALHO CRIADO COM SUCESSO!
    echo ========================================
    echo.
    echo Arquivo: %NOME_ATALHO%
    echo Local: Area de Trabalho
    echo.
    echo Agora voce pode clicar no atalho para abrir o sistema!
    echo.
) else (
    echo.
    echo [ERRO] Falha ao criar atalho
    echo.
)

pause
