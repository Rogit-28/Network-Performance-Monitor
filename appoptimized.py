import streamlit as st
import psutil
import socket
import time
import numpy as np
import subprocess
import re
import platform
import pandas as pd
import concurrent.futures

def ping(host):
    """
    Pings a given host to measure latency and returns a list of round-trip times in milliseconds.
    """
    # Build the appropriate ping command based on the operating system.
    if platform.system().lower() == "windows":
        command = ["ping", host, "-n", "1"]  # Using a single ping for performance.
    else:
        command = ["ping", host, "-c", "1"]
    
    # Execute the command and capture the output.
    response = subprocess.run(command, stdout=subprocess.PIPE, text=True)
    
    # If the ping was successful, parse the output to extract latency values.
    if response.returncode == 0:
        if platform.system().lower() == "windows":
            latencies = re.findall(r'time=(\d+\.?\d*)ms', response.stdout)
        else:
            latencies = re.findall(r'time=(\d+\.?\d*) ms', response.stdout)
        return [float(latency) for latency in latencies]
    else:
        return None

def calculate_throughput(bytes_sent, elapsed_time):
    """
    Calculates network throughput in Mbps.
    """
    # The formula converts bytes to bits and then divides by the elapsed time in seconds.
    return (bytes_sent * 8) / (elapsed_time * 1_000_000)

def get_network_interfaces():
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

def display_hardware_info():
    """
    Gathers detailed hardware information for all connected network adapters (Windows only).
    """
    import wmi
    w = wmi.WMI()
    hardware_info = []

    # Query WMI for network adapter properties.
    for nic in w.Win32_NetworkAdapter():
        # A status of '2' indicates that the adapter is connected.
        if nic.NetConnectionStatus == 2:
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
    """
    Measures and displays real-time performance metrics for each network interface.
    """
    net_io = psutil.net_io_counters(pernic=True)
    metrics_info = []
    host = "8.8.8.8"  # Using Google's DNS for a reliable ping target.

    # Use a thread pool to ping all interfaces concurrently for better performance.
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

            # Calculate throughput over a short interval.
            start_time = time.time()
            time.sleep(0.1)  # A short sleep to ensure a non-zero elapsed time.
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

# Main application entry point
def main():
    """
    Sets up and runs the Streamlit application.
    """
    # On Windows, initialize the COM library for WMI access.
    if platform.system().lower() == "windows":
        import pythoncom
        pythoncom.CoInitialize()
     
    st.title("Network Monitoring Application")

    # Display a table of available network interfaces.
    st.subheader("Available Network Interfaces")
    interfaces = get_network_interfaces()
    iface_df = pd.DataFrame(interfaces).T.reset_index()
    iface_df.columns = ['Interface', 'IPv4', 'IPv6']
    st.table(iface_df)

    # Display hardware information, with a check for the operating system.
    st.subheader("Hardware Information")
    if platform.system().lower() == "windows":
        hardware_info = display_hardware_info()
        hardware_df = pd.DataFrame(hardware_info)
        st.table(hardware_df)
    else:
        st.write("Hardware information is not available on this platform.")

    # Display real-time performance metrics.
    st.subheader("Performance Metrics")
    performance_metrics = display_performance_metrics()
    performance_df = pd.DataFrame(performance_metrics)
    st.table(performance_df)

if __name__ == "__main__":
    main()
