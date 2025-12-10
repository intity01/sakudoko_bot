import discord
import asyncio
import os
import logging
import aiohttp
import re

logger = logging.getLogger('discord_bot')

# ตั้งค่า FFmpeg
def get_ffmpeg_options(filter_name=None):
    """Generates FFmpeg options with optional audio filters."""
    filter_map = {
        'bass': 'bass=g=10',
        'nightcore': 'asetrate=44100*1.25,aresample=44100,atempo=1.1',
        'pitch': 'asetrate=44100*1.15,aresample=44100',
    }
    filter_str = filter_map.get(filter_name)
    
    options = '-vn -b:a 128k'
    if filter_str:
        options += f' -af "{filter_str}"'
    
    return {
        'options': options,
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
    }

# Cobalt API (ฟรี และเสถียร)
COBALT_API = "https://api.cobalt.tools"

class CobaltAPI:
    """Wrapper for Cobalt API to fetch YouTube audio"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    async def get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    def extract_video_id(self, url: str):
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
            r'^([a-zA-Z0-9_-]{11})$'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def extract_playlist_id(self, url: str):
        """Extract playlist ID from YouTube URL"""
        match = re.search(r'[?&]list=([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(1)
        return None
    
    async def get_audio_url(self, youtube_url: str):
        """Get audio stream URL from Cobalt API"""
        session = await self.get_session()
        
        try:
            payload = {
                "url": youtube_url,
                "videoQuality": "720",
                "audioFormat": "mp3",
                "isAudioOnly": True,
                "disableMetadata": True
            }
            
            async with session.post(
                COBALT_API,
                json=payload,
                headers=self.headers,
                timeout=30
            ) as resp:
                data = await resp.json()
                logger.info(f"Cobalt API response status: {resp.status}, data: {data.get('status', 'unknown')}")
                
                if resp.status == 200:
                    status = data.get("status")
                    
                    if status in ["stream", "tunnel", "redirect"]:
                        audio_url = data.get("url")
                        if audio_url:
                            logger.info(f"Cobalt API success: got audio URL")
                            return audio_url
                    
                    elif status == "picker":
                        picker = data.get("picker", [])
                        for item in picker:
                            if "audio" in item.get("type", ""):
                                return item.get("url")
                        if picker:
                            return picker[0].get("url")
                    
                    elif status == "error":
                        error_msg = data.get("error", {}).get("code", data.get("text", "Unknown"))
                        logger.error(f"Cobalt API error: {error_msg}")
                        return None
                else:
                    error_text = data.get("text", data.get("error", {}).get("code", "Unknown"))
                    logger.error(f"Cobalt API returned status {resp.status}: {error_text}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.error("Cobalt API timeout")
            return None
        except Exception as e:
            logger.error(f"Cobalt API error: {e}")
            return None
        
        return None
    
    async def search_youtube(self, query: str):
        """Search YouTube using scraping (fallback method)"""
        session = await self.get_session()
        
        try:
            search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            
            async with session.get(search_url, timeout=10) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    # Extract video ID from search results
                    match = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', text)
                    if match:
                        video_id = match.group(1)
                        return {
                            'id': video_id,
                            'webpage_url': f"https://www.youtube.com/watch?v={video_id}"
                        }
        except Exception as e:
            logger.error(f"YouTube search error: {e}")
        
        return None
    
    async def get_video_info(self, video_id: str):
        """Get video info and audio URL"""
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Get audio URL from Cobalt
        audio_url = await self.get_audio_url(youtube_url)
        
        if not audio_url:
            return None
        
        # Try to get title from YouTube page
        title = await self._get_video_title(video_id)
        
        return {
            'id': video_id,
            'title': title or f"YouTube Video {video_id}",
            'url': audio_url,
            'duration': 0,
            'thumbnail': f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
            'webpage_url': youtube_url
        }
    
    async def _get_video_title(self, video_id: str):
        """Get video title from YouTube"""
        session = await self.get_session()
        
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    # Extract title
                    match = re.search(r'"title":"([^"]+)"', text)
                    if match:
                        return match.group(1)
        except:
            pass
        
        return None
    
    async def extract_info(self, query: str, download=False):
        """Extract info from URL or search query"""
        # Check if it's a YouTube URL
        video_id = self.extract_video_id(query)
        
        if video_id:
            return await self.get_video_info(video_id)
        
        # Check if it's a playlist (not supported yet)
        playlist_id = self.extract_playlist_id(query)
        if playlist_id:
            logger.warning("Playlist not supported with Cobalt API")
            return None
        
        # Search YouTube
        if not query.startswith(('http://', 'https://')):
            search_result = await self.search_youtube(query)
            if search_result:
                return await self.get_video_info(search_result['id'])
        
        return None

# สร้าง instance
cobalt = CobaltAPI()
logger.info("Cobalt API initialized (free YouTube alternative)")

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.webpage_url = data.get('webpage_url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False, filter_name=None):
        loop = loop or asyncio.get_event_loop()
        
        try:
            data = await cobalt.extract_info(url, download=not stream)
        except Exception as e:
            logger.error(f"Cobalt API Error for {url}: {e}")
            return None

        if not data:
            return None

        if 'url' not in data:
            logger.error(f"No direct URL found for {data.get('title')}")
            return None

        filename = data['url']
        ffmpeg_opts = get_ffmpeg_options(filter_name)
        
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_opts), data=data)

# Export for use in music_manager
YTDL_INSTANCE = cobalt
