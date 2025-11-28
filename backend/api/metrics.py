from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time
from typing import Dict, Any
from backend.config_manager import ConfigManager

router = APIRouter()

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total', 
    'Total HTTP requests', 
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds', 
    'HTTP request latency',
    ['endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections', 
    'Number of active connections'
)

API_CALLS = Counter(
    'api_calls_total',
    'Total API calls by endpoint',
    ['endpoint']
)

# Performance metrics
CPU_USAGE = Gauge('cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('memory_usage_percent', 'Memory usage percentage')
DISK_USAGE = Gauge('disk_usage_percent', 'Disk usage percentage')

class MetricsMiddleware:
    """Middleware to collect metrics for each request."""
    def __init__(self):
        self.active_requests = 0
    
    async def __call__(self, request, call_next):
        start_time = time.time()
        self.active_requests += 1
        ACTIVE_CONNECTIONS.set(self.active_requests)
        
        try:
            response = await call_next(request)
        finally:
            self.active_requests -= 1
            ACTIVE_CONNECTIONS.set(self.active_requests)
        
        # Record metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        REQUEST_LATENCY.labels(endpoint=request.url.path).observe(
            time.time() - start_time
        )
        
        API_CALLS.labels(endpoint=request.url.path).inc()
        
        return response

# Initialize metrics middleware
metrics_middleware = MetricsMiddleware()

@router.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    return PlainTextResponse(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@router.get("/metrics/health")
async def get_health_metrics():
    """Get health-related metrics."""
    import psutil
    
    health_metrics = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else 0,
        "active_connections": ACTIVE_CONNECTIONS._value.get(),
        "total_requests": REQUEST_COUNT._metrics.get(('GET', '/api/v1/metrics/health', '200'), type(REQUEST_COUNT(0)))._value.get() if REQUEST_COUNT._metrics else 0,
        "timestamp": time.time()
    }
    
    # Update gauges
    CPU_USAGE.set(health_metrics["cpu_percent"])
    MEMORY_USAGE.set(health_metrics["memory_percent"])
    DISK_USAGE.set(health_metrics["disk_percent"])
    
    return health_metrics

def setup_metrics(app):
    """Setup metrics collection for the FastAPI app."""
    # Add middleware to app
    app.middleware('http')(metrics_middleware.__call__)
    
    # Include metrics routes
    app.include_router(router, prefix="/api/v1", tags=["metrics"])
