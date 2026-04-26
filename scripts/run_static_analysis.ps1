# Static Analysis Suite for NeuralCore

Write-Host "--- Running Strict Type Checking (Mypy) ---" -ForegroundColor Cyan
python -m mypy libs services

if ($LASTEXITCODE -ne 0) {
    Write-Host "Mypy failed!" -ForegroundColor Red
}

Write-Host "`n--- Running Aggressive Linting (Pylint) ---" -ForegroundColor Cyan
python -m pylint libs services

if ($LASTEXITCODE -ne 0) {
    Write-Host "Pylint failed!" -ForegroundColor Red
}

Write-Host "`n--- Running Ontology Verification ---" -ForegroundColor Cyan
python tests/verify_ontology.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Ontology verification failed!" -ForegroundColor Red
}

Write-Host "`n--- Running Security Linting (Bandit) ---" -ForegroundColor Cyan
python -m bandit -r libs services

if ($LASTEXITCODE -ne 0) {
    Write-Host "Bandit failed!" -ForegroundColor Red
}

Write-Host "`n--- Running Secret Scanning (detect-secrets) ---" -ForegroundColor Cyan
if (Test-Path .secrets.baseline) {
    python -m detect_secrets scan --baseline .secrets.baseline .
} else {
    python -m detect_secrets scan .
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "Secret scanning failed!" -ForegroundColor Red
}

Write-Host "`nStatic Analysis Complete." -ForegroundColor Green
