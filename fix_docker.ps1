# Docker Container Fix Script
# Run this in PowerShell as Administrator

Write-Host "Docker Container Fix for phone_utils Import Issue" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

# Check if Docker is running
try {
    $null = Get-Process docker -ErrorAction Stop
    Write-Host "Docker is running" -ForegroundColor Green
} catch {
    Write-Host "Error: Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Navigate to project directory
Set-Location -Path "c:\Users\msizi\CascadeProjects\windsurf-project"
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow

# Method 1: Try restart with volume mount first
Write-Host "`nStep 1: Restarting web service with volume mount..." -ForegroundColor Yellow
try {
    docker-compose restart web
    Write-Host "Web service restarted successfully" -ForegroundColor Green
    
    # Wait a moment and check logs
    Start-Sleep -Seconds 5
    Write-Host "`nChecking container logs..." -ForegroundColor Yellow
    $logs = docker-compose logs --tail=20 web
    Write-Host $logs
    
    # Check if the error is resolved
    if ($logs -match "ModuleNotFoundError.*phone_utils") {
        Write-Host "Error still present. Trying manual file copy..." -ForegroundColor Yellow
        
        # Method 2: Manual file copy
        Write-Host "`nStep 2: Manual file copy approach..." -ForegroundColor Yellow
        
        # Get container ID
        $containerId = docker-compose ps -q web
        if ($containerId) {
            $containerId = $containerId.Trim()
            Write-Host "Found container: $containerId" -ForegroundColor Green
            
            # Copy fixed files
            Write-Host "Copying fixed forms.py..." -ForegroundColor Yellow
            docker cp users/forms.py "$($containerId):/app/users/forms.py"
            
            Write-Host "Copying phone_utils.py..." -ForegroundColor Yellow
            docker cp users/phone_utils.py "$($containerId):/app/users/phone_utils.py"
            
            Write-Host "Restarting container..." -ForegroundColor Yellow
            docker-compose restart web
            
            Write-Host "`nFix completed! Checking logs again..." -ForegroundColor Green
            Start-Sleep -Seconds 5
            $finalLogs = docker-compose logs --tail=20 web
            Write-Host $finalLogs
            
            if ($finalLogs -match "ModuleNotFoundError.*phone_utils") {
                Write-Host "Error still present. Full rebuild may be needed." -ForegroundColor Red
                Write-Host "Run: docker-compose down && docker-compose build --no-cache web && docker-compose up -d" -ForegroundColor Yellow
            } else {
                Write-Host "SUCCESS! The phone_utils import error has been resolved." -ForegroundColor Green
            }
        } else {
            Write-Host "Could not find web container" -ForegroundColor Red
        }
    } else {
        Write-Host "SUCCESS! The phone_utils import error has been resolved." -ForegroundColor Green
    }
} catch {
    Write-Host "Error during Docker operations: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Please ensure Docker Desktop is running and you have proper permissions." -ForegroundColor Yellow
}

Write-Host "`n================================================" -ForegroundColor Green
Write-Host "Docker fix script completed" -ForegroundColor Green
