@echo off

echo Rebuilding Docker container with updated code...

REM Stop the containers
echo Stopping containers...
docker-compose down

REM Rebuild the web service with no cache to ensure fresh build
echo Rebuilding web service...
docker-compose build --no-cache web

REM Start the containers
echo Starting containers...
docker-compose up -d

echo Container rebuild complete. Checking status...
docker-compose ps

pause
