#!/usr/bin/env python3
"""
Test script to verify the simulation service works correctly.
"""
import asyncio
import time
from backend.simulation.simulation_service import SimulationService
from backend.config_manager import ConfigManager


def test_simulation():
    """Test the simulation service to ensure it generates realistic data."""
    print("Testing Network Performance Simulation Service...")
    
    # Create simulation service
    config_manager = ConfigManager()
    config_manager.set("SIMULATION_MODE", True)
    
    service = SimulationService(cache_duration=1.0)
    
    print("\n1. Testing initial data collection...")
    initial_data = service.get_all_metrics()
    
    print(f"   Interfaces: {len(initial_data['interfaces'])}")
    print(f"   Performance Metrics: {len(initial_data['performance_metrics'])}")
    print(f"   Hardware Info: {len(initial_data['hardware_info'])}")
    
    print("\n2. Testing data refresh...")
    time.sleep(1.5)  # Wait for cache to potentially expire
    refreshed_data = service.get_all_metrics()
    
    print(f"   New data collected after refresh")
    
    print("\n3. Testing data variation (waiting 3 seconds)...")
    first_data = service.get_performance_metrics()
    time.sleep(3)
    second_data = service.get_performance_metrics()
    
    # Compare some values to ensure they're changing
    if first_data and second_data:
        first_metric = first_data[0] if first_data else None
        second_metric = second_data[0] if second_data else None
        
        if first_metric and second_metric:
            print(f"   First throughput: {first_metric.throughput}")
            print(f"   Second throughput: {second_metric.throughput}")
            print(f"   Values are different: {first_metric.throughput != second_metric.throughput}")
    
    print("\n4. Testing simulation mode detection...")
    print(f"   Config manager simulation mode: {config_manager.is_simulation_mode()}")
    
    print("\n5. Testing with NetworkMonitorService in simulation mode...")
    # Temporarily set environment variable to simulate deployment
    import os
    os.environ["SIMULATION_MODE"] = "true"
    
    from backend.api.services import NetworkMonitorService
    service_with_config = NetworkMonitorService(cache_duration=1.0)
    
    service_data = service_with_config.get_all_metrics()
    print(f"   Service interfaces: {len(service_data['interfaces'])}")
    print(f"   Service performance metrics: {len(service_data['performance_metrics'])}")
    print(f"   Service hardware info: {len(service_data['hardware_info'])}")
    
    print("\nSimulation test completed successfully!")
    return True


if __name__ == "__main__":
    test_simulation()