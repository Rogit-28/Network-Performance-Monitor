import asyncio
import threading
import time
import platform
import pythoncom
from datetime import datetime
from typing import Callable, Dict, Any, Optional
from .services import NetworkMonitorService
from .models import NetworkInterface, PerformanceMetric, HardwareInfo


class BackgroundTaskManager:
    """
    Manages background tasks for continuous data collection to support real-time updates.
    """
    
    def __init__(self, service: NetworkMonitorService, refresh_interval: float = 1.0):
        self.service = service
        self.refresh_interval = refresh_interval
        self._stop_event = threading.Event()
        self._background_thread = None
        self._last_performance_data = []
        self._last_interface_data = []
        self._last_hardware_data = []
        self._data_lock = threading.Lock()
        self._is_running = False
        
    def start(self):
        """Start the background data collection."""
        if not self._is_running:
            self._is_running = True
            self._stop_event.clear()
            self._background_thread = threading.Thread(target=self._background_worker, daemon=True)
            self._background_thread.start()
            
    def stop(self):
        """Stop the background data collection."""
        if self._is_running:
            self._is_running = False
            self._stop_event.set()
            if self._background_thread:
                self._background_thread.join()
                
    def _background_worker(self):
        """Background worker to continuously collect data."""
        # Initialize COM for this thread if on Windows
        if platform.system().lower() == "windows":
            try:
                pythoncom.CoInitialize()
            except Exception:
                # COM might already be initialized
                pass
                
        while not self._stop_event.is_set():
            try:
                print(f"BackgroundTask: Collecting metrics at {datetime.now().isoformat()}")  # Debug log
                # Update performance metrics
                interfaces = self.service.get_network_interfaces()
                performance_data = self.service.get_performance_metrics()
                hardware_info = self.service.get_hardware_info()
                
                print(f"BackgroundTask: Collected - {len(interfaces)} interfaces, {len(performance_data)} performance, {len(hardware_info)} hardware")  # Debug log
                
                with self._data_lock:
                    self._last_performance_data = performance_data
                    self._last_interface_data = interfaces
                    self._last_hardware_data = hardware_info
                
                # Wait for the specified interval or until stop is requested
                for _ in range(int(self.refresh_interval * 10)):  # Check every 0.1 seconds
                    if self._stop_event.is_set():
                        break
                    time.sleep(0.1)
                    
            except Exception as e:
                print(f"Error in background worker: {e}")
                # Wait a bit before retrying
                time.sleep(1)
        
        # Uninitialize COM for this thread if on Windows
        if platform.system().lower() == "windows":
            try:
                pythoncom.CoUninitialize()
            except Exception:
                # COM might not need uninitialization or already done
                pass
                
    def get_latest_performance_data(self) -> list:
        """Get the latest performance data collected by the background task."""
        with self._data_lock:
            data = self._last_performance_data.copy()
            print(f"BackgroundTask: Returning {len(data)} performance metrics")  # Debug log
            return data
            
    def get_latest_interface_data(self) -> list:
        """Get the latest interface data collected by the background task."""
        with self._data_lock:
            data = self._last_interface_data.copy()
            print(f"BackgroundTask: Returning {len(data)} interface data")  # Debug log
            return data
            
    def get_latest_hardware_data(self) -> list:
        """Get the latest hardware data collected by the background task."""
        with self._data_lock:
            data = self._last_hardware_data.copy()
            print(f"BackgroundTask: Returning {len(data)} hardware data")  # Debug log
            return data
            
    def get_latest_all_metrics(self) -> Dict[str, Any]:
        """Get all latest metrics collected by the background task."""
        with self._data_lock:
            result = {
                "interfaces": self._last_interface_data.copy(),
                "performance_metrics": self._last_performance_data.copy(),
                "hardware_info": self._last_hardware_data.copy(),
                "timestamp": datetime.now()
            }
            print(f"BackgroundTask: Returning all metrics - {len(result['interfaces'])} interfaces, {len(result['performance_metrics'])} metrics, {len(result['hardware_info'])} hardware")  # Debug log
            return result


# Global background task manager instance
background_manager = None


def initialize_background_manager(service: NetworkMonitorService, refresh_interval: float = 1.0):
    """Initialize the background task manager."""
    global background_manager
    if background_manager is None:
        background_manager = BackgroundTaskManager(service, refresh_interval)
        background_manager.start()


def get_background_manager() -> Optional[BackgroundTaskManager]:
    """Get the global background task manager instance."""
    return background_manager
