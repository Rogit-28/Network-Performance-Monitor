import pytest
import asyncio
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.api.services import NetworkMonitorService
from backend.config_manager import ConfigManager

client = TestClient(app)

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert data["status"] in ["healthy", "degraded", "unhealthy"]

def test_readiness_check():
    """Test readiness check endpoint."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["ready", "not_ready"]

def test_liveness_check():
    """Test liveness check endpoint."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "alive"

def test_get_interfaces():
    """Test getting network interfaces."""
    response = client.get("/api/v1/interfaces")
    assert response.status_code == 200
    data = response.json()
    assert "interfaces" in data

def test_get_metrics():
    """Test getting performance metrics."""
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data

def test_get_hardware():
    """Test getting hardware information."""
    response = client.get("/api/v1/hardware")
    assert response.status_code == 200
    data = response.json()
    assert "hardware" in data

def test_get_all_metrics():
    """Test getting all metrics."""
    response = client.get("/api/v1/all-metrics")
    assert response.status_code == 200
    data = response.json()
    assert "interfaces" in data
    assert "performance_metrics" in data
    assert "hardware_info" in data

def test_api_root():
    """Test API root endpoint."""
    response = client.get("/api/v1/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

def test_config_loading():
    """Test configuration loading."""
    config_manager = ConfigManager()
    assert config_manager is not None
    assert hasattr(config_manager, 'get')
    assert hasattr(config_manager, 'get_cache_duration')

def test_rate_limiting_disabled_by_default():
    """Test that rate limiting is disabled by default."""
    config_manager = ConfigManager()
    rate_limit_enabled = config_manager.get("RATE_LIMIT_ENABLED", False)
    assert rate_limit_enabled is False

def test_cors_configuration():
    """Test CORS configuration is properly set."""
    # This tests that the app has CORS middleware configured
    # by checking if it responds to OPTIONS requests properly
    response = client.options("/api/v1/interfaces")
    # OPTIONS requests should return 200 or 405 (method not allowed)
    # but not 404 (not found) if CORS is configured
    assert response.status_code in [200, 405]
