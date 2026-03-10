@echo off
:: ============================================
::  Jegymester - Start Development Server
:: ============================================
title Jegymester - Django Server

cd /d "%~dp0"

:: Activate virtual environment
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment not found. Run "python setup.py" first.
    pause
    exit /b 1
)

:: Apply any pending migrations
echo Applying migrations...
python manage.py migrate --run-syncdb

:: Start the development server
echo.
echo ============================================
echo   Jegymester is running at http://127.0.0.1:8000
echo   Press Ctrl+C to stop the server.
echo ============================================
echo.
python manage.py runserver
