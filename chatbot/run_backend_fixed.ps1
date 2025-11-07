# Chatbot Startup Script (robust, path-relative)
# run_backend_fixed.ps1

param(
    [switch]$SkipInstall = $false,
    [switch]$UseVite = $false,          # start Vite dev server if possible
    [switch]$ReinstallFront = $false,   # force npm install in frontend
    [string]$AdminKey = 'admin123',
    [string]$HostIp = 'auto',           # 'auto', hostname, ip, ip:puerto o URL completa
    [switch]$LanMode = $false           # imprime URLs LAN si está activo
)

$ErrorActionPreference = 'Stop'

# Configurar UTF-8 para la consola de PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
$env:PYTHONIOENCODING = 'utf-8'

function Write-Status {
    param($Message, $Type = 'INFO')
    $colors = @{
        'INFO'    = 'Cyan'
        'SUCCESS' = 'Green'
        'WARNING' = 'Yellow'
        'ERROR'   = 'Red'
    }
    Write-Host "[$Type] $Message" -ForegroundColor $colors[$Type]
}

# Resolve paths relative to the script's location
$projectPath  = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath  = Join-Path $projectPath 'backend'
$frontendPath = Join-Path $projectPath 'frontend'
$logsPath     = Join-Path $projectPath 'logs'
$venvPath     = Join-Path $projectPath 'venv'
$venvPython   = Join-Path $venvPath 'Scripts\python.exe'

# Prepare logs
if (!(Test-Path $logsPath)) { New-Item -ItemType Directory -Path $logsPath | Out-Null }
$runLog = Join-Path $logsPath 'run_backend.log'
try { Stop-Transcript | Out-Null } catch {}
Start-Transcript -Path $runLog -Append | Out-Null

Write-Host ''
Write-Host '=============================================' -ForegroundColor Green
Write-Host '   Chatbot - Startup (Windows/PS)' -ForegroundColor Green
Write-Host '=============================================' -ForegroundColor Green
Write-Host ''


# Environment variables used by backend
$env:ADMIN_API_KEY   = $AdminKey
$env:GPT4ALL_DEVICE  = 'cpu'
$env:CHATBOT_TEMP    = '0.3'

# --- Helper: check command availability
function Test-Command($name) {
    return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

function Get-PrimaryIPv4 {
    try {
        $candidates = Get-NetIPAddress -AddressFamily IPv4 -PrefixOrigin Manual, Dhcp -ErrorAction Stop |
            Where-Object { $_.IPAddress -and $_.IPAddress -ne '127.0.0.1' -and $_.IPAddress -notlike '169.254*' } |
            Sort-Object -Property SkipAsSource, InterfaceIndex, IPAddress

        if ($candidates) {
            foreach ($candidate in $candidates) {
                if ($candidate.SkipAsSource) { continue }
                return $candidate.IPAddress
            }
            return $candidates[0].IPAddress
        }
    } catch {
        Write-Status "No se pudo detectar IP LAN automáticamente: $($_.Exception.Message)" 'WARNING'
    }
    return '127.0.0.1'
}

function Get-BaseUrlFromHost($hostValue) {
    if ([string]::IsNullOrWhiteSpace($hostValue) -or $hostValue.Trim().ToLower() -eq 'auto') {
        return $null
    }

    $trimmed = $hostValue.Trim().TrimEnd('/')

    if ($trimmed -match '^[a-zA-Z][a-zA-Z0-9+.-]*://') {
        return $trimmed
    }

    if ($trimmed -match ':\d+$') {
        return "http://$trimmed"
    }

    return "http://$($trimmed):8000"
}

# --- Python check and venv setup
try {
    if (!(Test-Path $projectPath)) {
        Write-Status 'Proyecto no encontrado: $projectPath' 'ERROR'
        throw 'Ruta invalida'
    }

    # Prefer 'python', fallback to 'py -3'
    $pythonCmd = $null
    if (Test-Command 'python') { $pythonCmd = 'python' }
    elseif (Test-Command 'py') { $pythonCmd = 'py -3' }

    if (-not $pythonCmd) { throw 'Python no encontrado. Instala Python 3.9+ desde https://www.python.org/downloads/' }
    $pyVer = & $pythonCmd --version 2>&1
    Write-Status "Python detectado: $pyVer" 'SUCCESS'

    if (!(Test-Path $venvPython)) {
        Write-Status 'Creando entorno virtual...' 'INFO'
        & $pythonCmd -m venv $venvPath
        Write-Status 'Entorno virtual creado' 'SUCCESS'
    }

    Write-Status 'Activando venv y actualizando pip...' 'INFO'
    & "$venvPath\Scripts\Activate.ps1"
    & $venvPython -m pip install --upgrade pip
} catch {
    Write-Status "Error con Python/venv: $($_.Exception.Message)" 'ERROR'
    Write-Host 'Consulta el log: $runLog' -ForegroundColor Yellow
    Read-Host 'Pulsa ENTER para salir'
    Stop-Transcript | Out-Null
    exit 1
}

# --- Backend deps
try {
    if (-not $SkipInstall) {
        $req = Join-Path $backendPath 'requirements.txt'
        if (!(Test-Path $req)) { throw 'requirements.txt no existe en backend' }
        Write-Status 'Instalando dependencias backend...' 'INFO'
        & $venvPython -m pip install -r $req
        Write-Status 'Dependencias backend OK' 'SUCCESS'
    } else {
        Write-Status 'SkipInstall activo: omitidas dependencias backend' 'WARNING'
    }
} catch {
    Write-Status "Fallo instalando deps backend: $($_.Exception.Message)" 'ERROR'
    Write-Host 'Seguimos igualmente. Revisa: $runLog' -ForegroundColor Yellow
}

# --- Start backend (new window, keeps open)
$backendMain = Join-Path $backendPath 'main.py'
if (!(Test-Path $backendMain)) {
    Write-Status 'No se encuentra backend/main.py' 'ERROR'
    Read-Host 'Pulsa ENTER para salir'
    Stop-Transcript | Out-Null
    exit 1
}

Write-Status 'Iniciando backend (Uvicorn)...' 'INFO'
$backendCmd = "`"$venvPython`" -m backend.main --host 0.0.0.0 --port 8000"
Start-Process powershell -ArgumentList '-NoExit', '-Command', $backendCmd -WorkingDirectory $projectPath -WindowStyle Normal

# --- Frontend handling
$hasPackageJson = Test-Path (Join-Path $frontendPath 'package.json')
$hasNode = Test-Command 'npm'
$hasNodeModules = Test-Path (Join-Path $frontendPath 'node_modules')

if ($hasPackageJson) {
    if (-not $hasNode) {
        Write-Status 'npm/Node no esta instalado. Serviremos archivos estaticos desde FastAPI.' 'WARNING'
    } else {
        try {
            if (-not $SkipInstall -and ($ReinstallFront -or -not $hasNodeModules)) {
                Write-Status 'Instalando dependencias frontend (npm install)...' 'INFO'
                Push-Location $frontendPath
                npm install | Tee-Object -FilePath (Join-Path $logsPath 'frontend-install.log')
                Pop-Location
                Write-Status 'Dependencias frontend OK' 'SUCCESS'
            } else {
                Write-Status 'Omitiendo npm install (SkipInstall/ya instalado)' 'INFO'
            }
        } catch {
            Write-Status "npm install fallo: $($_.Exception.Message)" 'ERROR'
            Write-Host 'Usaremos el modo estatico sirviendo /static desde el backend.' -ForegroundColor Yellow
        }

        if ($UseVite -and $hasNode) {
            Write-Status 'Lanzando Vite (npm run dev) en ventana separada...' 'INFO'
            Start-Process powershell -ArgumentList '-NoExit', '-Command', "Set-Location `"$frontendPath`"; npm run dev" -WindowStyle Normal
        } else {
            Write-Status 'UseVite no activado: saltamos Vite y usamos estaticos.' 'INFO'
        }
    }
} else {
    Write-Status 'No hay package.json en frontend: se serviran los HTML estaticos.' 'INFO'
}

