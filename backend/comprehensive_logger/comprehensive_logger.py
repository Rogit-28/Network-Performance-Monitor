import json
import logging
import logging.handlers
import os
import platform
import time
import gzip
import glob
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sys


class ComprehensiveLogger:
    """
    A comprehensive JSON-based logging system for network performance metrics with attribute-based filtering.
    This logger logs everything collected as key-value pairs to a master log file.
    """
    
    def __init__(self, log_file: str = "master_network_metrics.log", log_level: str = "INFO", sync_mode: bool = False, 
                 log_interval: float = 1.0, max_log_size: int = 10*1024*1024, retention_days: int = 7):
        """
        Initialize the comprehensive logger.
        
        Args:
            log_file: Path to the master log file
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            sync_mode: If True, ensures immediate file writes (useful for testing)
            log_interval: Interval in seconds between log operations
            max_log_size: Maximum size of log file before rotation (in bytes)
            retention_days: Number of days to retain logs
        """
        self.log_file = log_file
        self.log_level = getattr(logging, log_level.upper())
        self.session_id = f"sess_{int(time.time())}_{platform.node()}"
        self.hostname = platform.node()
        self.python_version = platform.python_version()
        self.os_version = platform.platform()
        self.platform_system = platform.system()
        self.log_counter = 0
        self.sync_mode = sync_mode  # New parameter to control synchronous logging
        self.file_handler = None # Store file handler to allow proper cleanup
        self.log_interval = log_interval  # Interval between log operations
        self.max_log_size = max_log_size  # Max log size in bytes (default 10MB)
        self.retention_days = retention_days  # Days to retain logs
        self.last_log_time = 0 # Track last log time for interval control
        
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Setup logging configuration with a custom handler that supports rotation and compression
        # Using RotatingFileHandler for log rotation based on size
        try:
            from logging.handlers import RotatingFileHandler
            # Custom handler that supports compression
            self.file_handler = CompressedRotatingFileHandler(log_file, maxBytes=max_log_size, backupCount=5)
        except ImportError:
            # Fallback to regular FileHandler if RotatingFileHandler is not available
            self.file_handler = logging.FileHandler(log_file)
        self.file_handler.setFormatter(logging.Formatter('%(message)s'))
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(message)s'))
        
        self.logger = logging.getLogger(f"ComprehensiveLogger_{id(self)}") # Use unique logger name to avoid conflicts
        self.logger.setLevel(self.log_level)
        self.logger.addHandler(self.file_handler)
        self.logger.addHandler(console_handler)
        self.logger.propagate = False # Prevent duplicate logs if there's a root logger
        
        # Initialize log management
        self._manage_log_retention()

    def _manage_log_retention(self):
        """Manage log retention by cleaning up old log files."""
        import os
        import glob
        from datetime import datetime, timedelta
        
        log_dir = os.path.dirname(self.log_file)
        base_name = os.path.basename(self.log_file)
        name_part, ext_part = os.path.splitext(base_name)
        
        # Find all related log files (including rotated ones)
        pattern = os.path.join(log_dir, f"{name_part}*{ext_part}*")
        log_files = glob.glob(pattern)
        
        # Remove files older than retention period
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        for file_path in log_files:
            try:
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if file_time < cutoff_date:
                    os.remove(file_path)
            except OSError:
                # Skip files that can't be accessed
                continue

    def update_log_settings(self, log_level: str = None, log_interval: float = None, 
                           max_log_size: int = None, retention_days: int = None):
        """
        Update logging settings dynamically.
        
        Args:
            log_level: New logging level (DEBUG, INFO, WARNING, ERROR)
            log_interval: New interval in seconds between log operations
            max_log_size: New maximum size of log file before rotation (in bytes)
            retention_days: New number of days to retain logs
        """
        if log_level is not None:
            self.log_level = getattr(logging, log_level.upper())
            self.logger.setLevel(self.log_level)
        
        if log_interval is not None:
            self.log_interval = log_interval

        if max_log_size is not None:
            self.max_log_size = max_log_size

        if retention_days is not None:
            self.retention_days = retention_days
            # Apply retention policy with new setting
            self._manage_log_retention()

    def flush(self):
        """Force all pending log writes to be written to disk."""
        for handler in self.logger.handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
        # Also force a sync to disk for the file
        if hasattr(self, 'log_file'):
            try:
                with open(self.log_file, 'a') as f:
                    os.fsync(f.fileno())
            except:
                # If fsync fails, just continue (might be on a system that doesn't support it)
                pass

    def wait_for_log_completion(self, timeout: float = 5.0) -> bool:
        """
        Wait for all pending log operations to complete, up to a timeout.
        Returns True if all logs were written within the timeout, False otherwise.
        """
        start_time = time.time()
        initial_counter = self.log_counter
        
        # In a real implementation, we might need to track pending operations differently
        # For now, we'll flush and briefly wait, then check if the counter has stabilized
        while time.time() - start_time < timeout:
            self.flush()
            time.sleep(0.01) # Brief pause to allow I/O to complete
            # If counter hasn't changed for a brief period, assume it's stable
            if self.log_counter == initial_counter:
                return True
            initial_counter = self.log_counter
            
        return False  # Timeout reached

    def close(self):
        """Close the logger and release file handles."""
        # Ensure all pending logs are written before closing
        for handler in self.logger.handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
            # Close the file handler specifically if it has a close method
            if hasattr(handler, 'close'):
                handler.close()
        # Remove all handlers from the logger to fully release resources
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            # Also close the handler after removing it
            if hasattr(handler, 'close'):
                handler.close()
        # Set logger to disabled state to prevent further logging
        self.logger.disabled = True

    def _generate_log_id(self, metric_type: str) -> str:
        """Generate a unique log ID for each log entry."""
        self.log_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
        return f"{metric_type[:4]}_{self.log_counter:03d}_{timestamp}"
    
    def log_metric(self, metric_type: str, data: Dict, level: str = "INFO", metric_category: str = "general"):
        """
        Log a metric in comprehensive JSON format.
        
        Args:
            metric_type: Type of metric being logged
            data: Dictionary containing the metric data
            level: Log level (INFO, WARNING, ERROR, DEBUG)
            metric_category: Category of the metric (e.g., performance, configuration, hardware)
        """
        # Check if enough time has passed since the last log for this metric type
        current_time = time.time()
        if current_time - self.last_log_time < self.log_interval:
            return # Skip logging if interval hasn't been reached yet

        log_entry = {
            "log_id": self._generate_log_id(metric_type),
            "timestamp": datetime.now().isoformat(),
            "timestamp_epoch": time.time(),
            "timezone": time.strftime("%Z", time.gmtime()),
            "log_level": level.upper(),
            "metric_category": metric_category,
            "metric_type": metric_type,
            "version": "1.0",
            "system_info": {
                "platform": self.platform_system,
                "hostname": self.hostname,
                "os_version": self.os_version,
                "python_version": self.python_version
            },
            "session_id": self.session_id,
            "data": data,
            "metadata": {
                "collection_method": "direct_api",
                "precision": "high",
                "tags": [metric_category, metric_type]
            }
        }
        
        log_message = json.dumps(log_entry)
        getattr(self.logger, level.lower(), self.logger.info)(log_message)
        
        # Update the last log time
        self.last_log_time = current_time

        # In sync mode, force flush the handlers to ensure immediate writing
        if self.sync_mode:
            for handler in self.logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
            # Also force a sync to disk for the file
            if hasattr(self, 'log_file'):
                # Try to sync the file to disk
                try:
                    with open(self.log_file, 'a') as f:
                        os.fsync(f.fileno())
                except:
                    # If fsync fails, just continue (might be on a system that doesn't support it)
                    pass
    
    def log_interfaces(self, interfaces: Dict):
        """Log network interface information with enhanced structure."""
        enhanced_interfaces = {
            "interfaces": []
        }
        
        for interface_name, addresses in interfaces.items():
            interface_info = {
                "name": interface_name,
                "type": self._determine_interface_type(interface_name),
                "status": "active",  # This would require additional logic to determine actual status
                "addresses": {
                    "ipv4": [addresses.get("IPv4")] if addresses.get("IPv4") else [],
                    "ipv6": [addresses.get("IPv6")] if addresses.get("IPv6") else []
                },
                "properties": self._get_interface_properties(interface_name)
            }
            enhanced_interfaces["interfaces"].append(interface_info)
        
        self.log_metric('interface_details', enhanced_interfaces, "INFO", "configuration")

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

    def _get_interface_properties(self, interface_name: str) -> Dict:
        """Get properties for an interface."""
        # This is a simplified version - in a real implementation, you would query actual interface properties
        return {
            "is_up": True,  # This would require actual interface status check
            "is_running": True,
            "is_broadcast": True,
            "is_loopback": "loopback" in interface_name.lower(),
            "is_pointtopoint": False,
            "is_multicast": True
        }

    def log_performance_metrics(self, metrics: List[Dict]):
        """Log performance metrics with enhanced structure."""
        for metric in metrics:
            enhanced_metric = {
                "interface": {
                    "name": metric.get('Interface', 'unknown'),
                    "type": self._determine_interface_type(metric.get('Interface', 'unknown')),
                    "status": "up",
                    "properties": {
                        "bytes_sent": metric.get('Bytes Sent', 0),
                        "bytes_received": metric.get('Bytes Received', 0),
                        "packets_sent": metric.get('Packets Sent', 0),
                        "packets_received": metric.get('Packets Received', 0)
                    },
                    "performance": {
                        "latency_ms": metric.get('Latency (ms)', None),
                        "throughput_mbps": metric.get('Throughput (Mbps)', 0.0)
                    },
                    "network_config": self._get_network_config(metric.get('Interface', 'unknown'))
                }
            }
            self.log_metric('interface_metrics', enhanced_metric, "INFO", "performance")

    def _get_network_config(self, interface_name: str) -> Dict:
        """Get network configuration for an interface."""
        # This would be populated with actual network configuration in a real implementation
        return {
            "ipv4": "unknown",
            "ipv6": "unknown",
            "subnet_mask": "unknown",
            "mac_address": "unknown",
            "gateway": "unknown",
            "dns_servers": []
        }

    def log_hardware_info(self, hardware_info: List[Dict]):
        """Log hardware information with enhanced structure."""
        for hw in hardware_info:
            enhanced_hw = {
                "adapter": {
                    "name": hw.get('Network Card', 'unknown'),
                    "description": hw.get('Vendor Description', 'unknown'),
                    "manufacturer": hw.get('Driver Manufacturer', 'unknown'),
                    "connection_status": "connected",  # This would require actual status check
                    "interface_status": "up",
                    "physical_properties": {
                        "mac_address": hw.get('MAC Address', 'unknown'),
                        "max_link_speed_mbps": self._parse_speed(hw.get('Maximum Link Speed', 'N/A')),
                        "current_link_speed_mbps": self._parse_speed(hw.get('Current Link Speed', 'N/A')),
                    },
                    "driver_info": {
                        "version": hw.get('Driver Version', 'unknown'),
                        "date": hw.get('Driver Date', 'unknown'),
                        "provider": hw.get('Driver Provider', 'unknown'),
                        "manufacturer": hw.get('Driver Manufacturer', 'unknown'),
                        "driver_name": hw.get('Driver Description', 'unknown')
                    },
                    "hardware_info": {
                        "device_id": hw.get('DeviceInstanceId', 'unknown'),
                        "hardware_id": hw.get('Hardware ID', 'unknown'),
                        "location_path": hw.get('Location Paths', 'unknown'),
                    },
                    "capabilities": {
                        "supports_wake_on_lan": True,  # Would need actual capability check
                        "supports_power_management": True,
                        "supports_promiscuous_mode": False
                    }
                }
            }
            self.log_metric('network_adapter', enhanced_hw, "INFO", "hardware")

    def _parse_speed(self, speed_str: str) -> int:
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

    def log_error(self, error_msg: str, context: str = "", component: str = "network_monitor"):
        """Log an error with enhanced context."""
        error_data = {
            "error": {
                "type": "NetworkError",  # This could be more specific based on the actual error
                "message": error_msg,
                "context": context,
                "severity": "high",  # This could be determined by the error type
                "component": component,
                "stack_trace": None, # Would capture actual stack trace in real implementation
                "recovery_suggestion": "Check network connectivity and configuration"
            }
        }
        self.log_metric('application_error', error_data, 'ERROR', 'system')


# Custom handler for compressed logging
class CompressedRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """
    Extended RotatingFileHandler that compresses old log files using gzip.
    """
    def __init__(self, filename, maxBytes=0, backupCount=0, encoding=None, delay=False):
        super().__init__(filename, maxBytes=maxBytes, backupCount=backupCount, encoding=encoding, delay=delay)

    def doRollover(self):
        """
        Override the doRollover method to compress the old log file before creating a new one.
        """
        import gzip
        import os
        
        if self.stream:
            self.stream.close()
            self.stream = None

        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = f"{self.baseFilename}.{i}.gz"
                dfn = f"{self.baseFilename}.{i + 1}.gz"
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)

            dfn = f"{self.baseFilename}.1.gz"
            if os.path.exists(dfn):
                os.remove(dfn)

            # Compress the current log file before renaming
            with open(self.baseFilename, 'rb') as f_in:
                with gzip.open(dfn, 'wb') as f_out:
                    f_out.writelines(f_in)

            # Remove the original uncompressed file
            os.remove(self.baseFilename)

        if not self.delay:
            self.stream = self._open()
