import discord
import asyncio
import os
import logging
import aiohttp
import random
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
    
    # ปรับปรุงคุณภาพเสียง: เพิ่ม bitrate และ audio codec
    options = '-vn -b:a 128k'  # 128kbps audio bitrate (เพิ่มคุณภาพ)
    if filter_str:
        options += f' -af "{filter_str}"'
    
    return {
        'options': options,
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
    }

# Invidious instances (ฟรี 100%)
INVIDIOUS_INSTANCES = [
    "https://inv.nadeko.net",
    "https://invidious.private.coffee",
    "https://iv.nboeck.de",
    "https://invidious.fdn.fr",
    "https://inv.tux.pizza",
    "https://invidious.perennialte.ch",
]

class InvidiousAPI:
    """Wrapper for Invidious API to fetch YouTube data"""
    
    def __init__(self):
        self.current_instance = random.choice(INVIDIOUS_INSTANCES)
        self.session = None
    
    async def get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close aiohttp session"""
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
    
    async def search(self, query: str, max_results: int = 1):
        """Search for videos on YouTube via Invidious"""
        session = await self.get_session()
        
        for instance in INVIDIOUS_INSTANCES:
            try:
                url = f"{instance}/api/v1/search"
                params = {
                    'q': query,
                    'type': 'video',
                    'sort_by': 'relevance'
                }
                
                async with session.get(url, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        results = []
                        for item in data[:max_results]:
                            results.append({
                                'id': item.get('videoId'),
                                'title': item.get('title'),
                                'duration': item.get('lengthSeconds', 0),
                                'thumbnail': f"https://i.ytimg.com/vi/{item.get('videoId')}/maxresdefault.jpg",
                                'webpage_url': f"https://www.youtube.com/watch?v={item.get('videoId')}"
                            })
                        return results
            except Exception as e:
                logger.warning(f"Failed to search on {instance}: {e}")
                continue
        
        raise Exception("All Invidious instances failed")
    
    async def get_video_info(self, video_id: str):
        """Get video information and stream URL"""
        session = await self.get_session()
        
        for instance in INVIDIOUS_INSTANCES:
            try:
                url = f"{instance}/api/v1/videos/{video_id}"
                
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        # หา audio stream ที่ดีที่สุด
                        audio_formats = [f for f in data.get('adaptiveFormats', []) 
                                       if f.get('type', '').startswith('audio/')]
                        
                        if not audio_formats:
                            raise Exception("No audio stream found")
                        
                        # เรียงตาม bitrate
                        audio_formats.sort(key=lambda x: x.get('bitrate', 0), reverse=True)
                        best_audio = audio_formats[0]
                        
                        return {
                            'id': video_id,
                            'title': data.get('title'),
                            'url': best_audio.get('url'),
                            'duration': data.get('lengthSeconds', 0),
                            'thumbnail': f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
                            'webpage_url': f"https://www.youtube.com/watch?v={video_id}"
                        }
            except Exception as e:
                logger.warning(f"Failed to get video info from {instance}: {e}")
                continue
        
        raise Exception("All Invidious instances failed")
    
    async def get_playlist(self, playlist_id: str):
        """Get playlist information"""
        session = await self.get_session()
        
        for instance in INVIDIOUS_INSTANCES:
            try:
                url = f"{instance}/api/v1/playlists/{playlist_id}"
                
                async with session.get(url, timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        videos = []
                        
                        for video in data.get('videos', []):
                            videos.append({
                                'id': video.get('videoId'),
                                'title': video.get('title'),
                                'duration': video.get('lengthSeconds', 0),
                                'thumbnail': f"https://i.ytimg.com/vi/{video.get('videoId')}/maxresdefault.jpg",
                                'webpage_url': f"https://www.youtube.com/watch?v={video.get('videoId')}"
                            })
                        
                        return {
                            'title': data.get('title'),
                            'entries': videos
                        }
            except Exception as e:
                logger.warning(f"Failed to get playlist from {instance}: {e}")
                continue
        
        raise Exception("All Invidious instances failed")
    
    async def extract_info(self, query: str, download=False):
        """Extract info from URL or search query (yt-dlp compatible interface)"""
        # ตรวจสอบว่าเป็น playlist หรือไม่
        playlist_id = self.extract_playlist_id(query)
        if playlist_id:
            return await self.get_playlist(playlist_id)
        
        # ตรวจสอบว่าเป็น video URL หรือไม่
        video_id = self.extract_video_id(query)
        if video_id:
            return await self.get_video_info(video_id)
        
        # ถ้าไม่ใช่ URL ให้ search
        results = await self.search(query, max_results=1)
        if results:
            video_id = results[0]['id']
            return await self.get_video_info(video_id)
        
        return None

# สร้าง instance
invidious = InvidiousAPI()
logger.info("Invidious API initialized (free YouTube alternative)")

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
            # ใช้ Invidious API แทน yt-dlp
            data = await invidious.extract_info(url, download=not stream)
        except Exception as e:
            logger.error(f"Invidious API Error for {url}: {e}")
            return None

        if not data:
            return None

        # Ensure we have a direct stream URL
        if 'url' not in data:
            logger.error(f"No direct URL found in Invidious data for {data.get('title')}")
            return None

        filename = data['url']
        ffmpeg_opts = get_ffmpeg_options(filter_name)
        
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_opts), data=data)

# Export invidious instance for use in music_manager
YTDL_INSTANCE = invidious
