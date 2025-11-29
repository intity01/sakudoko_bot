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
    
    # ปรับปรุงคุณภาพเสียง: เพิ่ม bitrate และ audio codec
    options = '-vn -b:a 128k'  # 128kbps audio bitrate (เพิ่มคุณภาพ)
    if filter_str:
        options += f' -af "{filter_str}"'
    
    return {
        'options': options,
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
    }


# ตั้งค่า yt-dlp - ใช้ android_embedded client + cookies (ถ้ามี)
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
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'sleep_interval': 1,  # หน่วงเวลา 1 วินาทีระหว่างการดึงข้อมูล (ป้องกัน rate limit)
    'max_sleep_interval': 3,
    # ใช้ android_embedded client - หลีกเลี่ยง bot detection
    'extractor_args': {
        'youtube': {
            'player_client': ['android_embedded'],
        }
    },
}

# ถ้าต้องการใช้ cookies เพื่อหลีกเลี่ยง rate limit ให้ตั้งค่า YTDLP_BROWSER ใน .env
browser = os.getenv("YTDLP_BROWSER")
if browser:
    try:
        ytdl_format_options['cookiesfrombrowser'] = (browser,)
        logger.info(f"Using cookies from {browser} to avoid rate limits")
    except Exception as e:
        logger.warning(f"Could not load cookies from {browser}: {e}")

# เพิ่ม proxy support จาก .env (ถ้ามี)
proxy_url = os.getenv("YTDLP_PROXY")
if proxy_url:
    ytdl_format_options['proxy'] = proxy_url
    logger.info(f"Using proxy: {proxy_url}")

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)
logger.info("yt-dlp initialized with android_embedded client (no cookies needed)")

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):  # เพิ่มเสียงจาก 0.3 เป็น 0.5 (50%)
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.webpage_url = data.get('webpage_url')
        self.duration = data.get('duration')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False, filter_name=None):
        loop = loop or asyncio.get_event_loop()
        
        # Use a search prefix if the URL doesn't look like a URL
        if not url.startswith(('http://', 'https://')):
            url = f"ytsearch:{url}"

        try:
            # Blocking call, run in executor
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        except yt_dlp.DownloadError as e:
            logger.error(f"YTDL Download Error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"General YTDL Error for {url}: {e}")
            return None

        if not data:
            return None

        # If it's a search result, take the first entry
        if 'entries' in data:
            # If it's a search, take the first result
            if url.startswith('ytsearch:'):
                data = data['entries'][0] if data['entries'] else None
            # If it's a playlist, the caller (MusicManager) should handle it
            else:
                # This case should ideally not be reached if MusicManager handles playlists
                # but as a fallback, we take the first entry for playback
                data = data['entries'][0] if data['entries'] else None

        if not data:
            return None

        # Ensure we have a direct stream URL
        if 'url' not in data:
            logger.error(f"No direct URL found in YTDL data for {data.get('title')}")
            return None

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        ffmpeg_opts = get_ffmpeg_options(filter_name)
        
        # Use the correct executable if specified, otherwise rely on system path
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_opts), data=data)

# Export ytdl instance for use in music_manager for search/playlist extraction
YTDL_INSTANCE = ytdl
