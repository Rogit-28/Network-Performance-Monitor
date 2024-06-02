import json
import os
from typing import Dict, Any, Optional
from backend.comprehensive_logger.comprehensive_logger import ComprehensiveLogger


class ConfigManager:
    """
    Manages application configuration and settings.
    """
    
    def __init__(self, config_file: str = "config.json", logger: Optional[ComprehensiveLogger] = None):
        self.config_file = config_file
        self.logger = logger
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from JSON file with environment variable overrides.
        """
        # Load default configuration
        config = self._get_default_config()
        
        # Try to load from JSON file
        try:
            with open(self.config_file, 'r') as f:
                file_config = json.load(f)
                # Merge file config with defaults, prioritizing file config
                config.update(file_config)
        except FileNotFoundError:
            if self.logger:
                self.logger.log_metric("config", {"message": f"Config file {self.config_file} not found, using defaults"}, "WARNING", "system")
        except json.JSONDecodeError:
            if self.logger:
                self.logger.log_metric("config", {"message": f"Invalid JSON in {self.config_file}, using defaults"}, "ERROR", "system")
        
        # Override with environment variables
        config.update({
            "SIMULATION_MODE": os.getenv("SIMULATION_MODE", str(config.get("SIMULATION_MODE", False))).lower() == "true",
            "CACHE_DURATION": float(os.getenv("CACHE_DURATION", str(config.get("update_interval", 1.0)))),
            "STREAMING_INTERVAL": float(os.getenv("STREAMING_INTERVAL", str(config.get("update_interval", 2.0)))),
            "MAX_HISTORY_POINTS": int(os.getenv("MAX_HISTORY_POINTS", str(config.get("max_history_points", 200)))),
            "API_HOST": os.getenv("API_HOST", config.get("api_host", "127.0.1")),
            "API_PORT": int(os.getenv("API_PORT", str(config.get("api_port", 8000)))),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", config.get("logging", {}).get("log_level", "INFO")),
            "ENABLE_CORS": os.getenv("ENABLE_CORS", str(config.get("security", {}).get("enable_cors", True))).lower() == "true",
            "ALLOWED_ORIGINS": os.getenv("ALLOWED_ORIGINS", ",".join(config.get("security", {}).get("allowed_origins", ["*"]))).split(","),
            "MAX_CONCURRENT_REQUESTS": int(os.getenv("MAX_CONCURRENT_REQUESTS", str(config.get("max_concurrent_requests", 100)))),
            "RATE_LIMIT_ENABLED": os.getenv("RATE_LIMIT_ENABLED", str(config.get("security", {}).get("enable_rate_limiting", False))).lower() == "true",
            "RATE_LIMIT_REQUESTS": int(os.getenv("RATE_LIMIT_REQUESTS", str(config.get("rate_limit", {}).get("requests", 100)))),
            "RATE_LIMIT_WINDOW": int(os.getenv("RATE_LIMIT_WINDOW", str(config.get("rate_limit", {}).get("window_seconds", 3600)))),
        })
        
        if self.logger:
            self.logger.log_metric("config", {"message": "Configuration loaded", "config_keys": list(config.keys())}, "INFO", "system")
        
        return config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "logging": {
                "log_level": "DEBUG",
                "log_interval": 1.0,
                "max_log_size": 10485760,
                "retention_days": 7,
                "log_file": "network_metrics.log"
            },
            "metrics": {
                "interfaces": True,
                "performance": True,
                "hardware": True,
                "latency": True,
                "throughput": True,
                "bytes_sent": True,
                "bytes_received": True,
                "packets_sent": True,
                "packets_received": True
            },
            "ping_host": "8.8.8.8",
            "update_interval": 1.0,
            "max_concurrent_requests": 100,
            "rate_limit": {
                "requests": 1000,
                "window_seconds": 3600
            },
            "security": {
                "enable_auth": False,
                "enable_cors": True,
                "enable_rate_limiting": False,
                "allowed_origins": ["*"]
            },
            "api_host": "127.0.0.1",
            "api_port": 8000,
            "max_history_points": 200,
            "SIMULATION_MODE": False,
            "CACHE_DURATION": 1.0,
            "STREAMING_INTERVAL": 2.0
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        """
        self.config[key] = value
        if self.logger:
            self.logger.log_metric("config", {"message": f"Configuration updated: {key} = {value}"}, "INFO", "system")
    
    def is_simulation_mode(self) -> bool:
        """
        Check if the application is running in simulation mode.
        """
        return self.config.get("SIMULATION_MODE", False)
    
    def get_cache_duration(self) -> float:
        """
        Get the cache duration for metrics.
        """
        return self.config.get("CACHE_DURATION", 1.0)
    
    def get_streaming_interval(self) -> float:
        """
        Get the streaming interval for WebSocket updates.
        """
        return self.config.get("STREAMING_INTERVAL", 2.0)
    
    def get_max_history_points(self) -> int:
        """
        Get the maximum number of history points to store.
        """
        return self.config.get("MAX_HISTORY_POINTS", 200)
