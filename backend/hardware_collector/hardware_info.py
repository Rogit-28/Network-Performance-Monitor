import wmi
import platform
import pythoncom
from typing import List, Dict, Any


def initialize_wmi():
    """
    Initialize the WMI library for Windows systems.
    This should be called before using any WMI functionality on Windows.
    """
    if platform.system().lower() == "windows":
        pythoncom.CoInitialize()


def display_hardware_info() -> List[Dict[str, Any]]:
    """
    Gathers detailed hardware information for all connected network adapters (Windows only).
    For macOS and Linux, returns an empty list as hardware information is not available through WMI on these platforms.
    """
    system = platform.system().lower()
    if system == "windows":
        # Initialize COM library for WMI access
        try:
            w = wmi.WMI()
            hardware_info = []

            # Query WMI for network adapter properties.
            for nic in w.Win32_NetworkAdapter():
                # A status of '2' indicates that the adapter is connected.
                if hasattr(nic, 'NetConnectionStatus') and nic.NetConnectionStatus == 2:
                    max_speed = 0
                    if hasattr(nic, 'Speed') and nic.Speed:
                        try:
                            if isinstance(nic.Speed, str) and nic.Speed.isdigit():
                                max_speed = int(nic.Speed) // 1_000_000  # Convert from bps to Mbps
                            elif isinstance(nic.Speed, (int, float)):
                                max_speed = int(nic.Speed) // 1_000_000  # Convert from bps to Mbps
                        except (ValueError, TypeError):
                            max_speed = 0
                    speed_str = f"{max_speed} Mbps" if max_speed > 0 else "N/A"
                    
                    hardware_info.append({
                        'Network Card': getattr(nic, 'Name', 'N/A'),
                        'Vendor Description': getattr(nic, 'Description', 'N/A'),
                        'MAC Address': getattr(nic, 'MACAddress', 'N/A'),
                        'Maximum Link Speed': speed_str,
                        'Hardware ID': getattr(nic, 'DeviceID', 'N/A'),
                        'Driver Manufacturer': getattr(nic, 'Manufacturer', 'N/A'),
                        'Driver Description': getattr(nic, 'Description', 'N/A'),
                        'Driver Provider': getattr(nic, 'ProviderName', 'N/A'),
                        'Driver Version': getattr(nic, 'DriverVersion', 'N/A'),
                        'Driver Date': getattr(nic, 'DriverDate', 'N/A'),
                        'DeviceInstanceId': getattr(nic, 'DeviceID', 'N/A'),
                        'Location Paths': getattr(nic, 'PNPDeviceID', 'N/A'),
                    })

            return hardware_info
        except Exception as e:
            # Return empty list if WMI access fails
            print(f"Error accessing WMI: {e}")
            return []
    elif system == "darwin":
        # For macOS, we could implement an alternative method using system_profiler or other macOS-specific tools
        # For now, returning an empty list
        return get_macos_hardware_info()
    else:
        # For Linux and other systems, return empty list
        return []


def get_macos_hardware_info() -> List[Dict[str, Any]]:
    """
    Alternative method to get hardware information on macOS using system commands.
    This is a placeholder implementation that returns an empty list until
    the actual implementation is completed.
    """
    # TODO: Implement macOS hardware information gathering using system_profiler, networksetup, or other macOS tools
    # This could involve parsing output from commands like:
    # - system_profiler SPNetworkDataType
    # - networksetup -listallhardwareports
    # - ifconfig for interface details
    return []


def get_network_config(interface_name: str) -> Dict[str, Any]:
    """
    Get network configuration for an interface (placeholder implementation).
    This would be populated with actual network configuration in a real implementation.
    """
    return {
        "ipv4": "unknown",
        "ipv6": "unknown",
        "subnet_mask": "unknown",
        "mac_address": "unknown",
        "gateway": "unknown",
        "dns_servers": []
    }
