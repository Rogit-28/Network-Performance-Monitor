import psutil
import time
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from .network_utils import calculate_throughput, get_latency_concurrent, is_interface_active


def display_performance_metrics() -> List[Dict[str, Any]]:
    """
    Measures and displays real-time performance metrics for each network interface.
    Uses concurrent processing to reduce measurement time and improve performance.
    Only active interfaces with network activity are included in the results.
    """
    net_io = psutil.net_io_counters(pernic=True)
    metrics_info = []
    host = "8.8.8"  # Using Google's DNS for a reliable ping target

    # Get initial network stats for throughput calculation
    initial_stats = {interface: (stats.bytes_sent, stats.bytes_recv, stats.packets_sent, stats.packets_recv) 
                     for interface, stats in net_io.items()}
    
    # Very small delay for throughput calculation - reduced to 0.05 seconds for faster initial load
    time.sleep(0.05)

    # Get final network stats
    final_net_io = psutil.net_io_counters(pernic=True)
    final_stats = {interface: (stats.bytes_sent, stats.bytes_recv, stats.packets_sent, stats.packets_recv) 
                   for interface, stats in final_net_io.items()}

    # Get interfaces list for concurrent ping
    interfaces = list(net_io.keys())
    
    # Get latencies concurrently (this can take time, so we do it concurrently)
    latencies = get_latency_concurrent(interfaces, host)

    # Calculate metrics for each interface
    for interface, initial_stat in initial_stats.items():
        if interface in final_stats:
            initial_bytes_sent, initial_bytes_recv, initial_packets_sent, initial_packets_recv = initial_stat
            final_bytes_sent, final_bytes_recv, final_packets_sent, final_packets_recv = final_stats[interface]
            
            # Calculate bytes sent and received during the interval
            bytes_sent_interval = final_bytes_sent - initial_bytes_sent
            bytes_recv_interval = final_bytes_recv - initial_bytes_recv
            total_bytes_interval = bytes_sent_interval + bytes_recv_interval
            
            # Calculate elapsed time (0.05 seconds as per sleep)
            elapsed_time = 0.05
            throughput = calculate_throughput(total_bytes_interval, elapsed_time)

            # Only include interfaces that are active (have network activity or are up)
            # Check if interface has activity or is likely active using multiple indicators
            interface_is_active = is_interface_active(interface)
            has_network_activity = (bytes_sent_interval > 0 or bytes_recv_interval > 0 or 
                                   initial_bytes_sent != final_bytes_sent or initial_bytes_recv != final_bytes_recv)
            has_latency_data = latencies.get(interface) is not None
            
            # An interface is considered active if it's flagged as up by the system OR has network activity OR has latency data
            is_active = interface_is_active or has_network_activity or has_latency_data
            
            if is_active:
                metrics_info.append({
                    'Interface': interface,
                    'Bytes Sent': final_bytes_sent,
                    'Bytes Received': final_bytes_recv,
                    'Packets Sent': final_packets_sent,
                    'Packets Received': final_packets_recv,
                    'Latency (ms)': latencies.get(interface),
                    'Throughput (Mbps)': throughput,
                })

    return metrics_info
