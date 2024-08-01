# 🌐 Network Performance Monitor

A sleek and powerful network monitoring tool built with Python and Streamlit. This application provides real-time insights into your system's network interfaces, hardware details, and performance metrics.

---

## Project Status

This project is currently in a **stable beta** phase. It is fully functional on Windows, but has limitations when running in a Linux container.

For more details on the limitations and future development, please see the `KNOWN_ISSUES.md` file.

---

## Features

-   **Available Network Interfaces:** Lists all network interfaces on your machine, displaying their IPv4 and IPv6 addresses.
-   **Hardware Information:** Provides detailed hardware specifications for your network adapters, including MAC address, link speed, and driver details. *(Note: This feature is only available when running on a native Windows host).*
-   **Performance Metrics:** Delivers real-time performance data for each interface, including bytes sent/received, latency, and throughput.

---

## Getting Started

### Prerequisites

-   Python 3.8+
-   Node.js and npm
-   Git (for cloning the repository)

---

## ⚙️ How to Run

You can run this application using the automated run scripts or by setting up the backend and frontend manually. The automated scripts are the recommended approach as they handle all dependencies and startup procedures automatically.

### 🚀 Using Automated Run Scripts (Recommended)

The project includes automated run scripts to simplify setup and execution for both Unix-like systems and Windows. Both scripts provide the same functionality including dependency checking, dependency installation, virtual environment management, application startup, error handling, and cross-platform compatibility. The scripts handle process management by storing process IDs in `.pid` files, automatically cleaning up processes when the script exits, and properly terminating background processes when interrupted (Ctrl+C).

**On Linux/macOS:**
```bash
chmod +x run.sh # Make the script executable
./run.sh [option]
```

**On Windows (Command Prompt):**
```cmd
run.bat [option]
```

**On Windows (Git Bash or WSL):**
```bash
./run.sh [option]
```

**Options:**
- `-d, --dev`: Start in development mode (default)
  - Starts backend with hot-reload enabled
  - Starts frontend in development mode
  - Access at http://127.0.0.1:8000 (backend) and http://127.0.0.1:3000 (frontend)
- `-p, --prod`: Start in production mode
  - Builds frontend for production
  - Starts backend with multiple workers
  - Optimized for production deployment
- `-s, --setup`: Install dependencies only
  - Installs Python and Node.js dependencies
  - Does not start the application
- `-h, --help`: Show help message

**Cross-platform compatibility:**
- On Windows, use either the batch file (`run.bat`) with Command Prompt or the bash script (`run.sh`) with Git Bash/WSL
- On Linux/Mac, use the bash script (`run.sh`) directly

When running in development mode, the application will start both the backend API server (on port 8000) and the frontend Next.js application (on port 3000). The backend will be available at `http://127.0.0.1:8000` and the frontend at `http://127.0.0.1:3000`.

### 🖥️ Manual Setup (Advanced Users)

For those who prefer to set up the backend and frontend manually, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Install Node.js dependencies:**
    ```bash
    cd frontend/app1
    npm install
    cd ../..
    ```

4.  **Start the backend API server:**
    ```bash
    cd backend/api
    python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
    ```

5.  **In a new terminal, start the frontend:**
    ```bash
    cd frontend/app1
    npm run dev
    ```

6. Open your web browser and navigate to `http://127.0.1:300` to access the application interface. The API will be available at `http://127.0.1:8000`.

---

## 🤝 Contributing

Contributions are welcome! If you would like to contribute to this project, please see the `CONTRIBUTING.md` file for more information.

---

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
