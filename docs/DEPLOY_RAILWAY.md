# 🚀 Deploy Discord Bot บน Railway (ฟรี)

## ข้อดี Railway
- ✅ ฟรี $5 credit ทุกเดือน (ไม่ต้องใช้บัตรเครดิต)
- ✅ Deploy ง่ายมาก เชื่อมต่อ GitHub แล้วกด Deploy
- ✅ Auto-deploy เมื่อ push code ใหม่
- ✅ มี Dashboard สวยงาม
- ✅ รองรับ Docker

## วิธี Deploy

### 1. สร้างบัญชี Railway
1. ไปที่ https://railway.app
2. Sign up ด้วย GitHub account
3. ยืนยัน email

### 2. Deploy จาก GitHub

#### ถ้ามี GitHub Repository แล้ว:
1. กด **"New Project"** ใน Railway Dashboard
2. เลือก **"Deploy from GitHub repo"**
3. เลือก repository ของคุณ
4. Railway จะ detect Dockerfile อัตโนมัติ

#### ถ้ายังไม่มี GitHub Repository:
```bash
# สร้าง repository ใหม่บน GitHub
# แล้ว push code ขึ้นไป
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 3. ตั้งค่า Environment Variables

ใน Railway Dashboard:
1. เลือก project ที่สร้าง
2. ไปที่ **Variables** tab
3. เพิ่ม variables:
   - `DISCORD_TOKEN` = your_discord_token
   - `ADMIN_USER_ID` = your_discord_user_id (optional)
   - `PORT` = 8080

### 4. Deploy!

Railway จะ build และ deploy อัตโนมัติ ใช้เวลาประมาณ 2-3 นาที

### 5. ตรวจสอบ

- ดู logs ใน **Deployments** tab
- ตรวจสอบว่า bot online ใน Discord
- Dashboard จะอยู่ที่ URL ที่ Railway generate ให้

## 💰 ค่าใช้จ่าย

- **Free Tier**: $5 credit/เดือน
- Bot ขนาดเล็ก ใช้ประมาณ $3-4/เดือน
- **เพียงพอสำหรับ bot ที่มี 1-10 servers**

## 🔧 คำสั่งที่เป็นประโยชน์

### ดู Logs
```bash
# ติดตั้ง Railway CLI
npm i -g @railway/cli

# Login
railway login

# ดู logs
railway logs
```

### Restart Service
ใน Railway Dashboard → Service → Settings → Restart

## 📝 Tips

1. **ประหยัด Credit**: ปิด service เมื่อไม่ใช้งาน
2. **Monitor Usage**: ดูการใช้งานใน Usage tab
3. **Custom Domain**: เพิ่ม custom domain ได้ฟรี
4. **Database**: Railway มี PostgreSQL, MySQL, Redis ฟรีด้วย

## 🐛 Troubleshooting

### Bot ไม่ online
- ตรวจสอบ logs ใน Deployments tab
- ตรวจสอบ DISCORD_TOKEN ใน Variables

### Out of Credit
- ลบ service ที่ไม่ใช้
- หรือ upgrade เป็น paid plan ($5/month)

---

## Alternative: Deploy ด้วย Railway CLI

```bash
# ติดตั้ง Railway CLI
npm i -g @railway/cli

# Login
railway login

# สร้าง project ใหม่
railway init

# เพิ่ม environment variables
railway variables set DISCORD_TOKEN=your_token
railway variables set ADMIN_USER_ID=your_id

# Deploy
railway up
```

---

**เชิญบอท:** [Invite Bot](https://discord.com/oauth2/authorize?client_id=1438729107578814564&scope=bot+applications.commands&permissions=277025508352)
