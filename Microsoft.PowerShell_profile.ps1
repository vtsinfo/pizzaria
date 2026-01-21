function prompt {
    # Lógica de Desativação Automática
    if ($env:VIRTUAL_ENV -ne $null) {
        # Obtém o diretório raiz onde o venv reside
        $venvRoot = Split-Path -Path $env:VIRTUAL_ENV -Parent
        $currentDir = (Get-Location).Path

        # Se o diretório atual não começar com o caminho da raiz do venv, desativa
        if (-not ($currentDir.StartsWith($venvRoot))) {
            Write-Host "[VTS] Saindo da pasta do projeto. Desativando venv..." -ForegroundColor Yellow
            deactivate
        }
    }

    # Verifica se existe uma pasta venv no diretório atual
    if (Test-Path ".\venv\Scripts\Activate.ps1") {
        # Verifica se o venv já não está ativo para evitar re-ativação redundante
        if ($env:VIRTUAL_ENV -eq $null) {
            Write-Host "[VTS] Ativando ambiente virtual encontrado..." -ForegroundColor Cyan
            . .\venv\Scripts\Activate.ps1
        }
    }
    
    # Mantém o comportamento padrão do prompt (exibe o caminho atual)
    $promptPath = $(Get-Location)
    Write-Output "PS $promptPath> "
    return " "
}