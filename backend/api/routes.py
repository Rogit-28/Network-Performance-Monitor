from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from .models import NetworkInterface, PerformanceMetric, HardwareInfo, LogEntry, LogQueryParams
from .services import NetworkMonitorService
from .background_tasks import get_background_manager
from backend.comprehensive_logger.comprehensive_logger import ComprehensiveLogger as BackendJSONLogger
from backend.log_exporter.log_exporter import LogExporter
import json

router = APIRouter()
service = NetworkMonitorService(cache_duration=1.0)  # Initialize with 1-second cache
logger = BackendJSONLogger()
log_exporter = LogExporter(logger)

@router.get("/")
def read_api_root():
    return {"message": "Network Performance Monitor API - Available routes: /interfaces, /metrics, /hardware, /all-metrics"}

@router.get("/interfaces", response_model=List[NetworkInterface])
def get_network_interfaces():
    """
    Retrieve all network interfaces with their details.
    """
    try:
        bg_manager = get_background_manager()
        if bg_manager:
            interfaces = bg_manager.get_latest_interface_data()
        else:
            interfaces = service.get_network_interfaces()
        # Log the API call
        logger.log_metric('api_call', {
            'endpoint': '/interfaces',
            'result_count': len(interfaces)
        }, 'INFO', 'api')
        return interfaces
    except Exception as e:
        logger.log_error(f"Error retrieving network interfaces: {str(e)}", "interfaces", "api")
        raise HTTPException(status_code=500, detail=f"Error retrieving network interfaces: {str(e)}")

@router.get("/metrics", response_model=List[PerformanceMetric])
def get_performance_metrics():
    """
    Retrieve performance metrics for all network interfaces.
    Includes bytes sent/received, packets sent/received, latency, and throughput.
    """
    try:
        bg_manager = get_background_manager()
        if bg_manager:
            metrics = bg_manager.get_latest_performance_data()
        else:
            metrics = service.get_performance_metrics()
        # Log the API call
        logger.log_metric('api_call', {
            'endpoint': '/metrics',
            'result_count': len(metrics)
        }, 'INFO', 'api')
        return metrics
    except Exception as e:
        logger.log_error(f"Error retrieving performance metrics: {str(e)}", "metrics", "api")
        raise HTTPException(status_code=500, detail=f"Error retrieving performance metrics: {str(e)}")

@router.get("/hardware", response_model=List[HardwareInfo])
def get_hardware_info():
    """
    Retrieve hardware information for network adapters.
    """
    try:
        bg_manager = get_background_manager()
        if bg_manager:
            hardware_info = bg_manager.get_latest_hardware_data()
        else:
            hardware_info = service.get_hardware_info()
        # Log the API call
        logger.log_metric('api_call', {
            'endpoint': '/hardware',
            'result_count': len(hardware_info)
        }, 'INFO', 'api')
        return hardware_info
    except Exception as e:
        logger.log_error(f"Error retrieving hardware info: {str(e)}", "hardware", "api")
        raise HTTPException(status_code=500, detail=f"Error retrieving hardware info: {str(e)}")

@router.get("/all-metrics")
def get_all_metrics():
    """
    Retrieve all metrics (interfaces, performance, hardware) at once.
    """
    try:
        bg_manager = get_background_manager()
        if bg_manager:
            all_metrics = bg_manager.get_latest_all_metrics()
        else:
            all_metrics = service.get_all_metrics()
        # Log the API call
        logger.log_metric('api_call', {
            'endpoint': '/all-metrics',
            'interfaces_count': len(all_metrics['interfaces']),
            'metrics_count': len(all_metrics['performance_metrics']),
            'hardware_count': len(all_metrics['hardware_info'])
        }, 'INFO', 'api')
        return all_metrics
    except Exception as e:
        logger.log_error(f"Error retrieving all metrics: {str(e)}", "all_metrics", "api")
        raise HTTPException(status_code=500, detail=f"Error retrieving all metrics: {str(e)}")

