# 🚀 Deploy Discord Bot บน Azure for Students

## ข้อกำหนดเบื้องต้น

1. **Azure for Students Account**
   - ลงทะเบียนที่: https://azure.microsoft.com/free/students/
   - ได้ $100 credit ฟรี (ไม่ต้องใช้บัตรเครดิต)

2. **ติดตั้ง Azure CLI**
   - Windows: `winget install Microsoft.AzureCLI`
   - Mac: `brew install azure-cli`
   - Linux: https://docs.microsoft.com/cli/azure/install-azure-cli-linux

3. **Discord Bot Token**
   - สร้างที่: https://discord.com/developers/applications
   - เปิด Privileged Gateway Intents: MESSAGE CONTENT, SERVER MEMBERS

---

## 🎯 วิธีที่ 1: Azure Container Instances (แนะนำสำหรับเริ่มต้น)

**ข้อดี:**
- ง่ายที่สุด
- ราคาถูก (~$10-15/เดือน แต่มี credit ฟรี)
- Deploy เร็ว

**ขั้นตอน:**

```bash
# 1. ให้สิทธิ์ execute script
chmod +x azure-deploy.sh

# 2. Run script
./azure-deploy.sh

# 3. ใส่ DISCORD_TOKEN และ ADMIN_USER_ID เมื่อถูกถาม
```

**หรือ Deploy แบบ Manual:**

```bash
# Login
az login

# สร้าง Resource Group
az group create --name discord-bot-rg --location southeastasia

# สร้าง Container Registry
az acr create --resource-group discord-bot-rg --name sakudokobotregistry --sku Basic

# Build และ Push Image
az acr build --registry sakudokobotregistry --image sakudoko-bot:latest .

# Deploy Container
az container create \
  --resource-group discord-bot-rg \
  --name sakudoko-bot \
  --image sakudokobotregistry.azurecr.io/sakudoko-bot:latest \
  --dns-name-label sakudoko-bot \
  --ports 8080 \
  --environment-variables \
    DISCORD_TOKEN="YOUR_TOKEN" \
    ADMIN_USER_ID="YOUR_USER_ID" \
  --cpu 1 \
  --memory 1.5 \
  --restart-policy Always
```

---

## 🌐 วิธีที่ 2: Azure App Service (Web App)

**ข้อดี:**
- Auto-scaling
- Monitoring ดีกว่า
- CI/CD integration

**ขั้นตอน:**

```bash
# 1. ให้สิทธิ์ execute script
chmod +x azure-webapp-deploy.sh

# 2. Run script
./azure-webapp-deploy.sh
```

---

## 📊 ตรวจสอบและจัดการ Bot

### ดู Logs
```bash
# Container Instances
az container logs --resource-group discord-bot-rg --name sakudoko-bot --follow

# Web App
az webapp log tail --name sakudoko-music-bot --resource-group discord-bot-rg
```

### Restart Bot
```bash
# Container Instances
az container restart --resource-group discord-bot-rg --name sakudoko-bot

# Web App
az webapp restart --name sakudoko-music-bot --resource-group discord-bot-rg
```

### ดู Dashboard
- Container Instances: `http://sakudoko-bot.southeastasia.azurecontainer.io:8080`
- Web App: `https://sakudoko-music-bot.azurewebsites.net`

### ดูสถานะและค่าใช้จ่าย
```bash
# ดู Resource ทั้งหมด
az resource list --resource-group discord-bot-rg --output table

# ดูค่าใช้จ่าย
az consumption usage list --output table
```

---

## 🔧 Update Bot

### Container Instances
```bash
# Build image ใหม่
az acr build --registry sakudokobotregistry --image sakudoko-bot:latest .

# Restart container (จะ pull image ใหม่)
az container restart --resource-group discord-bot-rg --name sakudoko-bot
```

### Web App
```bash
# Build และ push image ใหม่
az acr build --registry sakudokobotregistry --image sakudoko-bot:latest .

# Restart web app
az webapp restart --name sakudoko-music-bot --resource-group discord-bot-rg
```

---

## 💰 ประมาณการค่าใช้จ่าย (ใช้ Azure Credit)

### Container Instances
- CPU: 1 vCPU
- Memory: 1.5 GB
- ประมาณ: ~$10-15/เดือน

### App Service (B1 Plan)
- ประมาณ: ~$13/เดือน
- รวม 1.75 GB RAM, 100 GB Storage

**หมายเหตุ:** Azure for Students ให้ $100 credit ฟรี ใช้ได้ 6-10 เดือน

---

## 🗑️ ลบทรัพยากร (เมื่อไม่ใช้แล้ว)

```bash
# ลบทั้งหมด
az group delete --name discord-bot-rg --yes --no-wait

# ตรวจสอบว่าลบหมดแล้ว
az group list --output table
```

---

## 🐛 Troubleshooting

### Bot ไม่ online
```bash
# ดู logs
az container logs --resource-group discord-bot-rg --name sakudoko-bot

# ตรวจสอบ environment variables
az container show --resource-group discord-bot-rg --name sakudoko-bot
```

### Dashboard เข้าไม่ได้
- ตรวจสอบว่า port 8080 เปิดอยู่
- ลอง restart container

### Out of Memory
```bash
# เพิ่ม memory เป็น 2 GB
az container create ... --memory 2
```

---

## 📚 Resources

- [Azure for Students](https://azure.microsoft.com/free/students/)
- [Azure CLI Documentation](https://docs.microsoft.com/cli/azure/)
- [Azure Container Instances](https://docs.microsoft.com/azure/container-instances/)
- [Azure App Service](https://docs.microsoft.com/azure/app-service/)

---

## 💡 Tips

1. ใช้ `southeastasia` region เพื่อ latency ต่ำ
2. ตั้ง `--restart-policy Always` เพื่อ auto-restart
3. ใช้ Azure Portal เพื่อ monitor ง่ายขึ้น: https://portal.azure.com
4. เปิด Application Insights สำหรับ monitoring (ฟรี 5GB/เดือน)
