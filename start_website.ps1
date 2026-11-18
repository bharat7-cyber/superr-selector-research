$ErrorActionPreference = 'Stop'
Write-Host 'Starting the dashboard at http://localhost:8000'
Write-Host 'Press Ctrl+C to stop the local server.'
python -m http.server 8000 --directory app
