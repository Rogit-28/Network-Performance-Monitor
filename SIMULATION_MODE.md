# Running the Frontend with Simulation Mode

This document explains how to run the Network Performance Monitor frontend with the simulation mode, which generates realistic network performance data without requiring access to real hardware.

## What is Simulation Mode?

Simulation mode uses the `SimulationService` to generate realistic network performance data with natural fluctuations instead of collecting actual metrics from your system. This is useful for testing the frontend without requiring specific hardware access.

## Running the Frontend with Simulation Mode

### Method 1: Using the Dedicated Simulation Scripts

The easiest way to run the frontend with simulation mode is to use the dedicated scripts:

#### On Windows:
```cmd
run_simulation.bat
```

This script will:
1. Set up the environment with `SIMULATION_MODE=true`
2. Install dependencies for both backend and frontend
3. Start the backend API in simulation mode on port 8000
4. Start the frontend on port 3000

#### On Linux/macOS:
```bash
chmod +x run_simulation.sh
./run_simulation.sh
```

This script will:
1. Set up the environment with `SIMULATION_MODE=true`
2. Install dependencies for both backend and frontend
3. Start the backend API in simulation mode on port 8000
4. Start the frontend on port 3000

### Method 2: Using the Existing Run Scripts with Environment Variable

You can also use the existing run scripts with the simulation environment variable:

#### On Windows:
```cmd
set SIMULATION_MODE=true
run.bat
```

#### On Linux/macOS:
```bash
SIMULATION_MODE=true ./run.sh
```

### Method 3: Manual Setup

If you prefer to start components manually:

1. First, set the environment variable:
   - Windows: `set SIMULATION_MODE=true`
   - Linux/macOS: `export SIMULATION_MODE=true`

2. In a terminal, start the backend API:
   ```bash
   cd backend/api
   python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```

3. In a new terminal, start the frontend:
   ```bash
   cd frontend/app1
   npm run dev
   ```

## Accessing the Frontend

Once both the backend and frontend are running, the frontend will be available at:

- Frontend: [http://127.0.0.1:3000](http://127.0.0.1:3000)
- Backend API: [http://127.0.0.1:8000](http://127.0.0.1:8000)

The frontend will connect to the simulated backend and display realistic network performance metrics without requiring access to actual network hardware.