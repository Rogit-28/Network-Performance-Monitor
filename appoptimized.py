import streamlit as st
import psutil
import socket
import wmi
import time
import numpy as np
import subprocess
import re
import platform
import pandas as pd
import pythoncom
import concurrent.futures

def ping(host):
    # Ping any host to return latency(ms)
    if platform.system().lower() == "windows":
        command = ["ping", host, "-n", "1"]  # Reduced to 1 ping
    else:
        command = ["ping", host, "-c", "1"]
    
    response = subprocess.run(command, stdout=subprocess.PIPE, text=True)
    
    if response.returncode == 0:
        latencies = re.findall(r'time=(\d+\.?\d*) ms', response.stdout) if platform.system().lower() != "windows" else re.findall(r'time=(\d+\.?\d*)ms', response.stdout)
        return list(map(float, latencies))
    else:
        return None

def calculate_throughput(bytes_sent, elapsed_time):
    # Throughput (mbps)
    return (bytes_sent * 8) / (elapsed_time * 1_000_000)  # Convert bytes to bits, seconds to microseconds

def get_network_interfaces():
    interfaces = psutil.net_if_addrs()  # Get all network interfaces and their addresses
    interface_info = {}
    
    for interface, addresses in interfaces.items():
        interface_info[interface] = {}
        for addr in addresses:
            if addr.family == socket.AF_INET:  # Filter for IPv4 addresses
                interface_info[interface]['IPv4'] = addr.address
            elif addr.family == socket.AF_INET6:  # Filter for IPv6 addresses
                interface_info[interface]['IPv6'] = addr.address
    
    return interface_info

def display_hardware_info():
    w = wmi.WMI()
    hardware_info = []

    for nic in w.Win32_NetworkAdapter():
        if nic.NetConnectionStatus == 2:  # 2 is the state code for "connected", we're retrieving all connected NIs
            hardware_info.append({
                'Network Card': nic.Name,
                'Vendor Description': nic.Description,
                'MAC Address': nic.MACAddress,
                'Maximum Link Speed': f"{int(nic.MaxSpeed) // 1_000_000} Mbps" if nic.MaxSpeed else "N/A",
                'Current Link Speed': f"{int(nic.Speed) // 1_000_000} Mbps" if nic.Speed and nic.Speed.isdigit() else "N/A",
                'Hardware ID': nic.DeviceID,
                'Driver Manufacturer': getattr(nic, 'Manufacturer', 'N/A'),
                'Driver Description': nic.Description,
                'DeviceInstanceId': nic.DeviceID,
                'Location Paths': getattr(nic, 'PNPDeviceID', 'N/A'),
            })

    return hardware_info

def display_performance_metrics():
    net_io = psutil.net_io_counters(pernic=True)  # I/O stats for every active, available interface
    metrics_info = []
    host = "8.8.8.8"  # Google DNS

    # Use ThreadPoolExecutor to run ping in parallel for each interface
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_interface = {executor.submit(ping, host): interface for interface in net_io}

        for future in concurrent.futures.as_completed(future_to_interface):
            interface = future_to_interface[future]
            stats = net_io[interface]
            
            try:
                latencies = future.result()
                latency = np.mean(latencies) if latencies else None
            except Exception as exc:
                latency = None

            start_time = time.time()
            time.sleep(0.1)  # Reduced sleep to 0.1 seconds
            elapsed_time = time.time() - start_time

            throughput = calculate_throughput(stats.bytes_sent + stats.bytes_recv, elapsed_time)

            metrics_info.append({
                'Interface': interface,
                'Bytes Sent': stats.bytes_sent,
                'Bytes Received': stats.bytes_recv,
                'Packets Sent': stats.packets_sent,
                'Packets Received': stats.packets_recv,
                'Latency (ms)': latency,
                'Throughput (Mbps)': throughput,
            })

    return metrics_info

# Streamlit
def main():
    pythoncom.CoInitialize()
     
    st.title("Network Monitoring Application")

    # All available Network Interface
    st.subheader("Available Network Interfaces")
    interfaces = get_network_interfaces()
    iface_df = pd.DataFrame(interfaces).T.reset_index()
    iface_df.columns = ['Interface', 'IPv4', 'IPv6']
    st.table(iface_df)

    # Hardware info of available NI
    st.subheader("Hardware Information")
    hardware_info = display_hardware_info()
    hardware_df = pd.DataFrame(hardware_info)
    st.table(hardware_df)

    # Performance Metrics of available NI
    st.subheader("Performance Metrics")
    performance_metrics = display_performance_metrics()
    performance_df = pd.DataFrame(performance_metrics)
    st.table(performance_df)

if __name__ == "__main__":
    main()
