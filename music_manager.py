import asyncio
import discord
import os
import time
import random
import logging
from typing import Optional, Dict, Any, List, Set
from views import MusicControlView
from player import YTDLSource, YTDL_INSTANCE as cobalt
from discord.ext import tasks

logger = logging.getLogger('discord_bot')

# Load config colors from .env or use default
NOW_PLAYING_COLOR = int(os.getenv("NOW_PLAYING_COLOR", "0x0099ff"), 16)
EMBED_THUMBNAIL = os.getenv("EMBED_THUMBNAIL", "https://cdn-icons-png.flaticon.com/512/727/727245.png")
EMBED_FOOTER_TEXT = os.getenv("EMBED_FOOTER_TEXT", "Sakudoko Music Bot | Enjoy your music!")
EMBED_FOOTER_ICON = os.getenv("EMBED_FOOTER_ICON", "https://cdn-icons-png.flaticon.com/512/727/727245.png")
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "300")) # 5 minutes (300 seconds)

class MusicManager:
    """
    Centralized class to manage music state and playback logic for a single guild.
    """
    def __init__(self, bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        self.queue: List[str] = []
        self.loop_queue: bool = False
        self.auto_play: bool = False
        self.vote_skip: Set[int] = set()
        self.now_playing_msg: Optional[discord.Message] = None
        self.music_channel_id: Optional[int] = None
        self.owner_id: Optional[int] = None # The user who started the room
        self.selected_filter: Optional[str] = None
        self.last_activity_time: float = time.time()
        self.warning_sent: bool = False  # Flag to prevent duplicate warnings
        self.cleanup_task = self.cleanup_check.start()

    @property
    def voice_client(self) -> Optional[discord.VoiceClient]:
        """Returns the VoiceClient for the guild."""
        return discord.utils.get(self.bot.voice_clients, guild__id=self.guild_id)

    def get_text_channel(self) -> Optional[discord.TextChannel]:
        """Returns the music text channel."""
        if self.music_channel_id:
            guild = self.bot.get_guild(self.guild_id)
            if guild:
                return guild.get_channel(self.music_channel_id)
        return None

    @tasks.loop(seconds=30.0)
    async def cleanup_check(self):
        """Checks for inactivity and cleans up the room after 5 minutes of no music."""
        vc = self.voice_client
        
        # ตรวจสอบว่าไม่มีเพลงเล่นและคิวว่าง
        if vc and not vc.is_playing() and not self.queue:
            time_since_last_activity = time.time() - self.last_activity_time
            
            # แจ้งเตือนเมื่อเหลือเวลา 1 นาที (แจ้งครั้งเดียว)
            if time_since_last_activity > TIMEOUT_SECONDS - 60 and not self.warning_sent:
                channel = self.get_text_channel()
                if channel:
                    try:
                        embed = discord.Embed(
                            title="⏰ แจ้งเตือน", 
                            description="บอทจะออกจากห้องใน 1 นาที หากไม่มีการเล่นเพลง", 
                            color=0xffcc00
                        )
                        await channel.send(embed=embed, delete_after=60)
                        self.warning_sent = True
                    except Exception:
                        pass
            
            # ปิดห้องเมื่อครบเวลา
            if time_since_last_activity > TIMEOUT_SECONDS:
                logger.info(f"Inactivity timeout ({TIMEOUT_SECONDS}s) for guild {self.guild_id}. Cleaning up.")
                guild = self.bot.get_guild(self.guild_id)
                if guild:
                    await self.disconnect_and_cleanup(guild)
                    # Remove manager instance from bot's state
                    if self.guild_id in self.bot.managers:
                        del self.bot.managers[self.guild_id]
                self.cleanup_task.cancel()
        else:
            # Reset warning flag เมื่อมีเพลงเล่นหรือมีคิว
            self.warning_sent = False

    def start_cleanup_task(self, guild: discord.Guild):
        """Starts the cleanup task when the room is created."""
        self.last_activity_time = time.time()
        # Cleanup task already started in __init__ with @tasks.loop decorator
        # No need to create additional task

    async def fade_volume(self, start: float, end: float, duration: float = 2.0, steps: int = 20):
        """Fades the volume of the current player source."""
        vc = self.voice_client
        if not vc or not hasattr(vc, 'source') or not vc.source:
            return
        step = (end - start) / steps
        delay = duration / steps
        vol = start
        for _ in range(steps):
            vol += step
            vc.source.volume = max(0.0, min(1.0, vol))
            await asyncio.sleep(delay)

    async def play_next(self, channel: discord.TextChannel):
        """Plays the next song in the queue."""
        self.last_activity_time = time.time()  # Reset timeout เมื่อเริ่มเล่นเพลง
        self.warning_sent = False  # Reset warning flag
        vc = self.voice_client
        
        if not vc:
            logger.warning(f"Voice client not found for guild {self.guild_id}. Cannot play next.")
            return

        if not self.queue:
            if self.auto_play:
                logger.info(f"Auto Play triggered for guild {self.guild_id}")
                default_keywords = ["lofi hip hop", "pop hits", "EDM", "chill music"]
                keyword = random.choice(default_keywords)
                
                try:
                    # Search for a random song/playlist
                    info = await cobalt.extract_info(keyword, download=False)
                    urls = []
                    if info and 'entries' in info:
                        # Pick a random entry from the playlist/search results
                        entry = random.choice([e for e in info['entries'] if e])
                        urls.append(entry['webpage_url'])
                    elif info and 'webpage_url' in info:
                        urls.append(info['webpage_url'])

                    if urls:
                        self.queue.append(urls[0])
                        logger.info(f"Auto Play: Added '{urls[0]}' to queue for server {self.guild_id}")
                        await self.play_next(channel)
                        return
                except Exception as e:
                    logger.error(f"Auto Play failed: {e}")
            
            # Queue is truly empty
            embed = discord.Embed(title="Queue Empty", description="🎶 คิวเพลงหมดแล้ว! บอทจะออกจากห้องใน 5 นาทีหากไม่มีการเล่นเพลง", color=0xffcc00)
            await channel.send(embed=embed)
            return

        next_entry = self.queue.pop(0)
        
        if self.loop_queue:
            self.queue.append(next_entry)

        try:
            # Use run_in_executor for blocking ytdl operation
            player = await YTDLSource.from_url(next_entry, loop=self.bot.loop, stream=True, filter_name=self.selected_filter)
            
            if not player:
                await channel.send(embed=discord.Embed(title="Error", description="❌ ไม่พบข้อมูลเพลง", color=0xff0000))
                return

            # Stop current song with fade out
            if vc.is_playing() and hasattr(vc, 'source') and vc.source:
                await self.fade_volume(vc.source.volume, 0.0, duration=0.5)
                vc.stop()
            
            player.volume = 0.0 # Start at 0 volume for fade in

            def after_play(e):
                if e:
                    logger.error(f'Player error: {e}')
                    # Attempt to play next song on error
                    asyncio.run_coroutine_threadsafe(self.play_next(channel), self.bot.loop)
                    return
                
                # Check if the voice client is still connected before playing next
                if self.voice_client:
                    if self.queue or self.auto_play:
                        asyncio.run_coroutine_threadsafe(self.play_next(channel), self.bot.loop)
                    else:
                        # เพลงจบและคิวว่าง - เริ่มนับเวลา timeout (ไม่ reset!)
                        logger.info(f"Queue finished for guild {self.guild_id}. Timeout countdown started.")
                else:
                    logger.info(f"Voice client disconnected for guild {self.guild_id}. Stopping playback.")

            vc.play(player, after=after_play)
            await self.fade_volume(0.0, 0.3, duration=1.0) # Fade in to 30% volume

            # Save to history
            self.current_song = {
                'title': getattr(player, 'title', 'Unknown'),
                'url': getattr(player, 'webpage_url', next_entry),
                'duration': getattr(player, 'duration', 0),
                'thumbnail': getattr(player, 'thumbnail', None)
            }
            
            # Save to database if available
            if hasattr(self.bot, 'db') and self.bot.db:
                try:
                    # Get requester info from the song entry if it's a dict
                    if isinstance(next_entry, dict):
                        requested_by = next_entry.get('requested_by_id', 0)
                        requested_by_name = next_entry.get('requested_by', 'Unknown')
                    else:
                        requested_by = 0
                        requested_by_name = 'Unknown'
                    
                    self.bot.db.add_song_history(
                        self.guild_id,
                        self.current_song['title'],
                        self.current_song['url'],
                        self.current_song['duration'],
                        requested_by,
                        requested_by_name
                    )
                except Exception as e:
                    logger.error(f"Failed to save song history: {e}")
            
            # Create Now Playing embed
            embed = discord.Embed(
                title="Now Playing",
                description=f"[{getattr(player, 'title', 'Unknown')}]({getattr(player, 'webpage_url', next_entry)})",
                color=NOW_PLAYING_COLOR
            )
            embed.set_thumbnail(url=EMBED_THUMBNAIL)
            embed.set_footer(text=EMBED_FOOTER_TEXT, icon_url=EMBED_FOOTER_ICON)
            
            # Update Now Playing message with MusicControlView
            view = MusicControlView(self.bot, logger, channel.guild, channel.id, self.guild_id)
            try:
                if self.now_playing_msg:
                    await self.now_playing_msg.edit(embed=embed, view=view)
                else:
                    self.now_playing_msg = await channel.send(embed=embed, view=view)
            except Exception as e:
                logger.error(f"Failed to send/edit Now Playing message: {e}")

        except Exception as e:
            logger.error(f"Failed to play next music: {e}")
            await channel.send(embed=discord.Embed(title="Error", description=f"❌ เล่นเพลงถัดไปไม่สำเร็จ: {e}", color=0xff0000))
            # Try to play the next song if the current one failed
            if self.queue or self.auto_play:
                await self.play_next(channel)

    async def skip_to_next(self, channel: discord.TextChannel):
        """Stops current song and calls play_next."""
        vc = self.voice_client
        if vc and vc.is_playing():
            # Stop the current player to trigger the after_play callback
            vc.stop()
        elif self.queue:
            # If not playing but queue exists, just call play_next
            await self.play_next(channel)
        else:
            embed = discord.Embed(title="Queue Empty", description="🎶 ไม่มีเพลงถัดไปในคิว!", color=0xffcc00)
            await channel.send(embed=embed)

    def shuffle_queue(self):
        """Shuffles the current queue."""
        if len(self.queue) > 1:
            random.shuffle(self.queue)
            return True
        return False

    def toggle_loop(self) -> bool:
        """Toggles the loop state."""
        self.loop_queue = not self.loop_queue
        return self.loop_queue

    def add_to_queue(self, urls: List[str]):
        """Adds a list of URLs to the queue."""
        self.queue.extend(urls)
        self.last_activity_time = time.time()  # Reset timeout เมื่อเพิ่มเพลง
        self.warning_sent = False  # Reset warning flag

    def remove_from_queue(self, index: int) -> Optional[str]:
        """Removes a song from the queue by index (1-based)."""
        if 1 <= index <= len(self.queue):
            return self.queue.pop(index - 1)
        return None

    def get_queue_preview(self) -> discord.Embed:
        """Generates an embed for the queue preview."""
        # This function seems unused in the new structure, but keep it for completeness
        if self.queue:
            preview_embed = discord.Embed(
                title="Queue Preview", 
                description=f"เพลงถัดไป: [{self.queue[0]}]({self.queue[0]})", 
                color=0x00ccff
            )
        else:
            preview_embed = discord.Embed(
                title="Queue Preview", 
                description="คิวว่าง กรุณาขอเพลงแรก!", 
                color=0x00ccff
            )
        preview_embed.set_footer(text=EMBED_FOOTER_TEXT, icon_url=EMBED_FOOTER_ICON)
        return preview_embed

    def get_queue_list_embed(self) -> discord.Embed:
        """Generates an embed listing the queue."""
        embed = discord.Embed(title="📋 คิวเพลงทั้งหมด", color=0x1DB954)
        if self.queue:
            # Try to get song titles if possible, but fall back to URL
            display_queue = []
            for i, url in enumerate(self.queue[:10]):
                # In a real scenario, we would store the title/info when adding to queue
                # For now, we'll just display the URL/query
                display_queue.append(f"**{i+1}.** {url}")
            
            embed.description = "\n".join(display_queue)
            
            if len(self.queue) > 10:
                embed.set_footer(text=f"...และอีก {len(self.queue)-10} เพลง | ใช้ /remove [ลำดับ] เพื่อลบเพลงจากคิว")
            else:
                embed.set_footer(text="ใช้ /remove [ลำดับ] เพื่อลบเพลงจากคิว")
        else:
            embed.description = "❌ คิวเพลงว่างเปล่า!"
            embed.color = discord.Color.from_rgb(255, 205, 0)
        return embed

    def get_required_votes(self) -> int:
        """Calculates the required votes for skip."""
        vc = self.voice_client
        if not vc or not vc.channel:
            return 1
        # Count non-bot members who are not muted/deafened by server
        member_count = len([m for m in vc.channel.members if not m.bot and not m.voice.self_mute and not m.voice.self_deaf])
        return max(1, member_count // 2)

    def add_vote_skip(self, user_id: int) -> bool:
        """Adds a vote to skip. Returns True if skip threshold is met."""
        self.vote_skip.add(user_id)
        required = self.get_required_votes()
        if len(self.vote_skip) >= required:
            self.vote_skip = set()
            return True
        return False

    def get_vote_status(self) -> tuple[int, int]:
        """Returns (current_votes, required_votes)."""
        return len(self.vote_skip), self.get_required_votes()

    def reset_vote_skip(self):
        """Resets the vote skip count."""
        self.vote_skip = set()

    async def disconnect_and_cleanup(self, guild: discord.Guild):
        """Disconnects the bot and cleans up the music room."""
        vc = self.voice_client
        if vc:
            await vc.disconnect()
        
        # Cancel cleanup task
        self.cleanup_task.cancel()
        
        # Delete music channel
        if self.music_channel_id:
            ch = guild.get_channel(self.music_channel_id)
            if ch:
                try:
                    await ch.delete(reason="Bot disconnected and room closed.")
                except Exception as e:
                    logger.error(f"Failed to delete music channel: {e}")
        
        # Delete Now Playing message
        if self.now_playing_msg:
            try:
                await self.now_playing_msg.delete()
            except Exception as e:
                logger.error(f"Failed to delete Now Playing message: {e}")
        
        # Reset state
        self.queue = []
        self.loop_queue = False
        self.auto_play = False
        self.vote_skip = set()
        self.now_playing_msg = None
        self.music_channel_id = None
        self.owner_id = None
        self.selected_filter = None
        
        logger.info(f"Cleaned up MusicManager for guild {self.guild_id}")

    async def handle_music_request(self, message: discord.Message, query: str):
        """Handles a music request from the music text channel."""
        channel = message.channel
        
        try:
            # 1. Extract info (async operation with Cobalt)
            info = await cobalt.extract_info(query, download=False)
            
            if not info:
                await channel.send(embed=discord.Embed(title="Error", description="❌ ไม่พบเพลงหรือวิดีโอจากคำค้นนี้", color=0xff0000), delete_after=5)
                return

            urls_to_add = []
            if 'entries' in info:
                # Handle playlist
                for entry in info['entries']:
                    if entry and 'webpage_url' in entry:
                        urls_to_add.append(entry['webpage_url'])
                
                if urls_to_add:
                    self.add_to_queue(urls_to_add)
                    embed = discord.Embed(title="Playlist Added", description=f"✅ เพิ่ม **{len(urls_to_add)}** เพลงจากเพลย์ลิสต์ **{info.get('title', 'Unknown Playlist')}** ลงในคิว", color=0x00ff99)
                    await channel.send(embed=embed, delete_after=10)
                else:
                    await channel.send(embed=discord.Embed(title="Error", description="❌ ไม่พบเพลงในเพลย์ลิสต์นี้", color=0xff0000), delete_after=5)
                    return
            else:
                # Handle single track
                url = info.get('webpage_url')
                title = info.get('title', 'Unknown Song')
                if url:
                    self.add_to_queue([url])
                    embed = discord.Embed(title="Song Added", description=f"✅ เพิ่มเพลง **{title}** ลงในคิว", color=0x00ff99)
                    await channel.send(embed=embed, delete_after=10)
                else:
                    await channel.send(embed=discord.Embed(title="Error", description="❌ ไม่สามารถดึง URL ของเพลงได้", color=0xff0000), delete_after=5)
                    return

            # 2. Start playing if not already playing
            vc = self.voice_client
            if vc and not vc.is_playing():
                await self.play_next(channel)

        except discord.errors.NotFound:
            logger.warning(f"Channel not found when handling music request. Channel may have been deleted.")
            # Channel was deleted, cleanup
            await self.disconnect_and_cleanup(message.guild)
        except Exception as e:
            logger.error(f"Error handling music request: {e}")
            try:
                await channel.send(embed=discord.Embed(title="Error", description=f"❌ เกิดข้อผิดพลาดในการประมวลผลคำขอ: {e}", color=0xff0000), delete_after=5)
            except discord.errors.NotFound:
                logger.warning("Could not send error message, channel not found")

    # Add a method to handle voice state updates (e.g., bot disconnected manually)
    async def handle_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Handles voice state updates, primarily for bot disconnection."""
        if member.id == self.bot.user.id:
            # Bot was in a voice channel and is no longer in one
            if before.channel and not after.channel:
                logger.info(f"Bot manually disconnected from voice channel in guild {self.guild_id}. Cleaning up.")
                guild = self.bot.get_guild(self.guild_id)
                if guild:
                    # Use the cleanup logic but don't try to disconnect again
                    await self._cleanup_state_only(guild)
                    # Remove manager instance from bot's state
                    if self.guild_id in self.bot.managers:
                        del self.bot.managers[self.guild_id]
                self.cleanup_task.cancel()

    async def _cleanup_state_only(self, guild: discord.Guild):
        """Cleans up state and deletes the music channel/message without disconnecting the voice client."""
        # Delete music channel
        if self.music_channel_id:
            ch = guild.get_channel(self.music_channel_id)
            if ch:
                try:
                    await ch.delete(reason="Bot disconnected and room closed.")
                except Exception as e:
                    logger.error(f"Failed to delete music channel: {e}")
        
        # Delete Now Playing message
        if self.now_playing_msg:
            try:
                await self.now_playing_msg.delete()
            except Exception as e:
                logger.error(f"Failed to delete Now Playing message: {e}")
        
        # Reset state
        self.queue = []
        self.loop_queue = False
        self.auto_play = False
        self.vote_skip = set()
        self.now_playing_msg = None
        self.music_channel_id = None
        self.owner_id = None
        self.selected_filter = None
        
        logger.info(f"Cleaned up MusicManager state for guild {self.guild_id}")
