import asyncio
import discord
import os
import logging
import json
from threading import Thread
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from discord.ext import commands
from typing import Dict, Optional, List
from dotenv import load_dotenv
from datetime import datetime, timedelta

# --- 1. Dashboard API & Health Check Server ---
app = FastAPI(title="Sakudoko Bot Dashboard API", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state for bot and dashboard
class BotState:
    def __init__(self):
        self.bot = None
        self.start_time = datetime.now()
        self.is_online = False
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
        
        # Broadcast to WebSocket clients (only if event loop is running)
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self.broadcast_log(log_entry))
        except RuntimeError:
            # Event loop not running yet, skip broadcasting
            pass
        return log_entry
    
    async def broadcast_log(self, log_entry: dict):
        """Broadcast new log to all connected WebSocket clients"""
        disconnected = []
        for client in self.websocket_clients:
            try:
                await client.send_json({
                    "type": "new_log",
                    "log": log_entry
                })
            except:
                disconnected.append(client)
        
        # Remove disconnected clients
        for client in disconnected:
            self.websocket_clients.remove(client)

bot_state = BotState()

# Mount static files (assets folder)
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Dashboard API Endpoints

@app.get("/")
async def read_root():
    """Serve the main HTML page"""
    return FileResponse("index.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/health")
async def health_check_simple():
    """Simple health check for Azure"""
    return {"status": "ok"}

@app.get("/api/health")
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "online" if bot_state.is_online else "offline",
        "latency": round(bot_state.bot.latency * 1000) if bot_state.bot else 0,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/stats")
async def get_stats():
    """Get bot statistics"""
    if not bot_state.bot:
        return {"servers": 0, "users": 0, "uptime": "0d 0h 0m"}
    
    servers = len(bot_state.bot.guilds)
    users = sum(guild.member_count for guild in bot_state.bot.guilds)
    
    return {
        "servers": servers,
        "users": users,
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
            {"name": "/join", "description": "ให้บอทเข้าห้องเสียงและสร้างห้องแชทเพลง"},
            {"name": "/leave", "description": "ให้บอทออกจากห้องเสียงและลบห้องแชทเพลง"},
            {"name": "/queue", "description": "แสดงคิวเพลงปัจจุบัน"},
            {"name": "/remove", "description": "ลบเพลงออกจากคิว"},
            {"name": "/shuffle", "description": "สุ่มลำดับเพลงในคิว"},
            {"name": "/loop", "description": "เปิด/ปิดการเล่นซ้ำคิวเพลง"},
            {"name": "/autoplay", "description": "เปิด/ปิดโหมดเล่นเพลงอัตโนมัติ"},
            {"name": "/filter", "description": "ตั้งค่า filter/effect (bass, nightcore, pitch)"},
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
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "keepalive"})
                
    except WebSocketDisconnect:
        bot_state.websocket_clients.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in bot_state.websocket_clients:
            bot_state.websocket_clients.remove(websocket)

def run_dashboard_server():
    """Run FastAPI dashboard server"""
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="error")

Thread(target=run_dashboard_server, daemon=True).start()

# --- 2. Configuration and Logging ---
load_dotenv()
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

from logging.handlers import RotatingFileHandler

# Setup logging with rotation
log_handler = RotatingFileHandler(
    'bot.log',
    maxBytes=5*1024*1024,  # 5MB
    backupCount=5,
    encoding='utf-8'
)
log_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
    handlers=[log_handler, logging.StreamHandler()]
)
logger = logging.getLogger('discord_bot')

# Custom logging handler to send logs to dashboard
class DashboardLogHandler(logging.Handler):
    def emit(self, record):
        try:
            log_type = "INFO" if record.levelname == "INFO" else "ERROR"
            message = self.format(record)
            # Remove timestamp from message as it's added by bot_state.add_log
            message = message.split('] ', 1)[-1] if '] ' in message else message
            bot_state.add_log(log_type, message)
        except:
            pass

dashboard_handler = DashboardLogHandler()
dashboard_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(dashboard_handler)

# --- 3. Bot Utilities ---
async def notify_admin(bot: commands.Bot, message: str):
    """Send DM to admin when a critical error occurs."""
    if ADMIN_USER_ID:
        try:
            user = await bot.fetch_user(ADMIN_USER_ID)
            await user.send(f"[CRITICAL ERROR]\n{message}")
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")

