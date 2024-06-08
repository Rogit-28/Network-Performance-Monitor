import asyncio
import json
import threading
import time
import platform
import pythoncom
from collections import deque
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from .services import NetworkMonitorService
from .models import NetworkInterface, PerformanceMetric, HardwareInfo
from ..config_manager import ConfigManager


class ConnectionManager:
    """
    Manages WebSocket connections for real-time data streaming.
    """
    def __init__(self, max_history_points: int = 200):
        self.config_manager = ConfigManager()
        self.active_connections: List[WebSocket] = []
        self.service = NetworkMonitorService(cache_duration=self.config_manager.get_cache_duration())
        self.is_streaming = False
        self.streaming_thread = None
        
        # Time-series data storage for charting
        self.max_history_points = max_history_points
        self.historical_data = deque(maxlen=max_history_points)  # Circular buffer for historical data
        self.last_broadcast_time = None

    async def connect(self, websocket: WebSocket):
        """Add a new WebSocket connection."""
        await websocket.accept()
        if websocket not in self.active_connections:
            self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a personal message to a specific WebSocket."""
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        """Broadcast a message to all active WebSocket connections."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception:
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_with_historical_context(self, current_data: Dict[str, Any]):
        """Broadcast current data with historical context to all connections."""
        # Store the current data in historical buffer
        self._store_historical_data(current_data)
        
        # Create message with both current and historical data
        historical_data = self.get_historical_data(limit=50)  # Last 50 data points
        message_data = {
            "current_data": current_data,
            "historical_data": historical_data
        }
        message = json.dumps(message_data, default=str)
        
        await self.broadcast(message)

    async def _stream_data_async(self):
        """Async function to continuously collect and stream data."""
        cleanup_counter = 0
        cleanup_interval = 30  # Perform cleanup every 30 iterations (about every 60 seconds with 2s interval)
        
        while self.is_streaming:
            try:
                # Collect all metrics
                all_metrics = self.service.get_all_metrics()
                
                # Format the data for WebSocket transmission
                data = {
                    "timestamp": datetime.now().isoformat(),
                    "interfaces": [interface.__dict__ for interface in all_metrics["interfaces"]],
                    "performance_metrics": [metric.__dict__ for metric in all_metrics["performance_metrics"]],
                    "hardware_info": [hw.__dict__ for hw in all_metrics["hardware_info"]]
                }
                
                # Store data in historical buffer for charting
                self._store_historical_data(data)
                
                # Perform periodic cleanup to prevent memory overflow
                cleanup_counter += 1
                if cleanup_counter >= cleanup_interval:
                    self.cleanup_old_data()
                    cleanup_counter = 0 # Reset counter
                
                # Broadcast to all connected clients with historical context
                await self.broadcast_with_historical_context(data)
                
                # Wait before the next collection (adjust this value to control update frequency)
                await asyncio.sleep(self.config_manager.get_streaming_interval())
                
            except asyncio.CancelledError:
                break  # Exit the loop when cancelled
            except Exception as e:
                await asyncio.sleep(5)  # Wait longer before retrying if there's an error)
    
    def _store_historical_data(self, data: Dict[str, Any]):
        """Store data point in historical buffer for charting."""
        # Add the data point to the historical buffer
        self.historical_data.append(data)
        self.last_broadcast_time = datetime.now()
    
    def cleanup_old_data(self, max_age_minutes: int = 10):
        """Remove data points older than max_age_minutes to prevent memory overflow."""
        if not self.historical_data:
            return
            
        # Calculate the cutoff time
        cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
        
        # Filter out old data points - keep only recent ones
        # Since deque has a max length, this is mostly for extra safety
        filtered_data = []
        for data_point in self.historical_data:
            try:
                timestamp_str = data_point.get("timestamp", "")
                if timestamp_str:
                    data_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    if data_time >= cutoff_time:
                        filtered_data.append(data_point)
            except (ValueError, TypeError):
                # If timestamp parsing fails, keep the data point
                filtered_data.append(data_point)
        
        # Replace the historical data with filtered data
        # We need to create a new deque to maintain the max length
        self.historical_data = deque(filtered_data, maxlen=self.max_history_points)
    
    def get_historical_data(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get historical data for charting, optionally limited to a specific number of points."""
        if limit is None:
            limit = self.max_history_points
        
        # Convert deque to list and return the last 'limit' items
        data_list = list(self.historical_data)
        return data_list[-limit:] if len(data_list) > limit else data_list

    def start_streaming(self):
        """Start the background streaming task."""
        if not self.is_streaming:
            self.is_streaming = True
            # Create an asyncio task for the event loop
            try:
                loop = asyncio.get_running_loop()
                # If we're in an event loop, schedule the task
                self.streaming_task = loop.create_task(self._stream_data_async())
            except RuntimeError:
                # If no running loop, create a new thread with its own loop
                import threading
                
                def run_streaming():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(self._stream_data_async())
                    except asyncio.CancelledError:
                        pass  # Expected when cancelled during shutdown
                    finally:
                        loop.close()
                
                self.streaming_thread = threading.Thread(target=run_streaming, daemon=True)
                self.streaming_thread.start()

    async def stop_streaming(self):
        """Stop the background streaming."""
        self.is_streaming = False
        if hasattr(self, 'streaming_task'):
            self.streaming_task.cancel()
            try:
                # Wait for the task to finish cancellation
                await self.streaming_task
            except asyncio.CancelledError:
                pass  # Task was cancelled, which is expected
        if hasattr(self, 'streaming_thread') and self.streaming_thread is not None:
            self.streaming_thread.join(timeout=1.0)  # Wait up to 1 second for thread to finish

    async def _broadcast_async(self, data: Dict[str, Any]):
        """Async broadcast of data to all active connections."""
        json_data = json.dumps(data, default=str)  # default=str to handle datetime serialization
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json_data)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception:
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)


# Global connection manager instance
config_manager = ConfigManager()
manager = ConnectionManager(max_history_points=config_manager.get_max_history_points())  # Store up to configured number of data points for charting


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data streaming."""
    await manager.connect(websocket)
    try:
        # Send initial data with historical context when client connects
        all_metrics = manager.service.get_all_metrics()
        initial_data = {
            "timestamp": datetime.now().isoformat(),
            "interfaces": [interface.__dict__ for interface in all_metrics["interfaces"]],
            "performance_metrics": [metric.__dict__ for metric in all_metrics["performance_metrics"]],
            "hardware_info": [hw.__dict__ for hw in all_metrics["hardware_info"]]
        }
        
        # Include historical data for charting
        historical_data = manager.get_historical_data(limit=50)  # Send last 50 data points for initial charting
        
        # Combine current and historical data
        response_data = {
            "current_data": initial_data,
            "historical_data": historical_data
        }
        
        await manager.send_personal_message(json.dumps(response_data, default=str), websocket)
        
        # Keep the connection alive
        while True:
            try:
                # Listen for messages from client (could be used for control commands)
                data = await websocket.receive_text()
                # For now, just echo back if needed
                # await manager.send_personal_message(f"Echo: {data}", websocket)
            except WebSocketDisconnect:
                manager.disconnect(websocket)
                break
    except WebSocketDisconnect:
        manager.disconnect(websocket)
