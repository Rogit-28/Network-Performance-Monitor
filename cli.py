import psutil
import socket
import wmi

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

def display_performance_metrics():
    """
    Gathers and returns I/O statistics for each network interface.
    """
    net_io = psutil.net_io_counters(pernic=True)
    metrics_info = {}
    
    # Collect I/O statistics for each interface.
    for interface, stats in net_io.items():
        metrics_info[interface] = {
            'Bytes Sent': stats.bytes_sent,
            'Bytes Received': stats.bytes_recv,
            'Packets Sent': stats.packets_sent,
            'Packets Received': stats.packets_recv,
        }
    
    return metrics_info

def display_hardware_info():
    """
    Gathers detailed hardware information for all connected network adapters (Windows only).
    """
    w = wmi.WMI()
    hardware_info = {}

    # Query WMI for network adapter properties.
    for nic in w.Win32_NetworkAdapter():
        # A status of '2' indicates that the adapter is connected.
        if nic.NetConnectionStatus == 2:
            hardware_info[nic.Name] = {
                'Network Card': nic.Name,
                'Vendor Description': nic.Description,
                'MAC Address': nic.MACAddress,
                'Maximum Link Speed': f"{int(nic.MaxSpeed) // 1_000_000} Mbps" if nic.MaxSpeed else "N/A",
                'Current Link Speed': f"{int(nic.Speed) // 1_000_000} Mbps" if nic.Speed and nic.Speed.isdigit() else "N/A",
                'Hardware ID': nic.DeviceID,
                'Driver Manufacturer': getattr(nic, 'Manufacturer', 'N/A'),
                'Driver Description': nic.Description,
                'Driver Provider': getattr(nic, 'ProviderName', 'N/A'),
                'Driver Version': getattr(nic, 'DriverVersion', 'N/A'),
                'Driver Date': getattr(nic, 'DriverDate', 'N/A'),
                'DeviceInstanceId': nic.DeviceID,
                'Location Paths': getattr(nic, 'PNPDeviceID', 'N/A'),
            }

    return hardware_info


if __name__ == "__main__":
    # Display network interface information.
    interfaces = get_network_interfaces()
    print("Network Interfaces:")
    for iface, addr in interfaces.items():
        print(f"Interface: {iface}, Addresses: {addr}")

    # Display performance metrics.
    print("\nPerformance Metrics:")
    metrics = display_performance_metrics()
    for iface, metrics_data in metrics.items():
        print(f"Interface: {iface}, {metrics_data}")

    # Display hardware information.
    print("\nHardware Information:")
    hardware_info = display_hardware_info()
    for iface, info in hardware_info.items():
        print(f"Interface: {iface}")
        for key, value in info.items():
            print(f"  {key}: {value}")
