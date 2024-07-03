#!/usr/bin/env python3
"""
Test script to verify the WebSocket simulation works correctly.
"""
import asyncio
import os
from backend.api.websocket_handler import manager
from backend.api.services import NetworkMonitorService


async def test_websocket_simulation():
    """Test the WebSocket simulation functionality."""
    print("Testing WebSocket Simulation Integration...")
    
    # Set simulation mode
    os.environ["SIMULATION_MODE"] = "true"
    
    # Create a NetworkMonitorService in simulation mode
    service = NetworkMonitorService(cache_duration=1.0)
    
    print(f"Service is in simulation mode: {service.config_manager.is_simulation_mode()}")
    
    # Test that the service returns simulated data
    metrics = service.get_all_metrics()
    print(f"Retrieved metrics: {len(metrics['interfaces'])} interfaces, {len(metrics['performance_metrics'])} performance metrics, {len(metrics['hardware_info'])} hardware info")
    
    # Test the manager's service
    print(f"Manager service is in simulation mode: {manager.service.config_manager.is_simulation_mode()}")
    
    # Test getting metrics from the manager's service
    manager_metrics = manager.service.get_all_metrics()
    print(f"Manager metrics: {len(manager_metrics['interfaces'])} interfaces, {len(manager_metrics['performance_metrics'])} performance metrics, {len(manager_metrics['hardware_info'])} hardware info")
    
    # Test historical data functionality
    initial_historical = manager.get_historical_data(limit=10)
    print(f"Initial historical data points: {len(initial_historical)}")
    
    # Simulate some data collection
    all_metrics = manager.service.get_all_metrics()
    data = {
        "timestamp": "2023-01-01T00:00:00",
        "interfaces": [interface.__dict__ for interface in all_metrics["interfaces"]],
        "performance_metrics": [metric.__dict__ for metric in all_metrics["performance_metrics"]],
        "hardware_info": [hw.__dict__ for hw in all_metrics["hardware_info"]]
    }
    
    # Store data in historical buffer
    manager._store_historical_data(data)
    
    updated_historical = manager.get_historical_data(limit=10)
    print(f"Updated historical data points: {len(updated_historical)}")
    
    print("WebSocket simulation integration test completed successfully!")
    return True


if __name__ == "__main__":
    asyncio.run(test_websocket_simulation())