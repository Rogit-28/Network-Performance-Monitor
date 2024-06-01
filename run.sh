#!/bin/bash

# Network-Performance-Monitor Setup and Run Script
# This script automates the setup and running of the Network-Performance-Monitor application
# It handles dependency installation, backend and frontend startup with proper error handling

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check dependencies
check_dependencies() {
    print_status "Checking for required dependencies..."
    
    # Check for Python
    if command_exists python3; then
        PYTHON_CMD="python3"
        print_success "Python found: $(python3 --version 2>&1)"
    elif command_exists python; then
        PYTHON_CMD="python"
        print_success "Python found: $(python --version 2>&1)"
    else
        print_error "Python is not installed. Please install Python 3.x and try again."
        exit 1
    fi
    
    # Check for Node.js
    if command_exists node; then
        print_success "Node.js found: $(node --version)"
    else
        print_error "Node.js is not installed. Please install Node.js and try again."
        exit 1
    fi
    
    # Check for npm
    if command_exists npm; then
        print_success "npm found: $(npm --version)"
    else
        print_error "npm is not installed. Please install npm and try again."
        exit 1
    fi
}

# Function to install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies from requirements.txt..."
    
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found in project root."
        exit 1
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        $PYTHON_CMD -m venv venv
    fi
    
    # Activate virtual environment
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
        # Windows
        source venv/Scripts/activate
    else
        # Unix/Linux/macOS
        source venv/bin/activate
    fi
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    pip install -r requirements.txt
    
    print_success "Python dependencies installed successfully."
}

# Function to install Node.js dependencies
install_node_deps() {
    print_status "Installing Node.js dependencies in frontend/app1 directory..."
    
    if [ ! -d "frontend/app1" ]; then
        print_error "frontend/app1 directory not found."
        exit 1
    fi
    
    cd frontend/app1
    
    if [ ! -f "package.json" ]; then
        print_error "package.json not found in frontend/app1 directory."
        exit 1
    fi
    
    npm install
    
    print_success "Node.js dependencies installed successfully."
    
    # Return to project root
    cd ../..
}

# Function to start the backend API
start_backend() {
    print_status "Starting backend API on port 8000..."
    
    if [ ! -d "backend/api" ]; then
        print_error "backend/api directory not found."
        exit 1
    fi
    
    # Activate virtual environment
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
        # Windows
        source venv/Scripts/activate
    else
        # Unix/Linux/macOS
        source venv/bin/activate
    fi
    
    # Start the backend in background
    cd backend/api
    $PYTHON_CMD -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload &
    BACKEND_PID=$!
    cd ../..
    
    # Wait a moment for the server to start
    sleep 3
    
    # Check if backend started successfully
    if kill -0 $BACKEND_PID 2>/dev/null; then
        print_success "Backend API started successfully with PID $BACKEND_PID"
        echo $BACKEND_PID > backend.pid
    else
        print_error "Failed to start backend API"
        exit 1
    fi
}

# Function to start the frontend
start_frontend() {
    print_status "Starting frontend on port 3000..."
    
    if [ ! -d "frontend/app1" ]; then
        print_error "frontend/app1 directory not found."
        exit 1
    fi
    
    cd frontend/app1
    
    # Start the frontend in development mode
    npm run dev &
    FRONTEND_PID=$!
    cd ../..
    
    # Wait a moment for the server to start
    sleep 3
    
    # Check if frontend started successfully
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        print_success "Frontend started successfully with PID $FRONTEND_PID"
        echo $FRONTEND_PID > frontend.pid
    else
        print_error "Failed to start frontend"
        exit 1
    fi
}

# Function to start in production mode
start_production() {
    print_status "Starting in production mode..."
    
    # Activate virtual environment
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
        # Windows
        source venv/Scripts/activate
    else
        # Unix/Linux/macOS
        source venv/bin/activate
    fi
    
    # Build frontend
    print_status "Building frontend for production..."
    cd frontend/app1
    npm run build
    cd ../..
    
    # Start backend with production settings
    print_status "Starting backend API in production mode..."
    cd backend/api
    $PYTHON_CMD -m uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4 &
    BACKEND_PID=$!
    cd ../..
    
    # Wait a moment for the server to start
    sleep 3
    
    # Check if backend started successfully
    if kill -0 $BACKEND_PID 2>/dev/null; then
        print_success "Backend API started in production mode with PID $BACKEND_PID"
        echo $BACKEND_PID > backend.pid
    else
        print_error "Failed to start backend API in production mode"
        exit 1
    fi
}

# Function to clean up background processes
cleanup() {
    print_status "Cleaning up background processes..."
    
    # Kill backend if running
    if [ -f "backend.pid" ]; then
        BACKEND_PID=$(cat backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            print_status "Backend process $BACKEND_PID terminated."
        fi
        rm -f backend.pid
    fi
    
    # Kill frontend if running
    if [ -f "frontend.pid" ]; then
        FRONTEND_PID=$(cat frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID
            print_status "Frontend process $FRONTEND_PID terminated."
        fi
        rm -f frontend.pid
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [option]"
    echo "Options:"
    echo "  -d, --dev      Start in development mode (default)"
    echo " -p, --prod     Start in production mode"
    echo "  -s, --setup    Install dependencies only"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "Cross-platform compatibility:"
    echo "  - On Windows, use Git Bash or WSL to run this script"
    echo "  - On Linux/Mac, run directly with './run.sh'"
}

# Main execution
main() {
    MODE="dev"  # Default mode
    
    # Parse command line arguments
    case "${1:-}" in
        -d|--dev)
            MODE="dev"
            ;;
        -p|--prod)
            MODE="prod"
            ;;
        -s|--setup)
            MODE="setup"
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        "")
            MODE="dev"
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
    
    print_status "Network-Performance-Monitor Setup and Run Script"
    print_status "Mode: $MODE"
    echo ""
    
    # Set up cleanup trap
    trap cleanup EXIT
    
    # Check dependencies
    check_dependencies
    
    if [ "$MODE" = "setup" ]; then
        # Install dependencies only
        install_python_deps
        install_node_deps
        print_success "Dependencies installed successfully!"
        exit 0
    fi
    
    # Install dependencies
    install_python_deps
    install_node_deps
    
    # Start the application based on mode
    if [ "$MODE" = "prod" ]; then
        start_production
    else
        # Development mode
        start_backend
        start_frontend
        
        print_status "Application started successfully!"
        print_status "Backend API: http://127.0.0.1:8000"
        print_status "Frontend: http://127.0.0.1:3000"
        print_status "Press Ctrl+C to stop the application."
        
        # Wait for both processes to finish
        wait
    fi
}

# Execute main function with all arguments
main "$@"