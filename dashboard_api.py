"""
Sakudoko Dashboard API Server
FastAPI backend with WebSocket support for real-time logs
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import json
from datetime import datetime, timedelta
from typing import List
import random

app = FastAPI(title="Sakudoko Dashboard API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
class BotState:
    def __init__(self):
        self.servers = 1234
        self.users = 52000
        self.start_time = datetime.now() - timedelta(days=12, hours=5, minutes=23)
        self.is_online = True
        self.latency = 24
        self.logs = []
        self.websocket_clients: List[WebSocket] = []
        
    def get_uptime(self):
        """Calculate uptime from start_time"""
        delta = datetime.now() - self.start_time
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        return f"{days}d {hours}h {minutes}m"
    
    def add_log(self, log_type: str, message: str):
        """Add a new log entry"""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        log_entry = {
            "time": timestamp,
            "type": log_type,
            "message": message
        }
        self.logs.append(log_entry)
        # Keep only last 50 logs
        if len(self.logs) > 50:
            self.logs.pop(0)
        return log_entry

bot_state = BotState()

# Initialize with some sample logs
bot_state.add_log("INFO", "System initialized...")
bot_state.add_log("INFO", "Connected to Discord Gateway.")
bot_state.add_log("PLAY", 'Requested "Bling-Bang-Bang-Born" in Server #402')
bot_state.add_log("INFO", f"Latency stable at {bot_state.latency}ms.")


# REST API Endpoints

@app.get("/")
async def read_root():
    """Serve the main HTML page"""
    return FileResponse("index.html")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "online" if bot_state.is_online else "offline",
        "latency": bot_state.latency,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/stats")
async def get_stats():
    """Get bot statistics"""
    return {
        "servers": bot_state.servers,
        "users": bot_state.users,
        "uptime": bot_state.get_uptime(),
        "uptime_raw": {
            "days": (datetime.now() - bot_state.start_time).days,
            "total_seconds": (datetime.now() - bot_state.start_time).total_seconds()
        }
    }


@app.get("/api/logs")
async def get_logs(limit: int = 20):
    """Get recent logs"""
    return {
        "logs": bot_state.logs[-limit:],
        "total": len(bot_state.logs)
    }


@app.get("/api/commands")
async def get_commands():
    """Get available bot commands"""
    return {
        "commands": [
            {"name": "/play", "description": "Play music from URL"},
            {"name": "/skip", "description": "Skip current song"},
            {"name": "/queue", "description": "Show music queue"},
            {"name": "/stop", "description": "Stop & clear queue"},
            {"name": "/filter", "description": "Bassboost / Nightcore"},
            {"name": "/pause", "description": "Pause current song"},
            {"name": "/resume", "description": "Resume playback"},
            {"name": "/volume", "description": "Adjust volume"},
        ]
    }


# WebSocket for real-time logs
@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for real-time log streaming"""
    await websocket.accept()
    bot_state.websocket_clients.append(websocket)
    
    try:
        # Send initial logs
        await websocket.send_json({
            "type": "initial",
            "logs": bot_state.logs[-10:]
        })
        
        # Keep connection alive
        while True:
            # Wait for any message from client (ping/pong)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send keepalive
                await websocket.send_json({"type": "keepalive"})
                
    except WebSocketDisconnect:
        bot_state.websocket_clients.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in bot_state.websocket_clients:
            bot_state.websocket_clients.remove(websocket)


async def broadcast_log(log_entry: dict):
    """Broadcast new log to all connected WebSocket clients"""
    disconnected = []
    for client in bot_state.websocket_clients:
        try:
            await client.send_json({
                "type": "new_log",
                "log": log_entry
            })
        except:
            disconnected.append(client)
    
    # Remove disconnected clients
    for client in disconnected:
        bot_state.websocket_clients.remove(client)


# Background task to simulate bot activity
@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(simulate_bot_activity())


async def simulate_bot_activity():
    """Simulate bot activity with random logs"""
    await asyncio.sleep(5)  # Wait for server to fully start
    
    sample_activities = [
        ("INFO", "Voice channel joined in Server #{}"),
        ("PLAY", 'Now playing "{}" in Server #{}'),
        ("INFO", "User {} requested a song"),
        ("INFO", "Queue updated: {} songs pending"),
        ("PLAY", 'Added "{}" to queue'),
        ("INFO", "Latency check: {}ms"),
        ("INFO", "Server #{} connected"),
    ]
    
    songs = [
        "Bling-Bang-Bang-Born",
        "IDOL - YOASOBI",
        "Gurenge - LiSA",
        "Unravel - TK",
        "Blue Bird - Ikimono Gakari",
        "Silhouette - KANA-BOON",
        "Racing Into The Night - YOASOBI",
    ]
    
    while True:
        await asyncio.sleep(random.randint(8, 20))
        
        # Randomly update stats
        if random.random() < 0.3:
            bot_state.servers += random.randint(-2, 5)
            bot_state.users += random.randint(-50, 200)
            bot_state.latency = random.randint(20, 35)
        
        # Generate random log
        log_type, message_template = random.choice(sample_activities)
        
        if "{}" in message_template:
            if "song" in message_template.lower() or "playing" in message_template.lower():
                message = message_template.format(random.choice(songs), random.randint(100, 999))
            elif "latency" in message_template.lower():
                message = message_template.format(bot_state.latency)
            elif "queue" in message_template.lower():
                message = message_template.format(random.randint(1, 10))
            elif "user" in message_template.lower():
                message = message_template.format(f"User#{random.randint(1000, 9999)}")
            else:
                message = message_template.format(random.randint(100, 999))
        else:
            message = message_template
        
        log_entry = bot_state.add_log(log_type, message)
        
        # Broadcast to WebSocket clients
        await broadcast_log(log_entry)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