# --- Helpful URLs
$manualBaseUrl = Get-BaseUrlFromHost($HostIp)
$localIp = $null

if (-not $manualBaseUrl) {
    if (-not $HostIp -or $HostIp.Trim().ToLower() -eq 'auto') {
        $localIp = Get-PrimaryIPv4
        if ($localIp -eq '127.0.0.1' -or [string]::IsNullOrWhiteSpace($localIp)) {
            Write-Status 'Mostrando URLs con localhost (no se encontró IP LAN activa)' 'WARNING'
            $localIp = 'localhost'
        } else {
            Write-Status ("IP LAN detectada automáticamente: $localIp") 'INFO'
        }
    } else {
        Write-Status ("IP configurada manualmente: $HostIp") 'INFO'
        $localIp = $HostIp
    }
}

if ($manualBaseUrl) {
    $backendPrimary = $manualBaseUrl
} else {
    if ([string]::IsNullOrWhiteSpace($localIp)) {
        Write-Status 'IP no definida; usando localhost para URLs' 'WARNING'
        $localIp = 'localhost'
    }
    $backendPrimary = "http://$($localIp):8000"
}

$backendLocal = 'http://localhost:8000'

if ($LanMode -and -not $manualBaseUrl) {
    $lanCandidate = $localIp
    if ($lanCandidate -eq 'localhost') {
        $lanCandidate = Get-PrimaryIPv4
    }

    if ($lanCandidate -and $lanCandidate -ne '127.0.0.1' -and $lanCandidate -ne 'localhost') {
    $backendPrimary = "http://$($lanCandidate):8000"
        Write-Status ("LAN mode activo: mostrando $backendPrimary") 'INFO'
    } else {
        Write-Status 'LAN mode activo, pero no se encontró IP LAN. Se mantiene localhost.' 'WARNING'
    }
} elseif ($LanMode -and $manualBaseUrl) {
    Write-Status 'LAN mode ignorado porque se proporcionó URL/IP manual.' 'WARNING'
}

if (-not $backendPrimary -or [string]::IsNullOrWhiteSpace($backendPrimary)) {
    $backendPrimary = 'http://localhost:8000'
}

$backendUrl  = $backendPrimary.TrimEnd('/')
$apiBase     = $backendUrl
$adminUrl    = "$apiBase/admin.html"
$staticIndex = "$apiBase/static/index.html"
$staticDemo  = "$apiBase/static/demo.html"

Write-Host ''
Write-Host '════════ URLs utiles ════════' -ForegroundColor Green
Write-Host ('Backend (principal): ' + $backendPrimary) -ForegroundColor White
Write-Host ('Backend (localhost): ' + $backendLocal) -ForegroundColor White
Write-Host ('Admin Panel:        ' + $adminUrl) -ForegroundColor White
Write-Host ('Index (static):     ' + $staticIndex) -ForegroundColor White
Write-Host ('Demo (static):      ' + $staticDemo) -ForegroundColor White
Write-Host '══════════════════════════════' -ForegroundColor Green
Write-Host ''

Write-Status 'Todo lanzado. Las ventanas de Backend/Vite quedan abiertas.' 'SUCCESS'
Write-Host 'Este panel se cierra cuando pulses ENTER (util si hiciste doble click).' -ForegroundColor Gray
Read-Host 'Pulsa ENTER para salir'

Stop-Transcript | Out-Null
exit 0
# --- End of script ---
