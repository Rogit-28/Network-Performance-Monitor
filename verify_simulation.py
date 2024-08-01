import os
# Set simulation mode before importing any modules
os.environ['SIMULATION_MODE'] = 'true'

from backend.api.services import NetworkMonitorService

# Create service instance
service = NetworkMonitorService()

print(f'Simulation mode: {service.config_manager.is_simulation_mode()}')

# Get metrics
metrics = service.get_all_metrics()

print(f'Got metrics: {len(metrics["interfaces"])} interfaces, {len(metrics["performance_metrics"])} perf metrics, {len(metrics["hardware_info"])} hardware info')

# Verify we're getting simulated data
if service.config_manager.is_simulation_mode():
    print("SUCCESS: Running in simulation mode with simulated data")
else:
    print("ERROR: Not running in simulation mode as expected")