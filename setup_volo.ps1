# setup_volo.ps1
# Run this script from inside the project folder (e.g., "volo")

$python = "python"
$envPath = ".venv"

# Check if Python is available
if (-not (Get-Command $python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python is not available in the PATH. Please check your installation."
    exit 1
}

# Create virtual environment if not present
if (-not (Test-Path $envPath)) {
    Write-Host "Creating virtual environment..."
    & $python -m venv $envPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment."
        exit 1
    }
} else {
    Write-Host "Virtual environment already exists. Skipping creation."
}

# Activate virtual environment
$activateScript = ".\$envPath\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "Activating virtual environment..."
    & $activateScript
} else {
    Write-Host "ERROR: Activation script not found: $activateScript"
    exit 1
}

# Upgrade pip
Write-Host "Upgrading pip..."
python -m pip install --upgrade pip 

# Install dependencies
if (Test-Path "requirements.txt") {
    Write-Host "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
} else {
    Write-Host "No requirements.txt found. Installing base packages..."
    pip install flask flask_sqlalchemy flask_login flask_wtf wtforms
    pip freeze > requirements.txt
}

# Set environment variables from .env (optional if already exists)
if (-not (Test-Path ".env")) {
    Write-Host "Creating default .env file..."
    @"
FLASK_APP=run.py
FLASK_ENV=development
"@ | Out-File -Encoding ASCII .env
}

# Launch Flask app
Write-Host "Running Flask app..."
flask run --debug
