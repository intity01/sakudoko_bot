# Changelog

## [2.1.0] - 2025-11-29

### ✨ Added - New Features
- **Auto-Reconnect System**: Bot automatically reconnects on disconnect with exponential backoff
- **Database Integration**: SQLite database for persistent data
- **Playlist System**: Save, load, and manage personal playlists
  - `/playlist_save` - บันทึก queue ปัจจุบัน
  - `/playlist_load` - โหลด playlist ที่บันทึกไว้
  - `/playlist_list` - แสดง playlist ทั้งหมด
  - `/playlist_delete` - ลบ playlist
- **Song History**: Track and view played songs
  - `/history` - แสดงประวัติเพลงที่เล่น
  - `/top_songs` - แสดงเพลงที่เล่นบ่อยที่สุด
- **Log Rotation**: Automatic log file rotation (5MB per file, 5 backups)
- **Guild Settings**: Persistent server settings (volume, filter, auto-disconnect)
- **Error Recovery**: Better error handling with retry mechanism

### 🔧 Improved
- Enhanced logging system with rotation
- Better database structure
- Improved error messages
- More robust reconnection logic

## [2.0.0] - 2025-11-29

### ✨ Added
- Web Dashboard with real-time logs
- WebSocket support for live updates
- Health check endpoint
- Auto channel management
- Permission system (owner/admin)
- Anti-spam protection
- Filter/Effect system (Bass, Nightcore, Pitch)
- Autoplay mode
- Loop queue feature
- Shuffle queue feature
- Admin notification system

### 🔧 Changed
- Improved error handling
- Better logging system
- Optimized queue management
- Enhanced embed messages
- Restructured project folders

### 📁 Project Structure
```
sakudoko_bot/
├── main.py              # Main bot file
├── basic.py             # Basic commands
├── music_cog.py         # Music commands
├── music_manager.py     # Music queue manager
├── player.py            # Audio player
├── database.py          # Database handler
├── index.html           # Dashboard UI
├── scripts/             # Deploy scripts
│   ├── deploy.ps1
│   ├── azure-deploy.ps1
│   ├── azure-deploy.sh
│   └── azure-webapp-deploy.sh
├── docs/                # Documentation
│   ├── SETUP.md
│   ├── FEATURES.md
│   ├── DEPLOY_AZURE.md
│   ├── DEPLOY_RAILWAY.md
│   └── QUICK_START.md
├── assets/              # Images and static files
├── configs/             # Configuration files
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose
└── README.md            # Main documentation
```

### 🗑️ Removed
- Duplicate deploy scripts
- Unused backup files
- Old dashboard API file
- Unused views.py
- Enhanced music cog (not implemented)

## [1.0.0] - Initial Release

### Features
- Basic music playback
- Queue system
- Slash commands
- YouTube support
