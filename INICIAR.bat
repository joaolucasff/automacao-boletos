@echo off
title Sistema de Boletos - Jota Jota
color 0A

echo.
echo ========================================
echo   Sistema de Boletos - Jota Jota
echo ========================================
echo.
echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo.
echo Iniciando interface grafica...
python src\InterfaceBoletos.py

pause