# --- 4. Bot Definition ---
from music_manager import MusicManager
from database import Database

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents)
        self.managers: Dict[int, MusicManager] = {}
        self.user_last_request: Dict[int, float] = {}
        self.db = Database()  # Initialize database

    def get_manager(self, guild_id: int) -> MusicManager:
        """Retrieves or creates a MusicManager instance for a guild."""
        if guild_id not in self.managers:
            self.managers[guild_id] = MusicManager(self, guild_id)
        return self.managers[guild_id]

    def is_admin(self, member: discord.Member) -> bool:
        """Checks if a member has administrator permissions."""
        return member.guild_permissions.administrator

    async def setup_hook(self):
        """Load cogs and sync slash commands."""
        try:
            await self.load_extension('basic')
            logger.info("Loaded basic Cog.")
            await self.load_extension('music_cog')
            logger.info("Loaded music_cog Cog.")
        except commands.ExtensionAlreadyLoaded:
            logger.info("Extensions already loaded, skipping...")
        except Exception as e:
            logger.error(f"Failed to load extensions: {e}", exc_info=True)
            raise
        
        # Sync all slash commands globally
        await self.tree.sync()
        logger.info("Slash commands synced in setup_hook.")

bot = MyBot()
bot_state.bot = bot

# --- 5. Event Handlers ---

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user}')
    bot_state.add_log("INFO", f"Bot logged in as {bot.user}")
    activity = discord.Activity(
        type=discord.ActivityType.listening,
        name="/help | Sakudoko Music"
    )
    await bot.change_presence(status=discord.Status.online, activity=activity)
    bot_state.is_online = True
    bot_state.add_log("INFO", "Bot is now ONLINE")
    
    try:
        if ADMIN_USER_ID:
            user = await bot.fetch_user(ADMIN_USER_ID)
            await user.send(f"[BOT STATUS] ✅ Bot is ONLINE as {bot.user}")
    except Exception as e:
        logger.error(f"Failed to notify admin on_ready: {e}")

@bot.event
async def on_guild_join(guild: discord.Guild):
    try:
        logger.info(f"Bot invited to server: {guild.name} (ID: {guild.id})")
        bot_state.add_log("INFO", f"Joined server: {guild.name}")
        bot.get_manager(guild.id) # Initialize manager
        await bot.tree.sync(guild=guild)
        logger.info(f"Slash commands synced for guild {guild.id}")
    except Exception as e:
        logger.error(f"Exception in on_guild_join: {e}")

@bot.event
async def on_message(message: discord.Message):
    try:
        if message.author.bot or not message.guild:
            return

        manager = bot.get_manager(message.guild.id)

        # Anti-spam cooldown
        now = asyncio.get_event_loop().time()
        last = bot.user_last_request.get(message.author.id, 0)
        if now - last < 2:
            try: await message.delete()
            except Exception: pass
            return
        bot.user_last_request[message.author.id] = now

        # Music Room Logic
        if manager.music_channel_id == message.channel.id:
            manager.last_activity_time = now
            content = message.content.strip()
            
            # Permission Check - ต้องอยู่ในห้องเสียงเดียวกับบอท
            if not message.author.voice or not message.author.voice.channel:
                embed = discord.Embed(title="Error", description="❌ คุณต้องอยู่ในห้องเสียงก่อน!", color=0xff0000)
                await message.channel.send(embed=embed, delete_after=5)
                try: await message.delete()
                except Exception: pass
                return
            
            # ตรวจสอบว่าอยู่ห้องเดียวกับบอทหรือไม่
            vc = message.guild.voice_client
            if vc and vc.channel and message.author.voice.channel.id != vc.channel.id:
                embed = discord.Embed(title="Error", description="❌ คุณต้องอยู่ในห้องเสียงเดียวกับบอท!", color=0xff0000)
                await message.channel.send(embed=embed, delete_after=5)
                try: await message.delete()
                except Exception: pass
                return

            # Connect/Move bot
            channel = message.author.voice.channel
            if message.guild.voice_client is None:
                await channel.connect()
                bot_state.add_log("INFO", f"Connected to voice channel in {message.guild.name}")
            elif message.guild.voice_client.channel != channel:
                await message.guild.voice_client.move_to(channel)

            await manager.handle_music_request(message, content)
            
            try: await message.delete()
            except Exception: pass
            return

        await bot.process_commands(message) # For prefix commands like !ping
    except Exception as e:
        logger.error(f"Exception in on_message: {e}")
        await notify_admin(bot, str(e))

