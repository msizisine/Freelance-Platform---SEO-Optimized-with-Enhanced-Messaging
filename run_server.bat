@echo off
echo Starting Django Development Server...

REM Activate virtual environment
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

REM Start server
echo Starting server at http://127.0.0.1:8000
echo Press Ctrl+C to stop the server.
echo.
python manage.py runserver

pause
