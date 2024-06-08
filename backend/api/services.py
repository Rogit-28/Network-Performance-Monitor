import psutil
import platform
import pythoncom
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from .models import NetworkInterface, PerformanceMetric, HardwareInfo
from backend.telemetry_collector.network_utils import get_network_interfaces, get_latency_concurrent, calculate_throughput
from backend.hardware_collector.hardware_info import display_hardware_info, initialize_wmi
from backend.comprehensive_logger.comprehensive_logger import ComprehensiveLogger
from backend.config_manager import ConfigManager
from backend.logger_initializer.logging_service import JSONLogger as BackendJSONLogger
from backend.simulation.simulation_service import SimulationService
import time
import threading
import asyncio
from functools import wraps
from collections import OrderedDict


class LRUCache:
    """Simple LRU Cache implementation for better performance."""
    def __init__(self, maxsize: int = 128, ttl: float = 1.0):
        self.maxsize = maxsize
        self.ttl = ttl
        self.cache = OrderedDict()
        self.lock = threading.Lock()
    
    def get(self, key: str):
        with self.lock:
            if key in self.cache:
                result, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl:
                    # Move to end (most recently used)
                    self.cache.move_to_end(key)
                    return result
                else:
                    # Expired, remove it
                    del self.cache[key]
            return None
    
    def set(self, key: str, value):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            elif len(self.cache) >= self.maxsize:
                # Remove least recently used item
                self.cache.popitem(last=False)
            self.cache[key] = (value, time.time())


def cache_result(cache_duration: float = 1.0, maxsize: int = 128):
    """Decorator to cache function results with LRU cache and TTL."""
    cache = LRUCache(maxsize=maxsize, ttl=cache_duration)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from args and kwargs
            key = str(args) + str(sorted(kwargs.items()))
            result = cache.get(key)
            if result is not None:
                return result
            
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result
        return wrapper
    return decorator


