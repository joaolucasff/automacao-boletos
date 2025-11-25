@echo off
REM ========================================
REM Remove arquivo "nul" problemático
REM ========================================

echo.
echo Procurando e removendo arquivo "nul"...
echo.

REM Procurar em toda a pasta (exceto venv que não é necessária)
for /r "C:\Users\User-OEM\Desktop\BoletosAutomação" %%F in (nul) do (
    if exist "%%F" (
        echo [ENCONTRADO] %%F
        del /F /Q "%%F" 2>nul
        if %ERRORLEVEL% EQU 0 (
            echo [OK] Removido com sucesso
        ) else (
            echo [AVISO] Nao foi possivel remover
        )
    )
)

echo.
echo Concluido!
echo.
pause
