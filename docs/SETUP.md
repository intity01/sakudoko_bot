# คู่มือการติดตั้ง Sakudoko Music Bot

## ความต้องการของระบบ

- Python 3.8 หรือสูงกว่า
- FFmpeg (สำหรับเล่นเสียง)
- Discord Bot Token

## ขั้นตอนการติดตั้ง

### 1. สร้าง Discord Bot

1. ไปที่ [Discord Developer Portal](https://discord.com/developers/applications)
2. คลิก "New Application"
3. ตั้งชื่อบอทของคุณ
4. ไปที่แท็บ "Bot"
5. คลิก "Add Bot"
6. เปิดใช้งาน:
   - Presence Intent
   - Server Members Intent
   - Message Content Intent
7. คัดลอก Token (เก็บไว้ใช้ในขั้นตอนถัดไป)

### 2. เชิญบอทเข้าเซิร์ฟเวอร์

1. ไปที่แท็บ "OAuth2" > "URL Generator"
2. เลือก Scopes:
   - `bot`
   - `applications.commands`
3. เลือก Bot Permissions:
   - Read Messages/View Channels
   - Send Messages
   - Manage Messages
   - Embed Links
   - Attach Files
   - Read Message History
   - Add Reactions
   - Connect
   - Speak
   - Use Voice Activity
   - Manage Channels (สำหรับสร้าง/ลบห้องแชทเพลง)
4. คัดลอก URL และเปิดในเบราว์เซอร์
5. เลือกเซิร์ฟเวอร์ที่ต้องการเชิญบอท

### 3. ติดตั้ง FFmpeg

#### Windows:
1. ดาวน์โหลด FFmpeg จาก [ffmpeg.org](https://ffmpeg.org/download.html)
2. แตกไฟล์และเพิ่ม path ไปยัง System Environment Variables
3. หรือใช้ Chocolatey: `choco install ffmpeg`

#### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install ffmpeg
```

#### macOS:
```bash
brew install ffmpeg
```

### 4. ติดตั้ง Dependencies

```bash
# Clone repository
git clone <repository-url>
cd sakudoko_bot

# ติดตั้ง Python packages
pip install -r requirements.txt
```

### 5. ตั้งค่า Environment Variables

1. คัดลอกไฟล์ตัวอย่าง:
```bash
cp .env.example .env
```

2. แก้ไขไฟล์ `.env`:
```env
DISCORD_TOKEN=your_discord_bot_token_here
ADMIN_USER_ID=your_discord_user_id
PORT=8080
LOG_LEVEL=INFO
```

**หมายเหตุ:**
- `DISCORD_TOKEN`: Token ที่คัดลอกจาก Discord Developer Portal
- `ADMIN_USER_ID`: Discord User ID ของคุณ (ไม่บังคับ)
- `PORT`: พอร์ตสำหรับ Web Dashboard (ค่าเริ่มต้น: 8080)

### 6. รันบอท

```bash
python main.py
```

หรือใช้ script:

**Windows:**
```bash
run.bat
```

**Linux/macOS:**
```bash
chmod +x scripts/azure-deploy.sh
./scripts/azure-deploy.sh
```

### 7. ตรวจสอบว่าบอททำงาน

1. เปิด Web Dashboard: http://localhost:8080
2. ตรวจสอบว่าบอท Online ใน Discord
3. ลองใช้คำสั่ง `/ping` ในเซิร์ฟเวอร์

## การแก้ปัญหา

### บอทไม่ Online
- ตรวจสอบว่า Token ถูกต้อง
- ตรวจสอบว่าเปิดใช้งาน Intents ครบถ้วน
- ดู logs ใน `bot.log`

### ไม่สามารถเล่นเพลงได้
- ตรวจสอบว่าติดตั้ง FFmpeg แล้ว
- รัน `ffmpeg -version` เพื่อตรวจสอบ
- ตรวจสอบว่าบอทมีสิทธิ์ Connect และ Speak ในห้องเสียง

### Slash Commands ไม่แสดง
- รอ 1-2 ชั่วโมง (Discord ต้องใช้เวลาในการ sync)
- ลอง kick บอทออกแล้วเชิญใหม่
- ตรวจสอบว่าเลือก `applications.commands` scope ตอนเชิญบอท

### Dashboard ไม่เปิด
- ตรวจสอบว่าพอร์ต 8080 ไม่ถูกใช้งานโดยโปรแกรมอื่น
- เปลี่ยนพอร์ตใน `.env` ถ้าจำเป็น
- ตรวจสอบ firewall settings

## ขั้นตอนถัดไป

- อ่าน [FEATURES.md](FEATURES.md) เพื่อดูฟีเจอร์ทั้งหมด
- อ่าน [DEPLOY_AZURE.md](DEPLOY_AZURE.md) สำหรับการ deploy บน Azure
- อ่าน [DEPLOY_RAILWAY.md](DEPLOY_RAILWAY.md) สำหรับการ deploy บน Railway
