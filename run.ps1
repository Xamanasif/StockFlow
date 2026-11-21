param([int]$Port = 8000, [string]$PythonPath = '')
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$Probe = "import importlib.util,sys; sys.exit(0 if all(importlib.util.find_spec(m) for m in 'fastapi pandas numpy scipy sklearn httpx uvicorn openpyxl'.split()) else 1)"
$Python = $null
if ($PythonPath) {
    if (!(Test-Path -LiteralPath $PythonPath -PathType Leaf)) { throw "Python interpreter not found: $PythonPath" }
    $Candidate = (Resolve-Path -LiteralPath $PythonPath).Path
    & $Candidate -c $Probe
    if ($LASTEXITCODE -ne 0) { throw 'The selected interpreter is missing project dependencies. Install requirements.lock with that interpreter.' }
    $Python = $Candidate
} else {
    $Candidates = @((Join-Path $PSScriptRoot '.venv\Scripts\python.exe'), (Join-Path $PSScriptRoot '.venv-release-v3\Scripts\python.exe'))
    $ActivePython = Get-Command python -ErrorAction SilentlyContinue
    if ($ActivePython) { $Candidates += $ActivePython.Source }
    foreach ($Candidate in $Candidates) {
        if (Test-Path -LiteralPath $Candidate -PathType Leaf) {
            & $Candidate -c $Probe
            if ($LASTEXITCODE -eq 0) { $Python = $Candidate; break }
        }
    }
    if (!$Python) { throw 'No interpreter has the required modules. Create .venv and install requirements.lock; see README.md.' }
}
$Listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback,$Port)
try { $Listener.Start() } catch { throw "Port $Port is in use. Retry: .\run.ps1 -Port $($Port+1)" } finally { $Listener.Stop() }
Write-Host "Using Python: $Python"
& $Python -m uvicorn app.main:app --host 127.0.0.1 --port $Port --log-level info
exit $LASTEXITCODE