class NetworkMonitorService:
    def __init__(self, cache_duration: float = 1.0):
        # Initialize configuration manager and logger
        self.logger = BackendJSONLogger()
        # Create a config manager without logger to avoid the interface issue
        self.config_manager = ConfigManager()
        self.cache_duration = cache_duration  # Cache duration in seconds
        
        # Check if we're in simulation mode
        if self.config_manager.is_simulation_mode():
            # self.logger.log_metric("service", {"message": "Running in simulation mode"}, "INFO", "system")  # Commenting out to avoid logger dependency issues
            self._simulation_service = SimulationService(cache_duration=cache_duration)
            # Skip WMI initialization in simulation mode
        else:
            # self.logger.log_metric("service", {"message": "Running in real hardware collection mode"}, "INFO", "system")  # Commenting out to avoid logger dependency issues
            # Initialize the COM library for WMI access on Windows
            if platform.system().lower() == "windows":
                initialize_wmi()
            self._simulation_service = None
        
        # Initialize internal caches
        self._last_interface_refresh = 0
        self._cached_interfaces = []
        self._interfaces_lock = threading.Lock()
        self._last_hardware_refresh = 0
        self._cached_hardware_info = []
        self._hardware_lock = threading.Lock()
        self._performance_data_cache = []
        self._performance_lock = threading.Lock()
        self._last_performance_refresh = 0

    @cache_result(cache_duration=1.0)
    def get_network_interfaces(self) -> List[NetworkInterface]:
        """Get all network interfaces with their details."""
        try:
            if self._simulation_service:
                return self._simulation_service.get_network_interfaces()
            
            print("Service: Collecting network interfaces")  # Debug log
            interfaces = get_network_interfaces()
            result = []
            
            for interface_name, addresses in interfaces.items():
                # Determine interface type and status
                interface_type = self._determine_interface_type(interface_name)
                is_active = self._is_interface_active(interface_name)
                
                network_interface = NetworkInterface(
                    name=interface_name,
                    ipv4=addresses.get('IPv4'),
                    ipv6=addresses.get('IPv6'),
                    type=interface_type,
                    status="active" if is_active else "inactive",
                    is_up=is_active,
                    is_running=is_active
                )
                result.append(network_interface)
            
            print(f"Service: Collected {len(result)} network interfaces")  # Debug log
            return result
        except Exception as e:
            print(f"Error getting network interfaces: {str(e)}")
            # Return empty list instead of crashing
            return []

    @cache_result(cache_duration=1.0)
    def get_performance_metrics(self) -> List[PerformanceMetric]:
        """Get performance metrics for all network interfaces."""
        try:
            if self._simulation_service:
                return self._simulation_service.get_performance_metrics()
            
            print("Service: Collecting performance metrics")  # Debug log
            current_time = time.time()
            with self._performance_lock:
                # Check if we need to refresh performance data
                if current_time - self._last_performance_refresh >= self.cache_duration:
                    print("Service: Refreshing performance data")  # Debug log
                    result = []
                    
                    # Get initial network stats for throughput calculation
                    net_io = psutil.net_io_counters(pernic=True)
                    initial_stats = {
                        interface: (stats.bytes_sent, stats.bytes_recv, stats.packets_sent, stats.packets_recv)
                        for interface, stats in net_io.items()
                    }
                    
                    # Calculate final stats after a short delay for throughput calculation
                    time.sleep(0.2)  # Short delay for throughput calculation
                    final_net_io = psutil.net_io_counters(pernic=True)
                    final_stats = {
                        interface: (stats.bytes_sent, stats.bytes_recv, stats.packets_sent, stats.packets_recv)
                        for interface, stats in final_net_io.items()
                    }
                    
                    # Get latencies concurrently (this takes time)
                    interfaces = list(net_io.keys())
                    host = "8.8.8.8"
                    latencies = get_latency_concurrent(interfaces, host)
                    
                    # Calculate final metrics with actual values
                    for interface, initial_stat in initial_stats.items():
                        if interface in final_stats:
                            initial_bytes_sent, initial_bytes_recv, initial_packets_sent, initial_packets_recv = initial_stat
                            final_bytes_sent, final_bytes_recv, final_packets_sent, final_packets_recv = final_stats[interface]
                            
                            bytes_sent_interval = final_bytes_sent - initial_bytes_sent
                            bytes_recv_interval = final_bytes_recv - initial_bytes_recv
                            total_bytes_interval = bytes_sent_interval + bytes_recv_interval
                            elapsed_time = 0.2
                            throughput = calculate_throughput(total_bytes_interval, elapsed_time)
     
                            performance_metric = PerformanceMetric(
                                interface=interface,
                                bytes_sent=final_bytes_sent,
                                bytes_recv=final_bytes_recv,
                                packets_sent=final_packets_sent,
                                packets_recv=final_packets_recv,
                                latency=latencies.get(interface),
                                throughput=throughput,
                                timestamp=datetime.now()
                            )
                            result.append(performance_metric)
                    
                    self._performance_data_cache = result
                    self._last_performance_refresh = current_time
                else:
                    print("Service: Using cached performance data")  # Debug log

            print(f"Service: Returning {len(self._performance_data_cache)} performance metrics")  # Debug log
            return self._performance_data_cache
        except Exception as e:
            print(f"Error getting performance metrics: {str(e)}")
            # Return empty list instead of crashing
            return []

    @cache_result(cache_duration=5.0)
    def get_hardware_info(self) -> List[HardwareInfo]:
        """Get hardware information for network adapters."""
        if self._simulation_service:
            return self._simulation_service.get_hardware_info()
        
        print("Service: Collecting hardware info")  # Debug log
        # Initialize COM for this thread if on Windows
        if platform.system().lower() == "windows":
            try:
                pythoncom.CoInitialize()
            except Exception:
                # COM might already be initialized
                pass
        try:
            hardware_info_list = display_hardware_info()
        except Exception as e:
            print(f"Error accessing WMI: {e}")
            hardware_info_list = []
        finally:
            # Uninitialize COM for this thread if on Windows
            if platform.system().lower() == "windows":
                try:
                    pythoncom.CoUninitialize()
                except Exception:
                    # COM might not need uninitialization or already done
                    pass
        
        result = []
        if hardware_info_list:
            for hw in hardware_info_list:
                if hw and any(hw.values()):  # Filter out empty entries
                    hardware_info = HardwareInfo(
                        name=hw.get('Network Card', None),
                        description=hw.get('Vendor Description', None),
                        manufacturer=hw.get('Driver Manufacturer', None),
                        connection_status="connected",  # This would require actual status check
                        mac_address=hw.get('MAC Address', None),
                        max_link_speed=self._parse_speed(hw.get('Maximum Link Speed', 'N/A')),
                        current_link_speed=self._parse_speed(hw.get('Current Link Speed', 'N/A')),
                        driver_version=hw.get('Driver Version', None),
                        driver_date=hw.get('Driver Date', None),
                        driver_provider=hw.get('Driver Provider', None)
                    )
                    result.append(hardware_info)
        
        print(f"Service: Collected {len(result)} hardware info entries")  # Debug log
        return result

    def _determine_interface_type(self, interface_name: str) -> str:
        """Determine the type of network interface."""
        interface_name_lower = interface_name.lower()
        if 'loopback' in interface_name_lower or 'lo' == interface_name_lower:
            return "loopback"
        elif any(w in interface_name_lower for w in ['wi-fi', 'wireless', 'wlan', 'wifi']):
            return "wireless"
        elif any(w in interface_name_lower for w in ['ethernet', 'eth', 'lan']):
            return "ethernet"
        elif any(w in interface_name_lower for w in ['bluetooth']):
            return "bluetooth"
        elif any(w in interface_name_lower for w in ['virtual', 'vethernet', 'vmnet']):
            return "virtual"
        else:
            return "other"

    def _is_interface_active(self, interface_name: str) -> bool:
        """Check if a network interface is active/connected."""
        try:
            # Get interface status using psutil
            stats = psutil.net_if_stats()
            if interface_name in stats:
                interface_stat = stats[interface_name]
                # Check if interface is up and running
                return interface_stat.isup and interface_stat.speed > 0
            return False
        except:
            # If we can't determine the status, assume it's not active
            return False

    def _parse_speed(self, speed_str: str) -> Optional[int]:
        """Parse speed string to extract numeric value."""
        if speed_str == 'N/A' or not speed_str:
            return None
        try:
            # Extract numeric part from strings like "100 Mbps"
            import re
            numbers = re.findall(r'\d+', speed_str)
            if numbers:
                return int(numbers[0])
        except:
            pass
        return None

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics (interfaces, performance, hardware) at once."""
        return {
            "interfaces": self.get_network_interfaces(),
            "performance_metrics": self.get_performance_metrics(),
            "hardware_info": self.get_hardware_info(),
            "timestamp": datetime.now()
        }

    def refresh_all_metrics(self):
        """Force refresh of all metrics, clearing any cached data."""
        # The cache decorator will automatically refresh when cache expires
        # We can force this by updating the timestamps to an old time
        self._last_performance_refresh = 0
        # For the cache decorator functions, they will refresh on next call
