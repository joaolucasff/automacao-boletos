@echo off
REM ========================================
REM Script para Copiar Sistema para Servidor
REM ========================================
REM
REM Este script copia APENAS os arquivos necessários,
REM excluindo a pasta venv (ambiente virtual Python)
REM
REM INSTRUÇÕES:
REM 1. Edite a linha DESTINO abaixo com o caminho do servidor
REM 2. Execute este arquivo (duplo clique)
REM 3. Aguarde a conclusão da cópia
REM ========================================

echo.
echo ========================================
echo   COPIA DO SISTEMA PARA SERVIDOR
echo ========================================
echo.

REM ===== CONFIGURAR AQUI =====
REM Mude este caminho para o caminho do seu servidor:
SET DESTINO=\\SERVIDOR\Compartilhado\BoletosAutomacao

REM ===========================

SET ORIGEM=C:\Users\User-OEM\Desktop\BoletosAutomação

echo [INFO] Origem: %ORIGEM%
echo [INFO] Destino: %DESTINO%
echo.

REM Verificar se destino existe
if not exist "%DESTINO%\" (
    echo [ERRO] Caminho de destino nao existe!
    echo [ERRO] Verifique se o servidor esta acessivel e o caminho esta correto.
    echo.
    pause
    exit /b 1
)

echo [INFO] Copiando arquivos (excluindo venv)...
echo.

REM Copiar tudo EXCETO a pasta venv
xcopy "%ORIGEM%" "%DESTINO%" /E /I /H /Y /EXCLUDE:%ORIGEM%\exclude_copy.txt

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo   COPIA CONCLUIDA COM SUCESSO!
    echo ========================================
    echo.
    echo Proximos passos:
    echo 1. Edite o arquivo config.py no servidor
    echo 2. Mude a linha BASE_DIR para o caminho do servidor
    echo 3. Execute: python config.py para testar
    echo.
) else (
    echo.
    echo ========================================
    echo   ERRO DURANTE A COPIA
    echo ========================================
    echo.
    echo Codigo de erro: %ERRORLEVEL%
    echo.
)

pause
