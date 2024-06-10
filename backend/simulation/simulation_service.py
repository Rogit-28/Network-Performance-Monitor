import random
import time
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from backend.api.models import NetworkInterface, PerformanceMetric, HardwareInfo
import threading
import psutil


class SimulationService:
    """
    A service that simulates network performance data with realistic highs and lows.
    This replaces actual hardware collection for deployment purposes.
    """
    
    def __init__(self, cache_duration: float = 1.0):
        self.cache_duration = cache_duration
        self._last_refresh = 0
        self._cached_data = None
        self._lock = threading.Lock()
        
        # Initialize simulation parameters
        self._time_offset = time.time()
        self._base_throughput = 1000000  # 1 MB/s base
        self._base_latency = 20  # 20ms base latency
        self._base_packet_loss = 0.1  # 0.1% base packet loss
        
        # Generate some realistic interface names
        self._interfaces = [
            "eth0", "wlan0", "eth1", "enp0s3", "wlp2s0", 
            "en0", "en1", "WiFi", "Ethernet", "Local Area Connection"
        ]
        
        # Hardware info simulation
        self._hardware_manufacturers = [
            "Intel Corporation", "Realtek Semiconductor", "Broadcom", 
            "Qualcomm Atheros", "Marvell Technology", "ASUSTek Computer"
        ]
        
        self._hardware_descriptions = [
            "Ethernet Controller", "Wireless Network Adapter", 
            "Gigabit Network Connection", "Wi-Fi 6 Adapter", 
            "Thunderbolt Ethernet", "USB Ethernet Adapter"
        ]

    def _generate_realistic_data(self) -> Dict[str, Any]:
        """Generate realistic network performance data with fluctuations."""
        current_time = time.time()
        
        # Create a time-based pattern to simulate natural fluctuations
        time_factor = (current_time - self._time_offset) / 10  # Slow oscillation
        
        # Generate simulated interfaces
        interfaces = []
        for i, interface_name in enumerate(self._interfaces[:5]):  # Use first 5 interfaces
            # Simulate interface status with some variation
            is_up = random.random() > 0.05  # 95% uptime
            
            interfaces.append(NetworkInterface(
                name=interface_name,
                ipv4=f"192.168.{random.randint(1, 255)}.{random.randint(10, 250)}" if is_up else None,
                ipv6=f"2001:db8:{random.randint(1000, 9999)}::{random.randint(10, 99)}" if is_up else None,
                type="wireless" if "wlan" in interface_name or "WiFi" in interface_name else "ethernet",
                status="active" if is_up else "inactive",
                is_up=is_up,
                is_running=is_up
            ))
        
        # Generate simulated performance metrics with realistic fluctuations
        performance_metrics = []
        for interface in interfaces:
            if interface.is_up:
                # Base values with time-based oscillations
                base_throughput = self._base_throughput
                base_latency = self._base_latency
                base_packet_loss = self._base_packet_loss
                
                # Add time-based variations (sine waves for natural oscillation)
                time_var = math.sin(time_factor + hash(interface.name) % 100) * 0.5  # -0.5 to 0.5
                
                # Add random noise for more realistic variation
                noise = random.uniform(-0.2, 0.2)
                
                # Calculate final values with realistic constraints
                throughput_factor = max(0.1, 1.0 + time_var + noise)  # 0.1x to 1.7x of base
                latency_factor = max(0.5, 1.0 - time_var * 0.3 + noise * 0.2)  # Inverse relationship with throughput
                packet_loss_factor = max(0.1, 1.0 + time_var * 0.1 + noise * 0.3)
                
                # Calculate final values
                throughput = base_throughput * throughput_factor
                latency = max(5, base_latency * latency_factor)  # Minimum 5ms latency
                packet_loss = max(0, base_packet_loss * packet_loss_factor)
                
                # Simulate packet counts with realistic growth
                base_packets_sent = int(current_time * 1000 + hash(interface.name) * 100)
                base_packets_recv = int(current_time * 1200 + hash(interface.name) * 120)
                
                # Add some random variation to packet counts
                packets_sent = base_packets_sent + random.randint(0, 500)
                packets_recv = base_packets_recv + random.randint(0, 600)
                
                performance_metrics.append(PerformanceMetric(
                    interface=interface.name,
                    bytes_sent=int(throughput * 0.8),  # 80% of throughput as sent data
                    bytes_recv=int(throughput),
                    packets_sent=packets_sent,
                    packets_recv=packets_recv,
                    latency=round(latency, 2),
                    throughput=round(throughput, 2),
                    timestamp=datetime.now()
                ))
        
        # Generate simulated hardware info
        hardware_info = []
        for i, interface in enumerate(interfaces[:3]):  # Use first 3 interfaces
            hardware_info.append(HardwareInfo(
                name=f"{self._hardware_descriptions[i % len(self._hardware_descriptions)]} {i+1}",
                description=self._hardware_descriptions[i % len(self._hardware_descriptions)],
                manufacturer=self._hardware_manufacturers[i % len(self._hardware_manufacturers)],
                connection_status="connected" if interface.is_up else "disconnected",
                mac_address=f"{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}",
                max_link_speed=random.choice([100, 1000, 2500, 5000, 10000]),  # Mbps
                current_link_speed=random.choice([100, 1000, 2500]) if interface.is_up else 0,
                driver_version=f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 99)}",
                driver_date=f"{random.randint(2020, 2024)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                driver_provider="Simulated Driver"
            ))
        
        return {
            "interfaces": interfaces,
            "performance_metrics": performance_metrics,
            "hardware_info": hardware_info,
            "timestamp": datetime.now()
        }

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all simulated metrics, with caching."""
        current_time = time.time()
        
        with self._lock:
            if (current_time - self._last_refresh) >= self.cache_duration or self._cached_data is None:
                self._cached_data = self._generate_realistic_data()
                self._last_refresh = current_time
        
        return self._cached_data

    def get_network_interfaces(self) -> List[NetworkInterface]:
        """Get simulated network interfaces."""
        return self.get_all_metrics()["interfaces"]

    def get_performance_metrics(self) -> List[PerformanceMetric]:
        """Get simulated performance metrics."""
        return self.get_all_metrics()["performance_metrics"]

    def get_hardware_info(self) -> List[HardwareInfo]:
        """Get simulated hardware information."""
        return self.get_all_metrics()["hardware_info"]

    def refresh_all_metrics(self):
        """Force refresh of all metrics."""
        with self._lock:
            self._cached_data = self._generate_realistic_data()
            self._last_refresh = time.time()