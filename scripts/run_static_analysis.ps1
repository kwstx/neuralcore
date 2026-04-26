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

Write-Host "`nStatic Analysis Complete." -ForegroundColor Green
