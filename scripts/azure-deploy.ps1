# Azure Deployment Script for Windows PowerShell
# สำหรับนักศึกษาที่มี Azure for Students

Write-Host "🚀 Starting Azure Deployment..." -ForegroundColor Green

# Configuration
$RESOURCE_GROUP = "discord-bot-rg"
$LOCATION = "southeastasia"
$ACR_NAME = "sakudokobotregistry"
$CONTAINER_NAME = "sakudoko-bot"
$IMAGE_NAME = "sakudoko-bot:latest"

# Check if Azure CLI is installed
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Azure CLI ไม่ได้ติดตั้ง กรุณาติดตั้งก่อน: winget install Microsoft.AzureCLI" -ForegroundColor Red
    exit 1
}

# Login to Azure
Write-Host "📝 Logging in to Azure..." -ForegroundColor Cyan
az login

# Create Resource Group
Write-Host "📦 Creating Resource Group..." -ForegroundColor Cyan
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Container Registry
Write-Host "🐳 Creating Azure Container Registry..." -ForegroundColor Cyan
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

# Get ACR credentials
$ACR_USERNAME = az acr credential show --name $ACR_NAME --query username -o tsv
$ACR_PASSWORD = az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv

# Build and push Docker image
Write-Host "🔨 Building and pushing Docker image..." -ForegroundColor Cyan
az acr build --registry $ACR_NAME --image $IMAGE_NAME .

# Prompt for environment variables
Write-Host ""
Write-Host "⚙️  กรุณาใส่ Environment Variables:" -ForegroundColor Yellow
$DISCORD_TOKEN = Read-Host "DISCORD_TOKEN"
$ADMIN_USER_ID = Read-Host "ADMIN_USER_ID"

# Deploy Container Instance
Write-Host "🚀 Deploying Container Instance..." -ForegroundColor Cyan
az container create `
  --resource-group $RESOURCE_GROUP `
  --name $CONTAINER_NAME `
  --image "$ACR_NAME.azurecr.io/$IMAGE_NAME" `
  --registry-login-server "$ACR_NAME.azurecr.io" `
  --registry-username $ACR_USERNAME `
  --registry-password $ACR_PASSWORD `
  --dns-name-label $CONTAINER_NAME `
  --ports 8080 `
  --environment-variables `
    DISCORD_TOKEN="$DISCORD_TOKEN" `
    ADMIN_USER_ID="$ADMIN_USER_ID" `
  --cpu 1 `
  --memory 1.5 `
  --restart-policy Always

# Get container URL
$CONTAINER_FQDN = az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --query ipAddress.fqdn -o tsv

Write-Host ""
Write-Host "✅ Deployment สำเร็จ!" -ForegroundColor Green
Write-Host "📊 Dashboard URL: http://$CONTAINER_FQDN:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 คำสั่งที่เป็นประโยชน์:" -ForegroundColor Yellow
Write-Host "  - ดู logs: az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --follow"
Write-Host "  - Restart: az container restart --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"
Write-Host "  - ลบทั้งหมด: az group delete --name $RESOURCE_GROUP --yes"
