# 📁 โครงสร้างโปรเจกต์ - Sakudoko Bot Enhanced

## 📂 ไฟล์หลัก

### 🤖 Bot Core Files
```
main.py                     # ไฟล์หลักของบอท + FastAPI Dashboard
├── โหลด Cogs ทั้งหมด
├── เริ่ม Discord Bot
├── เริ่ม FastAPI Server
└── WebSocket สำหรับ Real-time Logs

music_cog.py                # คำสั่งเพลงพื้นฐาน (เดิม)
├── /join, /leave
├── /play, /pause, /resume
├── /skip, /stop, /queue
├── /remove, /shuffle
├── /loop, /autoplay, /filter
└── Vote Skip System

music_cog_enhanced.py       # คำสั่งเพลงใหม่ (Enhanced)
├── /nowplaying             # แสดงเพลงที่กำลังเล่นพร้อม Progress Bar
├── /volume                 # ปรับระดับเสียง 0-200%
├── /seek                   # กระโดดไปยังเวลาที่ต้องการ
├── /lyrics                 # ค้นหาเนื้อเพลง
├── /playlist_save          # บันทึก Playlist
├── /playlist_load          # โหลด Playlist
├── /playlist_list          # แสดงรายการ Playlist
└── /playlist_delete        # ลบ Playlist

basic.py                    # คำสั่งพื้นฐาน
├── !ping                   # ตรวจสอบ Latency
└── /help                   # แสดงคำสั่งทั้งหมด
```

### 🎵 Music System Files
```
music_manager.py            # จัดการ Music Queue และ Playback
├── MusicManager Class
│   ├── Queue Management
│   ├── Loop System
│   ├── Autoplay System
│   ├── Filter System
│   └── Database Integration
└── Guild-specific Music States

player.py                   # YouTube Downloader และ Audio Source
├── YTDLSource Class
│   ├── yt-dlp Integration
│   ├── YouTube Search
│   ├── Audio Extraction
│   └── Error Handling
└── FFmpeg Audio Source

views.py                    # Discord UI Components
├── MusicControlView        # ปุ่มควบคุมเพลง
│   ├── Play/Pause Button
│   ├── Skip Button
│   ├── Stop Button
│   └── Volume Select
└── Interactive Components
```

### 🗄️ Database Files
```
database.py                 # SQLite Database Handler
├── init_database()         # สร้างตารางทั้งหมด
├── Song History Functions
│   ├── add_song_history()
│   └── get_top_songs()
├── Playlist Functions
│   ├── save_playlist()
│   ├── load_playlist()
│   ├── get_user_playlists()
│   └── delete_playlist()
└── Guild Settings Functions

bot_data.db                 # SQLite Database File (สร้างอัตโนมัติ)
├── song_history            # ตารางประวัติเพลง
├── user_playlists          # ตารางเก็บ Playlist
└── guild_settings          # ตารางการตั้งค่าเซิร์ฟเวอร์
```

### 🌐 Dashboard Files
```
index.html                  # Dashboard เดิม
├── Stats Display
├── Commands List
└── Basic Logs

index_enhanced.html         # Dashboard ใหม่ (Enhanced)
├── Dark Mode Toggle        # สลับโหมดสว่าง/มืด
├── Remote Control          # ควบคุมเพลงจากเว็บ
│   ├── Play/Pause Button
│   ├── Skip Button
│   ├── Stop Button
│   └── Volume Slider
├── Live Stats              # สถิติแบบ Real-time
│   ├── Servers Count
│   ├── Users Count
│   └── Uptime
├── Now Playing Section     # แสดงเพลงที่กำลังเล่น
│   ├── Current Song
│   ├── Queue List
│   └── Top Songs
└── WebSocket Logs          # Log แบบ Real-time

dashboard_api.py            # API Endpoints สำหรับ Dashboard
├── GET /api/health
├── GET /api/stats
├── GET /api/logs
├── POST /api/control
└── WS /ws/logs
```

---

## 📋 Configuration Files

### 🔧 Environment & Config
```
.env.example                # ตัวอย่างไฟล์ Environment Variables
├── DISCORD_TOKEN
├── ADMIN_USER_IDS
├── DATABASE_PATH
└── PORT

.gitignore                  # Git Ignore Rules
├── Python cache
├── Virtual environment
├── Database files
├── Log files
└── Environment variables

requirements.txt            # Python Dependencies
├── discord.py              # Discord API
├── wavelink                # Music streaming
├── yt-dlp                  # YouTube downloader
├── fastapi                 # Web framework
├── uvicorn                 # ASGI server
└── aiohttp                 # Async HTTP
```

### 🐳 Deployment Files
```
Dockerfile                  # Docker Container Definition
├── FROM python:3.11-slim
├── Install FFmpeg
├── Install Dependencies
├── Copy Application Files
├── Expose Port 8080
└── CMD ["python", "main.py"]

docker-compose.yml          # Docker Compose Configuration
├── Service: bot
├── Environment Variables
├── Port Mapping: 8080:8080
├── Volume Mapping: ./data:/app/data
└── Restart Policy: unless-stopped

railway.json                # Railway Deployment Config
├── Build: DOCKERFILE
├── Start Command: python main.py
└── Restart Policy: ON_FAILURE

Procfile                    # Heroku Deployment Config
└── worker: python main.py

nixpacks.toml               # Nixpacks Configuration
└── Build settings
```

