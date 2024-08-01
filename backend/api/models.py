from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class NetworkInterface(BaseModel):
    name: str
    ipv4: Optional[str] = None
    ipv6: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    is_up: Optional[bool] = None
    is_running: Optional[bool] = None


class PerformanceMetric(BaseModel):
    interface: str
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    latency: Optional[float] = None
    throughput: Optional[float] = None
    timestamp: datetime


class HardwareInfo(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    connection_status: Optional[str] = None
    mac_address: Optional[str] = None
    max_link_speed: Optional[int] = None
    current_link_speed: Optional[int] = None
    driver_version: Optional[str] = None
    driver_date: Optional[str] = None
    driver_provider: Optional[str] = None


class LogEntry(BaseModel):
    log_id: str
    timestamp: str
    log_level: str
    metric_category: str
    metric_type: str
    data: Dict[str, Any]
    system_info: Dict[str, Any]
    session_id: str
    metadata: Dict[str, Any]


class NetworkMetricsResponse(BaseModel):
    interfaces: List[NetworkInterface]
    performance_metrics: List[PerformanceMetric]
    hardware_info: List[HardwareInfo]
    timestamp: datetime


class LogQueryParams(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    log_level: Optional[str] = None
    metric_type: Optional[str] = None
    search_term: Optional[str] = None