@bot.event
async def on_error(event_method, *args, **kwargs):
    import traceback
    err_msg = f"Exception in event: {event_method}\n{traceback.format_exc()}"
    logger.error(err_msg)
    await notify_admin(bot, err_msg)

@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    # Check if the bot itself is the one whose voice state changed
    if member.id == bot.user.id:
        guild_id = member.guild.id
        manager = bot.get_manager(guild_id)
        # Delegate the handling to the manager
        await manager.handle_voice_state_update(member, before, after)

@bot.event
async def on_disconnect():
    bot_state.is_online = False
    logger.warning("Bot is OFFLINE (disconnected)")
    bot_state.add_log("ERROR", "Bot disconnected")
    try:
        if ADMIN_USER_ID:
            user = await bot.fetch_user(ADMIN_USER_ID)
            await user.send("[BOT STATUS] ❌ Bot is OFFLINE (disconnected)")
    except Exception as e:
        logger.error(f"Failed to notify admin on_disconnect: {e}")

@bot.event
async def on_resumed():
    """Called when the bot resumes a session"""
    bot_state.is_online = True
    logger.info("Bot reconnected and resumed session")
    bot_state.add_log("INFO", "Bot reconnected successfully")
    try:
        if ADMIN_USER_ID:
            user = await bot.fetch_user(ADMIN_USER_ID)
            await user.send("[BOT STATUS] ✅ Bot reconnected")
    except Exception as e:
        logger.error(f"Failed to notify admin on_resumed: {e}")

# --- 6. Main Execution with Auto-Reconnect ---

def validate_environment():
    """Validate required environment variables"""
    required_vars = {
        "DISCORD_TOKEN": "Discord Bot Token is required"
    }
    
    missing = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing.append(f"{var}: {description}")
    
    if missing:
        error_msg = "Missing required environment variables:\n" + "\n".join(missing)
        logger.critical(error_msg)
        bot_state.add_log("ERROR", error_msg)
        return False
    
    # Validate token format
    token = os.getenv("DISCORD_TOKEN")
    if len(token) < 50:
        logger.critical("DISCORD_TOKEN appears to be invalid (too short)")
        bot_state.add_log("ERROR", "Invalid DISCORD_TOKEN format")
        return False
    
    logger.info("Environment variables validated successfully")
    return True

async def run_bot_with_retry():
    """Run bot with automatic reconnection on failure"""
    # Validate environment first
    if not validate_environment():
        return
    
    TOKEN = os.getenv("DISCORD_TOKEN")
    
    try:
        bot_state.add_log("INFO", "Starting bot...")
        await bot.start(TOKEN)
    except discord.LoginFailure:
        logger.critical("Invalid Discord token!")
        bot_state.add_log("ERROR", "Invalid token")
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        bot_state.add_log("INFO", "Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        bot_state.add_log("ERROR", f"Bot crashed: {e}")
        await notify_admin(bot, f"Bot crashed: {e}")
    finally:
        if bot.db:
            bot.db.close()
        await bot.close()

async def shutdown():
    """Graceful shutdown handler"""
    logger.info("Shutting down gracefully...")
    bot_state.add_log("INFO", "Shutting down...")
    
    # Close database
    if bot.db:
        bot.db.close()
    
    # Disconnect from all voice channels
    for guild_id, manager in bot.managers.items():
        try:
            if manager.voice_client:
                await manager.voice_client.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting from guild {guild_id}: {e}")
    
    # Close bot connection
    await bot.close()
    
    logger.info("Shutdown complete")
    bot_state.add_log("INFO", "Shutdown complete")

if __name__ == "__main__":
    import signal
    
    def signal_handler(sig, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {sig}, initiating shutdown...")
        bot_state.add_log("INFO", f"Received shutdown signal")
        asyncio.create_task(shutdown())
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(run_bot_with_retry())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        bot_state.add_log("INFO", "Bot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        bot_state.add_log("ERROR", f"Fatal error: {e}")
