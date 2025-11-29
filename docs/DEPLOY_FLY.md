# 🚀 Deploy Discord Bot บน Fly.io (ฟรี)

## ข้อดี Fly.io
- ✅ ฟรี (แต่ต้องใส่บัตรเครดิต)
- ✅ Performance ดี
- ✅ มี free tier: 3 shared-cpu VMs
- ✅ ไม่ sleep เหมือน Render

## ⚠️ ข้อควรระวัง
- ต้องใส่บัตรเครดิต (แต่ไม่มีการเรียกเก็บเงินถ้าไม่เกิน limit)
- Free tier: 3 shared-cpu-1x VMs, 160GB bandwidth/month

## วิธี Deploy

### 1. ติดตั้ง Fly CLI

**Windows:**
```powershell
iwr https://fly.io/install.ps1 -useb | iex
```

**Mac/Linux:**
```bash
curl -L https://fly.io/install.sh | sh
```

### 2. Login และสร้าง App

```bash
# Login (ต้องใส่บัตรเครดิต)
fly auth login

# สร้าง app (ใช้ fly.toml ที่มีอยู่แล้ว)
fly launch --no-deploy

# ตั้งค่า secrets
fly secrets set DISCORD_TOKEN=your_discord_token
fly secrets set ADMIN_USER_ID=your_discord_user_id

# Deploy
fly deploy
```

### 3. ตรวจสอบ

```bash
# ดู status
fly status

# ดู logs
fly logs

# เปิด dashboard
fly dashboard
```

## 💰 ค่าใช้จ่าย

**Free Tier ได้:**
- 3 shared-cpu-1x VMs (256MB RAM)
- 3GB persistent volume storage
- 160GB outbound bandwidth/month

**เพียงพอสำหรับ Discord bot ขนาดเล็ก-กลาง**

## 🔧 คำสั่งที่เป็นประโยชน์

```bash
# Scale up/down
fly scale count 1

# Restart
fly apps restart

# ดู metrics
fly metrics

# SSH เข้า container
fly ssh console
```

## 📝 Tips

1. ตรวจสอบ usage ใน dashboard เป็นประจำ
2. ถ้าเกิน free tier จะมีการเรียกเก็บเงิน
3. ตั้ง spending limit ใน billing settings

---

**สรุป**: Fly.io ดีแต่ต้องใส่บัตรเครดิต ถ้าไม่อยากใส่บัตร ใช้ Railway แทน
