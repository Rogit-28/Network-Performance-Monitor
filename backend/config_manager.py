import os
from typing import Dict, Any, Optional
from backend.comprehensive_logger.comprehensive_logger import ComprehensiveLogger


class ConfigManager:
    """
    Manages application configuration and settings.
    """
    
    def __init__(self, logger: Optional[ComprehensiveLogger] = None):
        self.logger = logger
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from environment variables or config file.
        """
        config = {
            # Default configuration values
            "SIMULATION_MODE": os.getenv("SIMULATION_MODE", "false").lower() == "true",
            "CACHE_DURATION": float(os.getenv("CACHE_DURATION", "1.0")),
            "STREAMING_INTERVAL": float(os.getenv("STREAMING_INTERVAL", "2.0")),
            "MAX_HISTORY_POINTS": int(os.getenv("MAX_HISTORY_POINTS", "200")),
            "API_HOST": os.getenv("API_HOST", "127.0.0.1"),
            "API_PORT": int(os.getenv("API_PORT", "8000")),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
            "ENABLE_CORS": os.getenv("ENABLE_CORS", "true").lower() == "true",
            "ALLOWED_ORIGINS": os.getenv("ALLOWED_ORIGINS", "*").split(","),
        }
        
        if self.logger:
            self.logger.log_metric("config", {"message": "Configuration loaded", "config": config}, "INFO", "system")
        
        return config
    
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
