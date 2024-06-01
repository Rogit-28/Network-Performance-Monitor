@echo off
REM Network-Performance-Monitor Setup and Run Script (Windows)
REM This script automates the setup and running of the Network-Performance-Monitor application on Windows

setlocal enabledelayedexpansion

REM Colors for output (using PowerShell for colored text)
set "INFO_COLOR=Blue"
set "SUCCESS_COLOR=Green"
set "WARNING_COLOR=Yellow"
set "ERROR_COLOR=Red"

REM Function to print colored output
call :print_status "Network-Performance-Monitor Setup and Run Script (Windows)"
call :print_status "Checking for required dependencies..."

REM Check for Python
python --version >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_CMD=python"
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    call :print_success "Python found: !PYTHON_VERSION!"
) else (
    python3 --version >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=python3"
        for /f "tokens=*" %%i in ('python3 --version 2^>^&1') do set PYTHON_VERSION=%%i
        call :print_success "Python found: !PYTHON_VERSION!"
    ) else (
        call :print_error "Python is not installed. Please install Python 3.x and try again."
        pause
        exit /b 1
    )
)

REM Check for Node.js
node --version >nul 2>&1
if !errorlevel! equ 0 (
    call :print_success "Node.js found: !error!"
    for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
    call :print_success "Node.js found: !NODE_VERSION!"
) else (
    call :print_error "Node.js is not installed. Please install Node.js and try again."
    pause
    exit /b 1
)

REM Check for npm
npm --version >nul 2>&1
if !errorlevel! equ 0 (
    call :print_success "npm found: !error!"
    for /f "tokens=*" %%i in ('npm --version') do set NPM_VERSION=%%i
    call :print_success "npm found: !NPM_VERSION!"
) else (
    call :print_error "npm is not installed. Please install npm and try again."
    pause
    exit /b 1
)

REM Function to install Python dependencies
call :install_python_deps

REM Function to install Node.js dependencies
call :install_node_deps

REM Determine execution mode
set "MODE=dev"
if "%1"=="-p" set "MODE=prod"
if "%1"=="--prod" set "MODE=prod"
if "%1"=="-s" set "MODE=setup"
if "%1"=="--setup" set "MODE=setup"
if "%1"=="-h" set "MODE=help"
if "%1"=="--help" set "MODE=help"

if "!MODE!"=="help" (
    call :show_usage
    exit /b 0
)

if "!MODE!"=="setup" (
    call :print_success "Dependencies installed successfully!"
    exit /b 0
)

REM Start the application based on mode
if "!MODE!"=="prod" (
    call :start_production
) else (
    REM Development mode
    call :start_backend
    call :start_frontend
    
    call :print_status "Application started successfully!"
    call :print_status "Backend API: http://127.0.0.1:8000"
    call :print_status "Frontend: http://127.0.0.1:3000"
    call :print_status "Press Ctrl+C to stop the application."
    
    REM Keep the script running to maintain both processes
    pause
)

goto :eof

REM Function definitions
:print_status
powershell -Command "Write-Host '[INFO] %~1' -ForegroundColor Blue"
goto :eof

:print_success
powershell -Command "Write-Host '[SUCCESS] %~1' -ForegroundColor Green"
goto :eof

:print_warning
powershell -Command "Write-Host '[WARNING] %~1' -ForegroundColor Yellow"
goto :eof

:print_error
powershell -Command "Write-Host '[ERROR] %~1' -ForegroundColor Red"
goto :eof

:install_python_deps
call :print_status "Installing Python dependencies from requirements.txt..."
if not exist "requirements.txt" (
    call :print_error "requirements.txt not found in project root."
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    call :print_status "Creating Python virtual environment..."
    !PYTHON_CMD! -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

REM Install requirements
python -m pip install -r requirements.txt

call :print_success "Python dependencies installed successfully."
goto :eof

:install_node_deps
call :print_status "Installing Node.js dependencies in frontend/app1 directory..."

if not exist "frontend\app1" (
    call :print_error "frontend\app1 directory not found."
    exit /b 1
)

cd frontend\app1

if not exist "package.json" (
    call :print_error "package.json not found in frontend\app1 directory."
    exit /b 1
)

npm install

call :print_success "Node.js dependencies installed successfully."

REM Return to project root
cd ..\..
goto :eof

:start_backend
call :print_status "Starting backend API on port 8000..."

if not exist "backend\api" (
    call :print_error "backend\api directory not found."
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start the backend in a new window
start "Network Performance Monitor - Backend" cmd /c "cd /d backend\api && !PYTHON_CMD! -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

call :print_success "Backend API started successfully"
goto :eof

:start_frontend
call :print_status "Starting frontend on port 3000..."

if not exist "frontend\app1" (
    call :print_error "frontend\app1 directory not found."
    exit /b 1
)

cd frontend\app1

REM Start the frontend in development mode in a new window
start "Network Performance Monitor - Frontend" cmd /c "cd /d frontend\app1 && npm run dev"

call :print_success "Frontend started successfully."

REM Return to project root
cd ..\..
goto :eof

:start_production
call :print_status "Starting in production mode..."

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Build frontend
call :print_status "Building frontend for production..."
cd frontend\app1
npm run build
cd ..\..

REM Start backend with production settings in a new window
start "Network Performance Monitor - Backend" cmd /c "cd /d backend\api && !PYTHON_CMD! -m uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4"

call :print_success "Backend API started in production mode"
goto :eof

:show_usage
echo Usage: %0 [option]
echo Options:
echo   -d, --dev      Start in development mode (default)
echo   -p, --prod     Start in production mode
echo   -s, --setup    Install dependencies only
echo   -h, --help     Show this help message
goto :eof