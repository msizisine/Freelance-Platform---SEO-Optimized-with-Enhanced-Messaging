@echo off
echo Manual Docker Fix for phone_utils Import Issue
echo ================================================

echo Step 1: Find the running web container...
for /f "tokens=*" %%i in ('docker-compose ps -q web') do set CONTAINER_ID=%%i
if "%CONTAINER_ID%"=="" (
    echo Error: Web container not found
    pause
    exit /b 1
)
echo Found container: %CONTAINER_ID%

echo.
echo Step 2: Copy fixed forms.py to container...
docker cp users/forms.py %CONTAINER_ID%:/app/users/forms.py
if %ERRORLEVEL% neq 0 (
    echo Error copying forms.py
    pause
    exit /b 1
)
echo forms.py copied successfully

echo.
echo Step 3: Copy phone_utils.py to container...
docker cp users/phone_utils.py %CONTAINER_ID%:/app/users/phone_utils.py
if %ERRORLEVEL% neq 0 (
    echo Error copying phone_utils.py
    pause
    exit /b 1
)
echo phone_utils.py copied successfully

echo.
echo Step 4: Restart web service...
docker-compose restart web
if %ERRORLEVEL% neq 0 (
    echo Error restarting web service
    pause
    exit /b 1
)
echo Web service restarted successfully

echo.
echo ================================================
echo Manual fix completed! The container should now work.
echo Check the container logs to verify the fix.
echo ================================================
pause
