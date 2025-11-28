from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocket

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.api.routes import router
from backend.api.services import NetworkMonitorService
from backend.api.background_tasks import initialize_background_manager
from backend.api.websocket_handler import manager, websocket_endpoint
from backend.config_manager import ConfigManager
from backend.api.metrics import setup_metrics

# Initialize configuration manager
config_manager = ConfigManager()
rate_limit_enabled = config_manager.get("RATE_LIMIT_ENABLED", False)

# Initialize rate limiter if enabled
if rate_limit_enabled:
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[f"{config_manager.get('RATE_LIMIT_REQUESTS', 1000)}/{config_manager.get('RATE_LIMIT_WINDOW', 3600)}s"]
    )
else:
    # Create a mock limiter that doesn't actually limit
    class MockLimiter:
        def __call__(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
    
    limiter = MockLimiter()

app = FastAPI(
    title="Network Performance Monitor API",
    description="API for network performance monitoring data",
    version="1.0.0"
)

# Add rate limiting middleware if enabled
if rate_limit_enabled:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=config_manager.get("ALLOWED_ORIGINS", ["http://localhost:3000", "http://127.0.0.1:3000"]),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize the service and background tasks
service = NetworkMonitorService(cache_duration=config_manager.get_cache_duration())
initialize_background_manager(service, refresh_interval=config_manager.get_cache_duration())

# Include the API routes
app.include_router(router, prefix="/api/v1", tags=["network-monitor"])

# Setup metrics collection
setup_metrics(app)

# Add startup event to start WebSocket streaming when the app starts
@app.on_event("startup")
async def startup_event():
    manager.start_streaming()

# Add shutdown event to stop WebSocket streaming when the app shuts down
@app.on_event("shutdown")
async def shutdown_event():
    await manager.stop_streaming()

# Add WebSocket endpoint for real-time data streaming
@app.websocket("/ws")
async def websocket_endpoint_wrapper(websocket: WebSocket):
    await websocket_endpoint(websocket)

@app.get("/")
def read_root():
    return {"message": "Network Performance Monitor API", "docs": "/docs"}


# Add error handling middleware
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for the application."""
    from fastapi.responses import JSONResponse
    import logging
    
    logging.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handler for internal server errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An internal error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
