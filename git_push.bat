@echo off
echo ========================================
echo Git Commit e Push Automatizado
echo ========================================
echo.

set /p msg="Digite a mensagem do commit: "

if "%msg%"=="" (
    echo [ERRO] Mensagem de commit obrigatoria!
    pause
    exit /b 1
)

echo.
echo [1/3] Adicionando arquivos...
git add .

echo.
echo [2/3] Commitando...
git commit -m "%msg%"

echo.
echo [3/3] Enviando para o GitHub...
git push origin main

echo.
echo ========================================
echo Concluido!
echo ========================================
pause