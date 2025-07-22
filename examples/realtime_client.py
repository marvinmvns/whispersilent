#!/usr/bin/env python3
"""
Real-time Transcription WebSocket Client Example
Connects to WhisperSilent real-time API and displays live transcriptions
"""

import asyncio
import json
import time
import argparse
import signal
import sys
from typing import Set
import websockets
from websockets.exceptions import ConnectionClosed, ConnectionClosedError

class RealtimeTranscriptionClient:
    """
    WebSocket client for real-time transcription streaming
    """
    
    def __init__(self, server_url: str = "ws://localhost:8081"):
        self.server_url = server_url
        self.websocket = None
        self.running = False
        self.subscriptions: Set[str] = {"transcription", "speaker_change"}
        self.client_id = None
        
    async def connect(self):
        """Connect to the WebSocket server"""
        try:
            print(f"🔌 Connecting to {self.server_url}...")
            self.websocket = await websockets.connect(
                self.server_url,
                ping_interval=20,
                ping_timeout=10
            )
            self.running = True
            print("✅ Connected successfully!")
            
            # Handle incoming messages
            await self._handle_messages()
            
        except ConnectionRefusedError:
            print(f"❌ Connection refused. Is the server running on {self.server_url}?")
        except Exception as e:
            print(f"❌ Connection error: {e}")
    
    async def _handle_messages(self):
        """Handle incoming WebSocket messages"""
        try:
            async for message in self.websocket:
                await self._process_message(message)
        except ConnectionClosed:
            print("🔌 Connection closed by server")
        except ConnectionClosedError as e:
            print(f"🔌 Connection lost: {e}")
        except Exception as e:
            print(f"❌ Error handling messages: {e}")
        finally:
            self.running = False
    
    async def _process_message(self, message: str):
        """Process incoming message from server"""
        try:
            data = json.loads(message)
            event = data.get("event", data.get("event_type"))
            timestamp = data.get("timestamp", time.time())
            
            # Format timestamp
            time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
            
            if event == "connected":
                self.client_id = data.get("client_id")
                available_events = data.get("available_events", [])
                buffer_size = data.get("buffer_size", 0)
                
                print(f"🎉 Connected as {self.client_id}")
                print(f"📊 Buffer contains {buffer_size} recent events")
                print(f"📡 Available events: {', '.join(available_events)}")
                
                # Subscribe to desired events
                await self._subscribe_to_events()
                
            elif event == "transcription":
                text = data.get("data", {}).get("text", "")
                metadata = data.get("data", {}).get("metadata", {})
                
                # Display transcription with formatting
                print(f"\n📝 [{time_str}] Transcription:")
                print(f"    {text}")
                
                if metadata:
                    if "processing_time_ms" in metadata:
                        print(f"    ⏱️  Processing: {metadata['processing_time_ms']:.0f}ms")
                    if "confidence" in metadata:
                        print(f"    🎯 Confidence: {metadata['confidence']:.1%}")
                
            elif event == "speaker_change":
                speaker_id = data.get("data", {}).get("speaker_id", "Unknown")
                confidence = data.get("data", {}).get("confidence", 0)
                
                print(f"🎭 [{time_str}] Speaker: {speaker_id} (confidence: {confidence:.1%})")
                
            elif event == "chunk_processed":
                chunk_data = data.get("data", {})
                chunk_size = chunk_data.get("size", 0)
                duration = chunk_data.get("duration_seconds", 0)
                
                print(f"🔊 [{time_str}] Audio chunk: {chunk_size} samples ({duration:.2f}s)")
                
            elif event == "heartbeat":
                server_uptime = data.get("server_uptime", 0)
                connected_clients = data.get("connected_clients", 0)
                
                print(f"💓 [{time_str}] Heartbeat - Uptime: {server_uptime:.0f}s, Clients: {connected_clients}")
                
            elif event == "error":
                error_msg = data.get("data", {}).get("message", data.get("message", "Unknown error"))
                print(f"❌ [{time_str}] Error: {error_msg}")
                
            elif event == "subscription_updated":
                subs = data.get("subscriptions", [])
                print(f"📡 [{time_str}] Subscriptions updated: {', '.join(subs)}")
                
            elif event == "pong":
                print(f"🏓 [{time_str}] Pong received")
                
            else:
                print(f"🔍 [{time_str}] Unknown event: {event}")
                print(f"    Data: {json.dumps(data, indent=2)}")
                
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON received: {message}")
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    async def _subscribe_to_events(self):
        """Subscribe to desired event types"""
        if self.websocket:
            subscribe_msg = {
                "action": "subscribe",
                "events": list(self.subscriptions)
            }
            await self.websocket.send(json.dumps(subscribe_msg))
    
    async def send_ping(self):
        """Send ping to server"""
        if self.websocket and self.running:
            ping_msg = {
                "action": "ping",
                "timestamp": time.time()
            }
            await self.websocket.send(json.dumps(ping_msg))
            print("🏓 Ping sent")
    
    async def get_buffer(self):
        """Request recent events from buffer"""
        if self.websocket and self.running:
            buffer_msg = {
                "action": "get_buffer"
            }
            await self.websocket.send(json.dumps(buffer_msg))
            print("📥 Requested recent events")
    
    async def update_subscriptions(self, events_to_add: Set[str] = None, events_to_remove: Set[str] = None):
        """Update event subscriptions"""
        if not self.websocket or not self.running:
            return
        
        if events_to_add:
            subscribe_msg = {
                "action": "subscribe",
                "events": list(events_to_add)
            }
            await self.websocket.send(json.dumps(subscribe_msg))
            self.subscriptions.update(events_to_add)
        
        if events_to_remove:
            unsubscribe_msg = {
                "action": "unsubscribe", 
                "events": list(events_to_remove)
            }
            await self.websocket.send(json.dumps(unsubscribe_msg))
            self.subscriptions.difference_update(events_to_remove)
    
    async def disconnect(self):
        """Disconnect from server"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            print("🔌 Disconnected from server")

async def interactive_client(server_url: str):
    """Interactive client with command support"""
    client = RealtimeTranscriptionClient(server_url)
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\\n⚡ Received interrupt signal, disconnecting...")
        asyncio.create_task(client.disconnect())
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🎤 Real-time Transcription Client")
    print("="*50)
    print("Commands:")
    print("  ping     - Send ping to server")
    print("  buffer   - Request recent events")
    print("  sub      - Subscribe to events (e.g., sub heartbeat)")
    print("  unsub    - Unsubscribe from events (e.g., unsub heartbeat)")
    print("  quit     - Disconnect and exit")
    print("="*50)
    
    # Start connection task
    connection_task = asyncio.create_task(client.connect())
    
    # Command input loop
    while client.running:
        try:
            # Non-blocking input (simplified for demo)
            await asyncio.sleep(0.1)
            
            # In a real implementation, you'd use aioconsole for async input
            # For now, this is a simple connection that listens for events
            
        except KeyboardInterrupt:
            break
    
    await client.disconnect()
    
    # Cancel connection task
    if not connection_task.done():
        connection_task.cancel()

def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(description="Real-time Transcription WebSocket Client")
    parser.add_argument(
        "--server", "-s",
        default="ws://localhost:8081",
        help="WebSocket server URL (default: ws://localhost:8081)"
    )
    parser.add_argument(
        "--events", "-e",
        nargs="+",
        default=["transcription", "speaker_change"],
        help="Event types to subscribe to"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    print(f"🎤 WhisperSilent Real-time Client")
    print(f"📡 Server: {args.server}")
    print(f"📋 Events: {', '.join(args.events)}")
    print()
    
    # Run the client
    try:
        asyncio.run(interactive_client(args.server))
    except KeyboardInterrupt:
        print("\\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Client error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()