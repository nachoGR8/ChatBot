# Restart backend safely (run this in PowerShell from the repository root: chatbot\chatbot)
# Usage: .\restart_backend.ps1

# Resolve venv python
try {
    $venvPy = Resolve-Path .\venv\Scripts\python.exe -ErrorAction Stop
} catch {
    Write-Error "No se encontró .\venv\Scripts\python.exe. Ejecuta esto desde la carpeta chatbot\chatbot donde está el venv."
    exit 1
}

# Kill any process listening on port 8000
$existing = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($existing) {
    $pids = $existing | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($pid in $pids) {
        try {
            Write-Output "Matando proceso PID=$pid que usa puerto 8000"
            Stop-Process -Id $pid -Force -ErrorAction Stop
        } catch {
            Write-Warning "No pude matar PID=$pid: $_"
        }
    }
}

Write-Output "Arrancando uvicorn con: $($venvPy.Path) -m uvicorn main:app --host 127.0.0.1 --port 8000"
# Start uvicorn in the current terminal (foreground) so you can see logs and errors.
& $venvPy -m uvicorn main:app --host 127.0.0.1 --port 8000

# NOTE: This runs in foreground. Open a second PowerShell window to call HTTP endpoints and tail logs.
