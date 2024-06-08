import subprocess
import re
import platform
import time
import numpy as np
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import socket


def ping(host: str) -> Optional[List[float]]:
    """
    Pings a given host to measure latency and returns a list of round-trip times in milliseconds.
    Supports Windows, Linux, and Darwin/macOS platforms.
    """
    # Build the appropriate ping command based on the operating system.
    if platform.system().lower() == "windows":
        command = ["ping", "-n", "4", host]
    elif platform.system().lower() == "darwin":  # macOS
        command = ["ping", "-c", "4", host]
    else:  # Linux and other Unix-like systems
        command = ["ping", "-c", "4", host]
    
    # Execute the command and capture the output.
    response = subprocess.run(command, stdout=subprocess.PIPE, text=True)
    
    # If the ping was successful, parse the output to extract latency values.
    if response.returncode == 0:
        if platform.system().lower() == "windows":
            latencies = re.findall(r'time=(\d+\.?\d*)ms', response.stdout)
        else:  # Linux and Darwin
            latencies = re.findall(r'time=(\d+\.?\d*) ms', response.stdout)
        return [float(latency) for latency in latencies]
    else:
        return None


def calculate_throughput(bytes_sent: int, elapsed_time: float) -> float:
    """
    Calculates network throughput in Mbps.
    """
    # The formula converts bytes to bits and then divides by the elapsed time in seconds.
    if elapsed_time == 0:
        return 0
    return (bytes_sent * 8) / (elapsed_time * 1_000_000)


def get_network_interfaces() -> Dict[str, Dict[str, str]]:
    """
    Retrieves a list of all network interfaces and their IPv4 and IPv6 addresses.
    """
    interfaces = psutil.net_if_addrs()
    interface_info = {}
    
    # Iterate over each interface and its addresses, filtering for IP addresses.
    for interface, addresses in interfaces.items():
        interface_info[interface] = {}
        for addr in addresses:
            if addr.family == socket.AF_INET:
                interface_info[interface]['IPv4'] = addr.address
            elif addr.family == socket.AF_INET6:
                interface_info[interface]['IPv6'] = addr.address
    
    return interface_info


def is_interface_active(interface_name: str) -> bool:
    """
    Check if a network interface is active/connected.
    """
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


def get_latency_concurrent(interfaces: List[str], host: str = "8.8.8.8") -> Dict[str, Optional[float]]:
    """
    Get latency for multiple interfaces concurrently.
    """
    latencies = {}
    with ThreadPoolExecutor(max_workers=min(len(interfaces), 4)) as executor:
        # Submit ping tasks for all interfaces
        future_to_interface = {
            executor.submit(ping, host): interface for interface in interfaces
        }
        # Collect results as they complete
        for future in as_completed(future_to_interface):
            interface = future_to_interface[future]
            try:
                result = future.result()
                latencies[interface] = float(np.mean(result)) if result else None
            except Exception:
                latencies[interface] = None
    return latencies