# Remove the logs and stats endpoints as they're not needed for this API

@router.get("/logs", response_model=List[LogEntry])
def get_logs(
    start_time: Optional[datetime] = Query(None, description="Start time for filtering logs"),
    end_time: Optional[datetime] = Query(None, description="End time for filtering logs"),
    log_level: Optional[str] = Query(None, description="Log level to filter by"),
    metric_type: Optional[str] = Query(None, description="Metric type to filter by"),
    search_term: Optional[str] = Query(None, description="Term to search for in log entries")
):
    """
    Retrieve logs with optional filtering by date range, log level, metric type, and search term.
    """
    try:
        # Create a temporary copy of the log file to avoid race conditions
        import tempfile
        import shutil
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.log') as temp_file:
            # Copy the current log file contents to the temporary file
            try:
                with open(logger.log_file, 'r', encoding='utf-8') as original_file:
                    shutil.copyfileobj(original_file, temp_file)
                temp_filename = temp_file.name
            except FileNotFoundError:
                return []
        
        # Now read from the temporary copy to avoid file locking issues
        try:
            with open(temp_filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            filtered_logs = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    log_entry = json.loads(line)
                    
                    # Apply time filtering
                    if start_time or end_time:
                        log_time = datetime.fromisoformat(log_entry['timestamp'].replace('Z', '+00:00'))
                        if start_time and log_time < start_time:
                            continue
                        if end_time and log_time > end_time:
                            continue
                    
                    # Apply search term filtering
                    if search_term:
                        if search_term.lower() not in json.dumps(log_entry).lower():
                            continue
                    
                    # Apply level filtering
                    if log_level:
                        log_entry_level = log_entry.get('log_level', '').upper()
                        # Handle multiple log levels (comma-separated)
                        if log_level.upper() != log_entry_level:
                            log_levels_list = [level.strip().upper() for level in log_level.split(',')]
                            if log_entry_level not in log_levels_list:
                                continue
                            
                    # Apply metric type filtering
                    if metric_type:
                        log_entry_metric_type = log_entry.get('metric_type', '').lower()
                        # Handle multiple metric types (comma-separated)
                        if log_entry_metric_type != metric_type.lower():
                            metric_types_list = [mt.strip().lower() for mt in metric_type.split(',')]
                            if log_entry_metric_type not in metric_types_list:
                                continue
                            
                    # Add the log entry to the filtered list
                    filtered_logs.append(log_entry)
                    
                except json.JSONDecodeError:
                    # Skip invalid JSON lines
                    continue

            # Convert to LogEntry models
            log_entries = [LogEntry(**log) for log in filtered_logs]
            return log_entries

        finally:
            # Clean up the temporary file
            import os
            os.unlink(temp_filename)

    except FileNotFoundError:
        return []
    except Exception as e:
        logger.log_error(f"Error retrieving logs: {str(e)}", "logs", "api")
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {str(e)}")


@router.get("/logs/export")
def export_logs(
    export_format: str = Query("json", description="Format to export logs (json or csv)"),
    start_time: Optional[datetime] = Query(None, description="Start time for filtering logs"),
    end_time: Optional[datetime] = Query(None, description="End time for filtering logs"),
    log_level: Optional[str] = Query(None, description="Log level to filter by"),
    metric_type: Optional[str] = Query(None, description="Metric type to filter by"),
    search_term: Optional[str] = Query(None, description="Term to search for in log entries")
):
    """
    Export logs in specified format with optional filtering by date range, log level, metric type, and search term.
    """
    try:
        # Use the LogExporter to handle the export
        exported_data = log_exporter.export_logs(
            export_format=export_format.lower(),
            start_time=start_time,
            end_time=end_time,
            level_filter=log_level,
            search_term=search_term,
            metric_type=metric_type
        )
        
        if exported_data is None:
            raise HTTPException(status_code=404, detail="Log file not found")
        
        # Return the exported data with appropriate content type
        if export_format.lower() == "csv":
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(content=exported_data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=network_logs.csv"})
        else:  # JSON format
            import io
            from fastapi.responses import StreamingResponse
            json_content = json.dumps(exported_data, indent=2)
            return StreamingResponse(io.StringIO(json_content), media_type="application/json", headers={"Content-Disposition": "attachment; filename=network_logs.json"})
            
    except Exception as e:
        logger.log_error(f"Error exporting logs: {str(e)}", "logs_export", "api")
        raise HTTPException(status_code=500, detail=f"Error exporting logs: {str(e)}")


@router.get("/logs/levels")
def get_log_levels():
    """
    Get distinct log levels available in the logs.
    """
    try:
        # Create a temporary copy of the log file to avoid race conditions
        import tempfile
        import shutil
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.log') as temp_file:
            # Copy the current log file contents to the temporary file
            try:
                with open(logger.log_file, 'r', encoding='utf-8') as original_file:
                    shutil.copyfileobj(original_file, temp_file)
                temp_filename = temp_file.name
            except FileNotFoundError:
                return []
        
        # Now read from the temporary copy to avoid file locking issues
        try:
            with open(temp_filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            log_levels = set()
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    log_entry = json.loads(line)
                    level = log_entry.get('log_level', '').upper()
                    if level:
                        log_levels.add(level)
                except json.JSONDecodeError:
                    # Skip invalid JSON lines
                    continue

            return sorted(list(log_levels))

        finally:
            # Clean up the temporary file
            import os
            os.unlink(temp_filename)

    except Exception as e:
        logger.log_error(f"Error retrieving log levels: {str(e)}", "logs_levels", "api")
        raise HTTPException(status_code=500, detail=f"Error retrieving log levels: {str(e)}")


@router.get("/logs/metric-types")
def get_metric_types():
    """
    Get distinct metric types available in the logs.
    """
    try:
        # Create a temporary copy of the log file to avoid race conditions
        import tempfile
        import shutil
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.log') as temp_file:
            # Copy the current log file contents to the temporary file
            try:
                with open(logger.log_file, 'r', encoding='utf-8') as original_file:
                    shutil.copyfileobj(original_file, temp_file)
                temp_filename = temp_file.name
            except FileNotFoundError:
                return []
        
        # Now read from the temporary copy to avoid file locking issues
        try:
            with open(temp_filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            metric_types = set()
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    log_entry = json.loads(line)
                    metric_type = log_entry.get('metric_type', '').lower()
                    if metric_type:
                        metric_types.add(metric_type)
                except json.JSONDecodeError:
                    # Skip invalid JSON lines
                    continue

            return sorted(list(metric_types))

        finally:
            # Clean up the temporary file
            import os
            os.unlink(temp_filename)

    except Exception as e:
        logger.log_error(f"Error retrieving metric types: {str(e)}", "logs_metric_types", "api")
        raise HTTPException(status_code=500, detail=f"Error retrieving metric types: {str(e)}")


# Health check endpoints
@router.get("/health")
def health_check():
    """Health check endpoint for the application."""
    import psutil
    import time
    from datetime import datetime
    from backend.config_manager import ConfigManager
    
    config_manager = ConfigManager()
    
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
        
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


@router.get("/health/ready")
def readiness_check():
    """Readiness check endpoint - checks if the application is ready to serve requests."""
    from backend.config_manager import ConfigManager
    from datetime import datetime
    
    config_manager = ConfigManager()
    
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
        
        return readiness_status
        
    except Exception as e:
        return {
            "status": "not_ready",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


@router.get("/health/live")
def liveness_check():
    """Liveness check endpoint - checks if the application is alive and responding."""
    from datetime import datetime
    
    liveness_status = {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "message": "Application is running and responding to requests"
    }
    
    return liveness_status


# Initialize start time for health check
if not hasattr(health_check, '_start_time'):
    import time
    health_check._start_time = time.time()
