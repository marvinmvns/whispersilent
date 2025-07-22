"""
Real-time Transcription API using WebSockets
Provides live transcription streaming to connected clients
"""

import asyncio
import json
import time
import threading
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, asdict
import websockets
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed, ConnectionClosedError
from logger import log
from config import Config

@dataclass
class TranscriptionEvent:
    """Real-time transcription event"""
    event_type: str  # "transcription", "speaker_change", "chunk_processed", "error", "heartbeat"
    timestamp: float
    data: Dict[str, Any]
    session_id: Optional[str] = None

@dataclass
class ClientConnection:
    """Client connection information"""
    websocket: WebSocketServerProtocol
    client_id: str
    connected_at: float
    last_heartbeat: float
    subscriptions: Set[str]  # Event types client is subscribed to
    metadata: Dict[str, Any]

class RealtimeTranscriptionAPI:
    """
    WebSocket-based real-time transcription API
    
    Features:
    - Live transcription streaming
    - Speaker identification events
    - Selective event subscriptions
    - Connection management
    - Heartbeat monitoring
    - Client metadata tracking
    """
    
    def __init__(self, pipeline=None):
        self.pipeline = pipeline
        self.enabled = Config.REALTIME_API.get("enabled", False)
        self.port = Config.REALTIME_API.get("websocket_port", 8081)
        self.max_connections = Config.REALTIME_API.get("max_connections", 50)
        self.buffer_size = Config.REALTIME_API.get("buffer_size", 100)
        self.heartbeat_interval = Config.REALTIME_API.get("heartbeat_interval", 30)
        
        # Connection management
        self.clients: Dict[str, ClientConnection] = {}
        self.event_buffer: List[TranscriptionEvent] = []
        self.lock = threading.Lock()
        
        # WebSocket server
        self.server = None
        self.server_task = None
        self.heartbeat_task = None
        self.running = False
        
        # Event loop for async operations
        self.loop = None
        self.loop_thread = None
        
        if self.enabled:
            log.info(f"RealtimeTranscriptionAPI initialized on port {self.port}")
        else:
            log.debug("RealtimeTranscriptionAPI disabled")
    
    def start(self):
        """Start the real-time WebSocket server"""
        if not self.enabled:
            log.debug("RealtimeAPI not enabled, skipping start")
            return
            
        if self.running:
            log.warning("RealtimeAPI already running")
            return
        
        self.running = True
        
        # Start event loop in separate thread
        self.loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.loop_thread.start()
        
        log.info(f"Real-time transcription WebSocket server started on port {self.port}")
    
    def stop(self):
        """Stop the WebSocket server"""
        if not self.running:
            return
            
        self.running = False
        
        if self.loop and self.loop.is_running():
            # Schedule shutdown in the event loop
            asyncio.run_coroutine_threadsafe(self._shutdown(), self.loop)
        
        if self.loop_thread and self.loop_thread.is_alive():
            self.loop_thread.join(timeout=5)
        
        log.info("Real-time transcription WebSocket server stopped")
    
    def _run_event_loop(self):
        """Run the asyncio event loop in a separate thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            # Start WebSocket server
            start_server = websockets.serve(
                self._handle_client_connection,
                "0.0.0.0",
                self.port,
                max_size=None,
                ping_interval=20,
                ping_timeout=10
            )
            
            self.server = self.loop.run_until_complete(start_server)
            
            # Start heartbeat task
            self.heartbeat_task = self.loop.create_task(self._heartbeat_monitor())
            
            # Run event loop
            self.loop.run_forever()
            
        except Exception as e:
            log.error(f"Error in WebSocket event loop: {e}")
        finally:
            if self.loop and not self.loop.is_closed():
                self.loop.close()
    
    async def _shutdown(self):
        """Gracefully shutdown the server"""
        # Cancel heartbeat task
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        
        # Close all client connections
        if self.clients:
            close_tasks = []
            for client in self.clients.values():
                close_tasks.append(client.websocket.close())
            if close_tasks:
                await asyncio.gather(*close_tasks, return_exceptions=True)
        
        # Stop server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        # Stop event loop
        self.loop.stop()
    
    async def _handle_client_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new client WebSocket connection"""
        client_id = f"client_{int(time.time() * 1000)}_{id(websocket)}"
        
        try:
            # Check connection limit
            if len(self.clients) >= self.max_connections:
                await websocket.send(json.dumps({
                    "event": "error",
                    "message": "Maximum connections exceeded",
                    "timestamp": time.time()
                }))
                await websocket.close(code=1008, reason="Connection limit exceeded")
                return
            
            # Create client connection
            client = ClientConnection(
                websocket=websocket,
                client_id=client_id,
                connected_at=time.time(),
                last_heartbeat=time.time(),
                subscriptions={"transcription", "speaker_change"},  # Default subscriptions
                metadata={}
            )
            
            with self.lock:
                self.clients[client_id] = client
            
            log.info(f"New WebSocket client connected: {client_id} from {websocket.remote_address}")
            
            # Send welcome message
            await websocket.send(json.dumps({
                "event": "connected",
                "client_id": client_id,
                "timestamp": time.time(),
                "available_events": ["transcription", "speaker_change", "chunk_processed", "error", "heartbeat"],
                "buffer_size": len(self.event_buffer)
            }))
            
            # Send recent events from buffer
            await self._send_buffered_events(client)
            
            # Handle client messages
            async for message in websocket:
                await self._handle_client_message(client, message)
                
        except ConnectionClosed:
            log.debug(f"Client {client_id} disconnected normally")
        except ConnectionClosedError as e:
            log.debug(f"Client {client_id} connection closed with error: {e}")
        except Exception as e:
            log.error(f"Error handling client {client_id}: {e}")
        finally:
            # Clean up client
            with self.lock:
                if client_id in self.clients:
                    del self.clients[client_id]
            
            log.info(f"Client {client_id} disconnected, {len(self.clients)} clients remaining")
    
    async def _handle_client_message(self, client: ClientConnection, message: str):
        """Handle incoming message from client"""
        try:
            data = json.loads(message)
            action = data.get("action")
            
            if action == "subscribe":
                # Subscribe to specific event types
                events = data.get("events", [])
                client.subscriptions.update(events)
                await client.websocket.send(json.dumps({
                    "event": "subscription_updated",
                    "subscriptions": list(client.subscriptions),
                    "timestamp": time.time()
                }))
                
            elif action == "unsubscribe":
                # Unsubscribe from event types
                events = data.get("events", [])
                client.subscriptions.difference_update(events)
                await client.websocket.send(json.dumps({
                    "event": "subscription_updated",
                    "subscriptions": list(client.subscriptions),
                    "timestamp": time.time()
                }))
                
            elif action == "ping":
                # Heartbeat/ping response
                client.last_heartbeat = time.time()
                await client.websocket.send(json.dumps({
                    "event": "pong",
                    "timestamp": time.time()
                }))
                
            elif action == "get_buffer":
                # Request recent events
                await self._send_buffered_events(client)
                
            elif action == "set_metadata":
                # Update client metadata
                client.metadata.update(data.get("metadata", {}))
                
            else:
                await client.websocket.send(json.dumps({
                    "event": "error",
                    "message": f"Unknown action: {action}",
                    "timestamp": time.time()
                }))
                
        except json.JSONDecodeError:
            await client.websocket.send(json.dumps({
                "event": "error",
                "message": "Invalid JSON message",
                "timestamp": time.time()
            }))
        except Exception as e:
            log.error(f"Error handling message from {client.client_id}: {e}")
            await client.websocket.send(json.dumps({
                "event": "error",
                "message": f"Message handling error: {str(e)}",
                "timestamp": time.time()
            }))
    
    async def _send_buffered_events(self, client: ClientConnection):
        """Send recent events from buffer to client"""
        with self.lock:
            events_to_send = [
                event for event in self.event_buffer
                if event.event_type in client.subscriptions
            ]
        
        for event in events_to_send:
            try:
                await client.websocket.send(json.dumps(asdict(event)))
            except Exception as e:
                log.error(f"Error sending buffered event to {client.client_id}: {e}")
                break
    
    async def _heartbeat_monitor(self):
        """Monitor client connections and send heartbeats"""
        while self.running:
            try:
                current_time = time.time()
                disconnected_clients = []
                
                with self.lock:
                    clients_copy = list(self.clients.items())
                
                for client_id, client in clients_copy:
                    try:
                        # Check if client is still responsive
                        if current_time - client.last_heartbeat > self.heartbeat_interval * 2:
                            log.warning(f"Client {client_id} unresponsive, removing")
                            disconnected_clients.append(client_id)
                            continue
                        
                        # Send heartbeat if client subscribed
                        if "heartbeat" in client.subscriptions:
                            await client.websocket.send(json.dumps({
                                "event": "heartbeat",
                                "timestamp": current_time,
                                "server_uptime": current_time - (self.pipeline.health_monitor.start_time if self.pipeline else current_time),
                                "connected_clients": len(self.clients)
                            }))
                            
                    except Exception as e:
                        log.error(f"Error in heartbeat for client {client_id}: {e}")
                        disconnected_clients.append(client_id)
                
                # Remove disconnected clients
                with self.lock:
                    for client_id in disconnected_clients:
                        if client_id in self.clients:
                            del self.clients[client_id]
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"Error in heartbeat monitor: {e}")
                await asyncio.sleep(5)
    
    def broadcast_transcription(self, transcription_text: str, metadata: Dict[str, Any] = None):
        """Broadcast new transcription to all connected clients"""
        if not self.enabled or not self.running:
            return
        
        event = TranscriptionEvent(
            event_type="transcription",
            timestamp=time.time(),
            data={
                "text": transcription_text,
                "metadata": metadata or {},
                "client_count": len(self.clients)
            }
        )
        
        self._add_to_buffer_and_broadcast(event)
    
    def broadcast_speaker_change(self, speaker_id: str, confidence: float, metadata: Dict[str, Any] = None):
        """Broadcast speaker change event"""
        if not self.enabled or not self.running:
            return
        
        event = TranscriptionEvent(
            event_type="speaker_change",
            timestamp=time.time(),
            data={
                "speaker_id": speaker_id,
                "confidence": confidence,
                "metadata": metadata or {}
            }
        )
        
        self._add_to_buffer_and_broadcast(event)
    
    def broadcast_chunk_processed(self, chunk_info: Dict[str, Any]):
        """Broadcast audio chunk processing event"""
        if not self.enabled or not self.running:
            return
        
        event = TranscriptionEvent(
            event_type="chunk_processed",
            timestamp=time.time(),
            data=chunk_info
        )
        
        self._add_to_buffer_and_broadcast(event)
    
    def broadcast_error(self, error_message: str, error_type: str = "general"):
        """Broadcast error event"""
        if not self.enabled or not self.running:
            return
        
        event = TranscriptionEvent(
            event_type="error",
            timestamp=time.time(),
            data={
                "message": error_message,
                "error_type": error_type
            }
        )
        
        self._add_to_buffer_and_broadcast(event)
    
    def _add_to_buffer_and_broadcast(self, event: TranscriptionEvent):
        """Add event to buffer and broadcast to clients"""
        # Add to buffer
        with self.lock:
            self.event_buffer.append(event)
            # Keep buffer size limited
            if len(self.event_buffer) > self.buffer_size:
                self.event_buffer = self.event_buffer[-self.buffer_size:]
        
        # Broadcast to clients
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._broadcast_event(event), self.loop)
    
    async def _broadcast_event(self, event: TranscriptionEvent):
        """Broadcast event to all subscribed clients"""
        if not self.clients:
            return
        
        event_data = asdict(event)
        message = json.dumps(event_data)
        
        # Get clients subscribed to this event type
        subscribed_clients = []
        with self.lock:
            for client in self.clients.values():
                if event.event_type in client.subscriptions:
                    subscribed_clients.append(client)
        
        # Send to subscribed clients
        for client in subscribed_clients:
            try:
                await client.websocket.send(message)
            except Exception as e:
                log.error(f"Error broadcasting to client {client.client_id}: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get real-time API status"""
        with self.lock:
            client_info = []
            for client in self.clients.values():
                client_info.append({
                    "client_id": client.client_id,
                    "connected_at": client.connected_at,
                    "last_heartbeat": client.last_heartbeat,
                    "subscriptions": list(client.subscriptions),
                    "metadata": client.metadata
                })
        
        return {
            "enabled": self.enabled,
            "running": self.running,
            "port": self.port,
            "connected_clients": len(self.clients),
            "max_connections": self.max_connections,
            "buffer_size": len(self.event_buffer),
            "max_buffer_size": self.buffer_size,
            "heartbeat_interval": self.heartbeat_interval,
            "clients": client_info
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get real-time API statistics"""
        with self.lock:
            event_types = {}
            for event in self.event_buffer:
                event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
        
        return {
            "total_events_buffered": len(self.event_buffer),
            "event_type_counts": event_types,
            "current_connections": len(self.clients),
            "average_events_per_client": len(self.event_buffer) / max(len(self.clients), 1)
        }