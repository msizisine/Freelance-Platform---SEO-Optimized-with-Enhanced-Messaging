@echo off
echo Setting up Django Freelance Platform...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo Python found. Setting up virtual environment...

REM Create virtual environment
if not exist venv (
    python -m venv venv
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file...
    copy .env.example .env
    echo Please edit .env file with your settings.
)

REM Run migrations
echo Running database migrations...
python manage.py makemigrations
python manage.py migrate

REM Create superuser
echo.
echo Creating superuser account...
python manage.py createsuperuser

REM Collect static files
echo Collecting static files...
python manage.py collectstatic --noinput

echo.
echo Setup complete!
echo.
echo To run the development server:
echo 1. Activate virtual environment: venv\Scripts\activate.bat
echo 2. Run server: python manage.py runserver
echo 3. Open browser: http://127.0.0.1:8000
echo.
echo Admin panel: http://127.0.0.1:8000/admin
echo.
pause
