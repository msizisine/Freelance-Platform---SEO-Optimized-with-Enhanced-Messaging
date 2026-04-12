# Railway Deployment Script for PowerShell
# This script helps deploy the Django freelance platform to Railway

Write-Host "=== Railway Deployment Script ===" -ForegroundColor Green
Write-Host "Starting deployment process..." -ForegroundColor Yellow

# Check if git is installed
try {
    git --version | Out-Null
} catch {
    Write-Host "ERROR: Git is not installed. Please install Git first." -ForegroundColor Red
    Write-Host "Download from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# Check if Railway CLI is installed
try {
    railway --version | Out-Null
} catch {
    Write-Host "ERROR: Railway CLI is not installed. Please install Railway CLI first." -ForegroundColor Red
    Write-Host "Run: npm install -g @railway/cli" -ForegroundColor Yellow
    exit 1
}

# Check if user is logged in to Railway
try {
    railway whoami | Out-Null
} catch {
    Write-Host "Please login to Railway first:" -ForegroundColor Yellow
    Write-Host "railway login" -ForegroundColor Cyan
    exit 1
}

# Initialize git repository if not already initialized
if (!(Test-Path ".git")) {
    Write-Host "Initializing git repository..." -ForegroundColor Yellow
    git init
    git add .
    git commit -m "Initial commit: Django freelance platform"
} else {
    Write-Host "Git repository already exists." -ForegroundColor Green
    # Add all changes
    git add .
    git commit -m "Fixed phone_utils import and Railway configuration"
}

# Create Railway project if it doesn't exist
Write-Host "Creating/updating Railway project..." -ForegroundColor Yellow
railway init

# Set environment variables
Write-Host "Setting up environment variables..." -ForegroundColor Yellow
railway variables set DJANGO_SETTINGS_MODULE="freelance_platform.settings.production"
railway variables set SECRET_KEY="django-insecure-change-this-in-production"
railway variables set DEBUG="False"
railway variables set ALLOWED_HOSTS="*.railway.app"

# Deploy to Railway
Write-Host "Deploying to Railway..." -ForegroundColor Yellow
railway up

Write-Host "=== Deployment Complete ===" -ForegroundColor Green
Write-Host "Your application should be available at: https://your-app-name.railway.app" -ForegroundColor Cyan
Write-Host "Check Railway dashboard for the actual URL" -ForegroundColor Cyan
