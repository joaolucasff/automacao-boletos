@echo off
echo ============================================
echo GERADOR DE .EXE - Sistema Boletos JotaJota
echo ============================================
echo.

REM Ativar ambiente virtual
cd ..
call .venv\Scripts\activate.bat
cd _build_server

REM Limpar builds anteriores
echo [1/5] Limpando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Verificar se pyinstaller está instalado
echo [2/5] Verificando PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller nao encontrado. Instalando...
    pip install pyinstaller
)

REM Gerar .exe
echo [3/5] Gerando executavel...
echo (Isso pode demorar 5-10 minutos...)
pyinstaller build_sistema.spec --clean

REM Verificar se gerou com sucesso
if not exist "dist\SistemaBoletosJotaJota.exe" (
    echo [ERRO] Falha ao gerar .exe!
    pause
    exit /b 1
)

echo [4/5] Executavel gerado com sucesso!
echo.
echo Tamanho:
dir "dist\SistemaBoletosJotaJota.exe" | findstr "SistemaBoletosJotaJota.exe"
echo.

REM Renomear assinatura.jpg (se necessário)
if exist "Imagem1.jpg" (
    copy /y "Imagem1.jpg" "dist\assinatura.jpg"
    echo [5/5] Assinatura copiada para dist\assinatura.jpg
)

echo.
echo ============================================
echo CONCLUIDO!
echo.
echo Executavel: dist\SistemaBoletosJotaJota.exe
echo Assinatura: dist\assinatura.jpg
echo.
echo Deseja testar o executavel agora? (S/N)
set /p resposta=
if /i "%resposta%"=="S" (
    cd dist
    start "" "SistemaBoletosJotaJota.exe"
    cd ..
)
echo ============================================
pause
