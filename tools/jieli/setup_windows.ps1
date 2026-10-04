$ErrorActionPreference = "Stop"

Write-Host "Setting up JieLi read-only acquisition environment..."

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher 'py' not found. Install Python 3.10+ first."
}

py -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host ""
Write-Host "Ready."
Write-Host "UART probe example:"
Write-Host "  .\.venv\Scripts\python.exe .\jieli_uart_probe.py --port COM7 --baud 9600 --seconds 10 --out reset_9600.bin"
Write-Host ""
Write-Host "Do not run erase/write operations against the target."
