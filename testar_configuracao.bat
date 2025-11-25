@echo off
REM ========================================
REM Testar Configuração do Sistema
REM ========================================

echo.
echo ========================================
echo   TESTE DE CONFIGURACAO
echo ========================================
echo.

REM ===== CONFIGURAR AQUI =====
REM Se você ainda está testando localmente, deixe assim:
SET PASTA=C:\Users\User-OEM\Desktop\BoletosAutomação

REM Quando mover para o servidor, mude para:
REM SET PASTA=\\SERVIDOR\Compartilhado\BoletosAutomacao
REM ===========================

echo [INFO] Testando pasta: %PASTA%
echo.

REM Verificar se a pasta existe
if not exist "%PASTA%\config.py" (
    echo [ERRO] Arquivo config.py nao encontrado em: %PASTA%
    echo [ERRO] Verifique se o caminho esta correto.
    echo.
    pause
    exit /b 1
)

REM Ir para a pasta e executar o teste
cd /d "%PASTA%"
python config.py

echo.
echo ========================================
pause
