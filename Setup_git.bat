@echo off
echo ========================================
echo Script de Configuracao do Git
echo Pizzaria Colonial - VTS
echo ========================================
echo.

REM Verifica se o Git esta instalado
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Git nao encontrado! Instale o Git primeiro.
    echo Download: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo [1/5] Configurando usuario Git...
git config user.name "vtsinfo"
git config user.email "tercio@vts.com.br"
echo Usuario configurado: vtsinfo ^<tercio@vts.com.br^>
echo.

echo [2/5] Verificando repositorio remoto...
git remote -v
if %errorlevel% neq 0 (
    echo [INFO] Configurando repositorio remoto...
    git remote add origin https://github.com/vtsinfo/pizzaria.git
    echo Remoto configurado: https://github.com/vtsinfo/pizzaria.git
) else (
    echo Remoto ja configurado.
)
echo.

echo [3/5] Buscando atualizacoes do repositorio remoto...
git fetch origin
if %errorlevel% neq 0 (
    echo [AVISO] Erro ao buscar atualizacoes. Verifique sua conexao.
)
echo.

echo [4/5] Verificando status do repositorio local...
git status
echo.

echo [5/5] Puxando ultimas alteracoes...
git pull origin main
if %errorlevel% neq 0 (
    echo [AVISO] Erro ao fazer pull. Pode haver conflitos ou o repositorio nao esta inicializado.
    echo Execute manualmente: git pull origin main
)
echo.

echo ========================================
echo Configuracao concluida!
echo ========================================
echo.
echo Configuracao atual:
git config user.name
git config user.email
echo.
echo Repositorio remoto:
git remote get-url origin
echo.
pause