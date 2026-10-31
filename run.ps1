Write-Host "=== Starting Forex Dashboard ===" -ForegroundColor Cyan

# Kill old
netstat -ano | Select-String ":5050 " | ForEach-Object { $_.ToString().Trim() -split '\s+' | Select-Object -Last 1 } | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
netstat -ano | Select-String ":5173 " | ForEach-Object { $_.ToString().Trim() -split '\s+' | Select-Object -Last 1 } | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }

# Open terminals
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn backend.main:app --host 0.0.0.0 --port 5050"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev -- --port 5173"

Write-Host "Backend started in a new window (port 5050)" -ForegroundColor Green
Write-Host "Frontend started in a new window (port 5173)" -ForegroundColor Green
Write-Host "`nOpen: http://localhost:5173" -ForegroundColor Cyan
