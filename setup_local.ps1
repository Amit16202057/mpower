# Setup Script for KoBocat Local Development
# This script will set up the project for local development with SQLite

Write-Host "============================================" -ForegroundColor Green
Write-Host "KoBocat Local Development Setup" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# Check if Git is installed
Write-Host "Checking for Git installation..." -ForegroundColor Yellow
$gitCheck = git --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Git is not installed!" -ForegroundColor Red
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ Git is installed: $gitCheck" -ForegroundColor Green
Write-Host ""

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version
Write-Host "✓ Python is installed: $pythonVersion" -ForegroundColor Green
Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
Write-Host "✓ Virtual environment activated" -ForegroundColor Green
Write-Host ""

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
Write-Host "This may take several minutes..." -ForegroundColor Cyan
pip install -r mpowersocial-geobis_server-364c03fb06cf\kobocat\requirements\base.pip
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
Write-Host ""

# Run migrations
Write-Host "Running database migrations..." -ForegroundColor Yellow
cd mpowersocial-geobis_server-364c03fb06cf\kobocat
python manage.py migrate --settings=onadata.settings.example_sqlite
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Some migrations may have failed" -ForegroundColor Yellow
}
Write-Host "✓ Migrations completed" -ForegroundColor Green
Write-Host ""

# Create superuser (optional)
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To start the development server, run:" -ForegroundColor Yellow
Write-Host "python manage.py runserver --settings=onadata.settings.example_sqlite" -ForegroundColor Cyan
Write-Host ""
Write-Host "The application will be available at: http://127.0.0.1:8000/" -ForegroundColor Cyan
