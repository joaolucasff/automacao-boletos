@echo off
REM ============================================
REM Sistema de Envio de Boletos - Jota Jota
REM Duplo clique neste arquivo para abrir
REM ============================================

title Sistema de Boletos - Jota Jota
color 0B

echo.
echo ========================================
echo   Sistema de Boletos - Jota Jota
echo ========================================
echo.
echo Carregando interface grafica...
echo.

REM Ir para a pasta do script
cd /d "%~dp0"

REM Abrir interface grafica usando caminho completo do pythonw
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0Abrir_Interface.py"

REM Fechar este terminal automaticamente
exit
