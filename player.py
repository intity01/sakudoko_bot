import discord
import yt_dlp
import asyncio
import os
import logging

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

# yt-dlp config - ใช้หลาย client เพื่อหลีกเลี่ยง bot detection
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    # ใช้ web client แทน android (มีโอกาสสำเร็จมากกว่า)
    'extractor_args': {
        'youtube': {
            'player_client': ['web', 'android', 'ios'],
            'player_skip': ['webpage', 'configs'],
        }
    },
    # เพิ่ม headers เพื่อหลีกเลี่ยง bot detection
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    },
}

# ถ้ามี cookies file ให้ใช้
cookies_file = os.getenv("YTDLP_COOKIES_FILE")
if cookies_file and os.path.exists(cookies_file):
    ytdl_format_options['cookiefile'] = cookies_file
    logger.info(f"Using cookies file: {cookies_file}")

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)
logger.info("yt-dlp initialized with web/android/ios client fallback")


class YTDLWrapper:
    """Async wrapper for yt-dlp"""
    
    def __init__(self, ytdl_instance):
        self.ytdl = ytdl_instance
    
    async def extract_info(self, query: str, download=False):
        """Extract info asynchronously"""
        loop = asyncio.get_event_loop()
        
        # Add search prefix if not a URL
        if not query.startswith(('http://', 'https://')):
            query = f"ytsearch:{query}"
        
        try:
            data = await loop.run_in_executor(
                None, 
                lambda: self.ytdl.extract_info(query, download=download)
            )
            
            if not data:
                return None
            
            # Handle search results
            if 'entries' in data:
                if query.startswith('ytsearch:'):
                    # Take first search result
                    data = data['entries'][0] if data['entries'] else None
            
            return data
            
        except yt_dlp.DownloadError as e:
            logger.error(f"yt-dlp download error: {e}")
            return None
        except Exception as e:
            logger.error(f"yt-dlp error: {e}")
            return None


# สร้าง wrapper instance
ytdl_wrapper = YTDLWrapper(ytdl)
logger.info("YTDLWrapper initialized")


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
            data = await ytdl_wrapper.extract_info(url, download=not stream)
        except Exception as e:
            logger.error(f"YTDL Error for {url}: {e}")
            return None

        if not data:
            return None

        if 'url' not in data:
            logger.error(f"No direct URL found for {data.get('title')}")
            return None

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        ffmpeg_opts = get_ffmpeg_options(filter_name)
        
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_opts), data=data)


# Export for use in music_manager
YTDL_INSTANCE = ytdl_wrapper
