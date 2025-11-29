# 🚀 Quick Start - Deploy Discord Bot บน Azure

## ขั้นตอนที่ 1: หา Discord User ID

1. เปิด Discord
2. ไปที่ **User Settings** (⚙️) → **Advanced**
3. เปิด **Developer Mode**
4. คลิกขวาที่ชื่อตัวเอง → **Copy User ID**

## ขั้นตอนที่ 2: Deploy บน Azure

### สำหรับ Windows (PowerShell)

```powershell
# 1. ติดตั้ง Azure CLI
winget install Microsoft.AzureCLI

# 2. ปิด PowerShell แล้วเปิดใหม่

# 3. ไปที่โฟลเดอร์โปรเจค
cd "C:\path\to\your\project"

# 4. Run deployment
.\azure-deploy.ps1
```

### ข้อมูลที่ต้องใส่

เมื่อ script ถาม:
- **DISCORD_TOKEN**: Discord Bot Token ของคุณ (ดูได้จาก Discord Developer Portal)
- **ADMIN_USER_ID**: User ID ของคุณ (ตัวเลข 18 หลัก)

## ขั้นตอนที่ 3: เชิญบอทเข้า Server

เปิดลิงก์นี้ในเบราว์เซอร์:
```
https://discord.com/oauth2/authorize?client_id=1438729107578814564&permissions=8&integration_type=0&scope=bot
```

เลือก Server ที่ต้องการและกด **Authorize**

## ขั้นตอนที่ 4: ทดสอบ Bot

หลัง deploy เสร็จ (ประมาณ 5-10 นาที):

1. Bot จะ online ใน Discord
2. พิมพ์ `/help` เพื่อดูคำสั่งทั้งหมด
3. พิมพ์ `/join` เพื่อให้บอทเข้าห้องเสียง

## 📊 ดู Dashboard

เปิดเบราว์เซอร์ไปที่:
```
http://sakudoko-bot.southeastasia.azurecontainer.io:8080
```

## 🔧 คำสั่งที่เป็นประโยชน์

### ดู Logs
```powershell
az container logs --resource-group discord-bot-rg --name sakudoko-bot --follow
```

### Restart Bot
```powershell
az container restart --resource-group discord-bot-rg --name sakudoko-bot
```

### ดูสถานะ
```powershell
az container show --resource-group discord-bot-rg --name sakudoko-bot
```

### ลบทั้งหมด (เมื่อไม่ใช้แล้ว)
```powershell
az group delete --name discord-bot-rg --yes
```

## 🐛 Troubleshooting

### Bot ไม่ online
```powershell
# ดู logs เพื่อหาสาเหตุ
az container logs --resource-group discord-bot-rg --name sakudoko-bot
```

### Token ผิด
1. ไปที่ Discord Developer Portal
2. Bot → Reset Token
3. Update environment variable:
```powershell
az container delete --resource-group discord-bot-rg --name sakudoko-bot --yes
# แล้วรัน azure-deploy.ps1 ใหม่
```

### Dashboard เข้าไม่ได้
- รอ 2-3 นาทีหลัง deploy
- ตรวจสอบว่า container กำลังทำงาน:
```powershell
az container show --resource-group discord-bot-rg --name sakudoko-bot --query instanceView.state
```

## 💰 ค่าใช้จ่าย

- **Container Instances**: ~$10-15/เดือน
- **Azure for Students**: $100 credit ฟรี
- **ใช้ได้**: 6-10 เดือนฟรี

## 🔒 Security Tips

1. **อย่าแชร์ Token** ให้ใครเห็น
2. **ลบข้อความที่มี Token** หลังใช้งาน
3. ถ้า Token รั่วไหล → **Regenerate ทันที**
4. เพิ่ม `.env` ใน `.gitignore` (ทำแล้ว ✅)

## 📚 คำสั่ง Bot

- `/join` - ให้บอทเข้าห้องเสียง
- `/play [เพลง]` - เล่นเพลง
- `/queue` - ดูคิวเพลง
- `/leave` - ให้บอทออกจากห้อง
- `/help` - ดูคำสั่งทั้งหมด

---

**หมายเหตุ:** หลัง deploy เสร็จ ควรลบ Token ออกจากประวัติแชท เพื่อความปลอดภัย
