from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocket

from backend.api.routes import router
from backend.api.services import NetworkMonitorService
from backend.api.background_tasks import initialize_background_manager
from backend.api.websocket_handler import manager, websocket_endpoint
from backend.config_manager import ConfigManager

app = FastAPI(
    title="Network Performance Monitor API",
    description="API for network performance monitoring data",
    version="1.0.0"
)

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the service and background tasks
config_manager = ConfigManager()
service = NetworkMonitorService(cache_duration=config_manager.get_cache_duration())
initialize_background_manager(service, refresh_interval=config_manager.get_cache_duration())

# Include the API routes
app.include_router(router, prefix="/api/v1", tags=["network-monitor"])

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
