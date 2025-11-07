
# Instalador de chatbot local (Frontend + Backend)

function Write-Info($msg) {
    Write-Host "[INFO] $msg" -ForegroundColor Cyan
}
function Write-Success($msg) {
    Write-Host "[OK] $msg" -ForegroundColor Green
}
function Write-ErrorMsg($msg) {
    Write-Host "[ERROR] $msg" -ForegroundColor Red
}

function Test-Installation {
    Write-Info "Verificando dependencias..."

    try {
        # Verificar Node.js
        node -v | Out-Null
        Write-Success "Node.js instalado"
    } catch {
        Write-ErrorMsg "Node.js no está instalado. Instálalo desde https://nodejs.org/"
        exit 1
    }

    try {
        # Verificar Python
        python --version | Out-Null
        Write-Success "Python instalado"
    } catch {
        Write-ErrorMsg "Python no está instalado. Descárgalo desde https://www.python.org/"
        exit 1
    }

    try {
        # Verificar dependencias Python
        python -c "import fastapi, gpt4all, sqlalchemy; print('OK')" | Out-Null
        Write-Success "Dependencias Python instaladas"
    } catch {
        Write-ErrorMsg "Faltan dependencias de Python. Ejecuta: pip install fastapi gpt4all sqlalchemy"
        exit 1
    }
}

function Start-Frontend {
    Write-Info "Iniciando Frontend..."
    cd frontend
    npm install
    Start-Process powershell -ArgumentList "cd $(Get-Location); npm run dev"
    cd ..
}

function Start-Backend {
    Write-Info "Iniciando Backend..."
    cd backend
    Start-Process powershell -ArgumentList "cd $(Get-Location); python main.py"
    cd ..
}

Write-Info "==== Instalador Chatbot ===="
Test-Installation

Start-Frontend
Start-Backend

Write-Success "Todo listo 🚀"
Write-Host "Frontend: http://localhost:5173"
Write-Host "Backend: http://localhost:8000"
