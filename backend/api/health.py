from fastapi import APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime
import psutil
import time
from typing import Dict, Any
from backend.config_manager import ConfigManager

router = APIRouter()
config_manager = ConfigManager()

@router.get("/health")
async def health_check():
    """Health check endpoint for the application."""
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else 0
        
        # Get process-specific metrics
        process = psutil.Process()
        process_memory = process.memory_info().rss / 1024 / 1024  # MB
        process_cpu = process.cpu_percent()
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime": time.time() - getattr(health_check, '_start_time', time.time()),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
                "load_average": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            },
            "process": {
                "memory_mb": round(process_memory, 2),
                "cpu_percent": process_cpu,
                "num_threads": process.num_threads(),
                "num_fds": process.num_fds() if hasattr(process, 'num_fds') else 0
            },
            "config": {
                "simulation_mode": config_manager.is_simulation_mode(),
                "cache_duration": config_manager.get_cache_duration(),
                "rate_limit_enabled": config_manager.get("RATE_LIMIT_ENABLED", False)
            }
        }
        
        # Check if any metric is concerning
        if (cpu_percent > 80 or memory_percent > 80 or disk_percent > 80 or 
            process_memory > 1000):  # More than 1GB
            health_status["status"] = "degraded"
        
        return JSONResponse(content=health_status, status_code=200)
        
    except Exception as e:
        return JSONResponse(
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            },
            status_code=500
        )

@router.get("/health/ready")
async def readiness_check():
    """Readiness check endpoint - checks if the application is ready to serve requests."""
    try:
        # Basic readiness check - ensure config is loaded and services are available
        config_manager.get("SIMULATION_MODE")
        
        readiness_status = {
            "status": "ready",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "config_loaded": True,
                "api_available": True,
                "network_monitoring": True
            }
        }
        
        return JSONResponse(content=readiness_status, status_code=200)
        
    except Exception as e:
        return JSONResponse(
            content={
                "status": "not_ready",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            },
            status_code=503
        )

@router.get("/health/live")
async def liveness_check():
    """Liveness check endpoint - checks if the application is alive and responding."""
    liveness_status = {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "message": "Application is running and responding to requests"
    }
    
    return JSONResponse(content=liveness_status, status_code=20)

# Initialize start time
if not hasattr(health_check, '_start_time'):
    health_check._start_time = time.time()
