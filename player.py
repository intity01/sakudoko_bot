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

# Piped instances (ฟรี 100% - เสถียรกว่า Invidious)
PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://api-piped.mha.fi",
    "https://pipedapi.in.projectsegfau.lt",
    "https://pipedapi-libre.kavin.rocks",
    "https://api.piped.yt",
    "https://pipedapi.adminforge.de",
]

class PipedAPI:
    """Wrapper for Piped API to fetch YouTube data"""
    
    def __init__(self):
        self.current_instance = random.choice(PIPED_INSTANCES)
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
        """Search for videos on YouTube via Piped"""
        session = await self.get_session()
        
        for instance in PIPED_INSTANCES:
            try:
                url = f"{instance}/search"
                params = {
                    'q': query,
                    'filter': 'videos'
                }
                
                async with session.get(url, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        results = []
                        items = data.get('items', [])
                        for item in items[:max_results]:
                            if item.get('type') == 'stream':
                                results.append({
                                    'id': item.get('url', '').replace('/watch?v=', ''),
                                    'title': item.get('title'),
                                    'duration': item.get('duration', 0),
                                    'thumbnail': item.get('thumbnail'),
                                    'webpage_url': f"https://www.youtube.com{item.get('url')}"
                                })
                        if results:
                            logger.info(f"Search successful on {instance}")
                            return results
            except asyncio.TimeoutError:
                logger.warning(f"Timeout searching on {instance}")
                continue
            except Exception as e:
                logger.warning(f"Failed to search on {instance}: {e}")
                continue
        
        raise Exception("All Piped instances failed")
    
    async def get_video_info(self, video_id: str):
        """Get video information and stream URL"""
        session = await self.get_session()
        
        for instance in PIPED_INSTANCES:
            try:
                url = f"{instance}/streams/{video_id}"
                
                async with session.get(url, timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        # หา audio stream ที่ดีที่สุด
                        audio_streams = data.get('audioStreams', [])
                        
                        if not audio_streams:
                            logger.warning(f"No audio streams in response from {instance}")
                            continue
                        
                        # เรียงตาม bitrate
                        audio_streams.sort(key=lambda x: x.get('bitrate', 0), reverse=True)
                        best_audio = audio_streams[0]
                        
                        audio_url = best_audio.get('url')
                        if not audio_url:
                            logger.warning(f"No URL in audio stream from {instance}")
                            continue
                        
                        logger.info(f"Successfully got video info from {instance}")
                        return {
                            'id': video_id,
                            'title': data.get('title'),
                            'url': audio_url,
                            'duration': data.get('duration', 0),
                            'thumbnail': data.get('thumbnailUrl'),
                            'webpage_url': f"https://www.youtube.com/watch?v={video_id}"
                        }
                    else:
                        logger.warning(f"Got status {resp.status} from {instance}")
            except asyncio.TimeoutError:
                logger.warning(f"Timeout getting video info from {instance}")
                continue
            except Exception as e:
                logger.warning(f"Failed to get video info from {instance}: {e}")
                continue
        
        raise Exception("All Piped instances failed")
    
    async def get_playlist(self, playlist_id: str):
        """Get playlist information"""
        session = await self.get_session()
        
        for instance in PIPED_INSTANCES:
            try:
                url = f"{instance}/playlists/{playlist_id}"
                
                async with session.get(url, timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        videos = []
                        
                        for video in data.get('relatedStreams', []):
                            video_id = video.get('url', '').replace('/watch?v=', '')
                            videos.append({
                                'id': video_id,
                                'title': video.get('title'),
                                'duration': video.get('duration', 0),
                                'thumbnail': video.get('thumbnail'),
                                'webpage_url': f"https://www.youtube.com/watch?v={video_id}"
                            })
                        
                        return {
                            'title': data.get('name'),
                            'entries': videos
                        }
            except Exception as e:
                logger.warning(f"Failed to get playlist from {instance}: {e}")
                continue
        
        raise Exception("All Piped instances failed")
    
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
piped = PipedAPI()
logger.info("Piped API initialized (free YouTube alternative)")

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
            # ใช้ Piped API แทน yt-dlp
            data = await piped.extract_info(url, download=not stream)
        except Exception as e:
            logger.error(f"Piped API Error for {url}: {e}")
            return None

        if not data:
            return None

        # Ensure we have a direct stream URL
        if 'url' not in data:
            logger.error(f"No direct URL found in Piped data for {data.get('title')}")
            return None

        filename = data['url']
        ffmpeg_opts = get_ffmpeg_options(filter_name)
        
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_opts), data=data)

# Export piped instance for use in music_manager
YTDL_INSTANCE = piped
