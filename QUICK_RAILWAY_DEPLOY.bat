@echo off
echo === Quick Railway Deployment ===
echo.

REM Check if Railway CLI is installed
railway --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Railway CLI not found. Installing...
    npm install -g @railway/cli
    if errorlevel 1 (
        echo ERROR: Failed to install Railway CLI. Please install Node.js first.
        pause
        exit /b 1
    )
)

REM Login to Railway
echo Logging into Railway...
railway login

REM Initialize git if needed
if not exist ".git" (
    echo Initializing git repository...
    git init
    git add .
    git commit -m "Initial commit: Django freelance platform with fixed imports"
) else (
    echo Adding latest changes...
    git add .
    git commit -m "Fixed phone_utils import and Railway configuration"
)

REM Initialize Railway project
echo Setting up Railway project...
railway init

REM Set environment variables
echo Configuring environment variables...
railway variables set DJANGO_SETTINGS_MODULE="freelance_platform.settings.production"
railway variables set SECRET_KEY="django-insecure-change-this-in-production"
railway variables set DEBUG="False"
railway variables set ALLOWED_HOSTS="*.railway.app"

REM Deploy
echo Deploying to Railway...
railway up

echo.
echo === Deployment Complete ===
echo Check your Railway dashboard for the application URL
echo.
pause
