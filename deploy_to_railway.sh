#!/bin/bash

# Railway Deployment Script
# This script helps deploy the Django freelance platform to Railway

echo "=== Railway Deployment Script ==="
echo "Starting deployment process..."

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "ERROR: Git is not installed. Please install Git first."
    echo "On Windows: Download from https://git-scm.com/download/win"
    echo "On macOS: brew install git"
    echo "On Ubuntu/Debian: sudo apt-get install git"
    exit 1
fi

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "ERROR: Railway CLI is not installed. Please install Railway CLI first."
    echo "Run: npm install -g @railway/cli"
    exit 1
fi

# Check if user is logged in to Railway
if ! railway whoami &> /dev/null; then
    echo "Please login to Railway first:"
    echo "railway login"
    exit 1
fi

# Initialize git repository if not already initialized
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit: Django freelance platform"
else
    echo "Git repository already exists."
    # Add all changes
    git add .
    git commit -m "Fixed phone_utils import and Railway configuration"
fi

# Create Railway project if it doesn't exist
echo "Creating/updating Railway project..."
railway init

# Set environment variables
echo "Setting up environment variables..."
railway variables set DJANGO_SETTINGS_MODULE="freelance_platform.settings.production"
railway variables set SECRET_KEY="django-insecure-change-this-in-production"
railway variables set DEBUG="False"
railway variables set ALLOWED_HOSTS="*.railway.app"

# Deploy to Railway
echo "Deploying to Railway..."
railway up

echo "=== Deployment Complete ==="
echo "Your application should be available at: https://your-app-name.railway.app"
echo "Check Railway dashboard for the actual URL"
