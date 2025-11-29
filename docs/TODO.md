# TODO List - สิ่งที่ควรเพิ่มในอนาคต

## 🔥 Priority High

### 1. Error Recovery & Stability ✅ DONE
- [x] Auto-reconnect เมื่อ disconnect
- [x] Retry mechanism สำหรับ YouTube download
- [ ] Graceful shutdown
- [ ] Memory leak prevention

### 2. Database Integration ✅ DONE
- [x] SQLite database สำหรับเก็บข้อมูล
- [x] บันทึกการตั้งค่าของแต่ละเซิร์ฟเวอร์
- [x] บันทึกประวัติการเล่นเพลง
- [x] User preferences

### 3. Playlist System ✅ DONE
- [x] บันทึก playlist ส่วนตัว
- [ ] แชร์ playlist ระหว่างผู้ใช้
- [ ] Import/Export playlist
- [ ] Favorite songs

### 4. Better Logging ✅ DONE
- [x] Log rotation (5MB per file, 5 backups)
- [x] Better log formatting
- [x] Dashboard integration

## 🎯 Priority Medium

### 4. Advanced Features
- [ ] Lyrics search
- [ ] Now playing with progress bar
- [ ] Volume control per user
- [ ] Seek to timestamp
- [ ] Queue history

### 5. Performance
- [ ] Cache YouTube metadata
- [ ] Optimize memory usage
- [ ] Faster queue processing
- [ ] Parallel downloads

### 6. UI/UX
- [ ] Better embed designs
- [ ] Interactive buttons
- [ ] Reaction controls
- [ ] Custom emojis

## 💡 Priority Low

### 7. Social Features
- [ ] User statistics
- [ ] Leaderboard (most played songs)
- [ ] Song recommendations
- [ ] Collaborative playlists

### 8. Admin Tools
- [ ] Ban/Unban users from music room
- [ ] Blacklist songs
- [ ] Rate limiting per user
- [ ] Usage analytics

### 9. Integration
- [ ] Spotify integration
- [ ] SoundCloud support
- [ ] Apple Music support
- [ ] Last.fm scrobbling

## 🐛 Known Issues

- [ ] bot.log ไม่สามารถลบได้ขณะ bot ทำงาน
- [ ] Slash commands อาจใช้เวลานานในการ sync
- [ ] Dashboard WebSocket อาจ disconnect บางครั้ง

## 📝 Documentation

- [x] SETUP.md - คู่มือการติดตั้ง
- [x] FEATURES.md - รายการฟีเจอร์
- [x] CHANGELOG.md - ประวัติการเปลี่ยนแปลง
- [ ] API.md - API documentation
- [ ] CONTRIBUTING.md - คู่มือสำหรับ contributors
- [ ] FAQ.md - คำถามที่พบบ่อย

## 🔒 Security

- [ ] Rate limiting API endpoints
- [ ] Input validation
- [ ] SQL injection prevention
- [ ] XSS protection in dashboard
- [ ] Environment variable encryption

## 🧪 Testing

- [ ] Unit tests
- [ ] Integration tests
- [ ] Load testing
- [ ] CI/CD pipeline