---

## 📚 Documentation Files

### 📖 Guides & Docs
```
README_ENHANCED.md          # คู่มือหลัก (English)
├── Features Overview
├── Quick Start Guide
├── Commands Reference
├── Docker Deployment
├── Cloud Deployment
├── API Documentation
└── Troubleshooting

FEATURES_SUMMARY.md         # สรุปฟีเจอร์ใหม่ (Thai)
├── ภาพรวมการปรับปรุง
├── ฟีเจอร์ใหม่ทั้งหมด
├── การเปลี่ยนแปลงจากเวอร์ชันเดิม
├── สถิติการปรับปรุง
└── ผลลัพธ์

INSTALLATION_GUIDE_TH.md    # คู่มือติดตั้ง (Thai)
├── ข้อกำหนดระบบ
├── การติดตั้งแบบปกติ
├── การติดตั้งด้วย Docker
├── การ Deploy บน Cloud
├── การตั้งค่า
├── การใช้งาน
└── แก้ไขปัญหา

PROJECT_STRUCTURE.md        # ไฟล์นี้
├── โครงสร้างโปรเจกต์
├── คำอธิบายไฟล์
└── ความสัมพันธ์ระหว่างไฟล์

LICENSE                     # MIT License
```

---

## 🎨 Assets & Resources

### 📁 Directories
```
assets/                     # ไฟล์ Assets
├── images/
├── icons/
└── sounds/

configs/                    # ไฟล์ Config เพิ่มเติม
└── filters.json

__pycache__/                # Python Cache (Git ignored)

data/                       # Data Directory (Git ignored)
└── bot_data.db
```

### 🖼️ Media Files
```
Logo.png                    # โลโก้บอท
docs - Copy.html            # เอกสารสำรอง
cookies.txt                 # YouTube Cookies (ถ้ามี)
```

---

## 🔄 File Dependencies

### ลำดับการโหลด
```
1. main.py
   ├── โหลด database.py
   ├── โหลด music_manager.py
   │   └── ใช้ database.py
   ├── โหลด player.py
   ├── โหลด views.py
   ├── โหลด basic.py
   ├── โหลด music_cog.py
   │   ├── ใช้ music_manager.py
   │   ├── ใช้ player.py
   │   └── ใช้ views.py
   ├── โหลด music_cog_enhanced.py
   │   ├── ใช้ music_manager.py
   │   ├── ใช้ player.py
   │   └── ใช้ database.py
   └── เริ่ม FastAPI Dashboard
       └── ใช้ dashboard_api.py (ถ้ามี)
```

---

## 📊 File Statistics

### จำนวนไฟล์
- **Python Files:** 8 ไฟล์
- **HTML Files:** 3 ไฟล์
- **Config Files:** 7 ไฟล์
- **Documentation:** 4 ไฟล์
- **Deployment Files:** 4 ไฟล์
- **Total:** 26 ไฟล์

### ขนาดโค้ด (โดยประมาณ)
- **main.py:** ~400 บรรทัด
- **music_cog.py:** ~600 บรรทัด
- **music_cog_enhanced.py:** ~600 บรรทัด
- **music_manager.py:** ~650 บรรทัด
- **database.py:** ~300 บรรทัด
- **player.py:** ~150 บรรทัด
- **views.py:** ~400 บรรทัด
- **Total:** ~3,100 บรรทัด

---

## 🎯 Key Files Summary

### ไฟล์ที่ต้องแก้ไขบ่อย
1. **music_cog_enhanced.py** - เพิ่มคำสั่งใหม่
2. **index_enhanced.html** - ปรับแต่ง Dashboard
3. **.env** - ตั้งค่า Environment Variables
4. **requirements.txt** - เพิ่ม Dependencies

### ไฟล์ที่ไม่ควรแก้ไข
1. **database.py** - Database Schema
2. **player.py** - YouTube Handler
3. **music_manager.py** - Core Music Logic

### ไฟล์ที่สร้างอัตโนมัติ
1. **bot_data.db** - Database
2. **__pycache__/** - Python Cache
3. **logs/** - Log Files

---

## 🚀 Quick Reference

### เริ่มต้นใช้งาน
```bash
# 1. ติดตั้ง Dependencies
pip install -r requirements.txt

# 2. ตั้งค่า Environment
cp .env.example .env
nano .env

# 3. รันบอท
python main.py
```

### เพิ่มคำสั่งใหม่
```python
# แก้ไข music_cog_enhanced.py
@app_commands.command(name="mycommand")
@commands.cooldown(1, 5, commands.BucketType.user)
async def mycommand(self, interaction: discord.Interaction):
    # Your code here
    pass
```

### Deploy ด้วย Docker
```bash
docker-compose up -d
```

---

**📌 หมายเหตุ:** โครงสร้างนี้ออกแบบมาเพื่อความยืดหยุ่นและง่ายต่อการขยาย สามารถเพิ่มฟีเจอร์ใหม่ได้โดยไม่กระทบกับโค้ดเดิม
