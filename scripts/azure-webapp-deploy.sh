#!/bin/bash

# Azure Web App Deployment Script
# สำหรับ deploy บน Azure App Service (มี auto-scaling)

set -e

echo "🚀 Starting Azure Web App Deployment..."

# Configuration
RESOURCE_GROUP="discord-bot-rg"
LOCATION="southeastasia"
ACR_NAME="sakudokobotregistry"
APP_SERVICE_PLAN="sakudoko-plan"
WEB_APP_NAME="sakudoko-music-bot"
IMAGE_NAME="sakudoko-bot:latest"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI ไม่ได้ติดตั้ง"
    exit 1
fi

# Login
echo "📝 Logging in to Azure..."
az login

# Create Resource Group
echo "📦 Creating Resource Group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Container Registry
echo "🐳 Creating Azure Container Registry..."
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

# Build and push image
echo "🔨 Building Docker image..."
az acr build --registry $ACR_NAME --image $IMAGE_NAME .

# Get ACR credentials
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

# Create App Service Plan (B1 tier - ฟรีสำหรับนักศึกษา)
echo "📋 Creating App Service Plan..."
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --is-linux \
  --sku B1

# Create Web App
echo "🌐 Creating Web App..."
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $WEB_APP_NAME \
  --deployment-container-image-name $ACR_LOGIN_SERVER/$IMAGE_NAME

# Configure container registry credentials
az webapp config container set \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --docker-custom-image-name $ACR_LOGIN_SERVER/$IMAGE_NAME \
  --docker-registry-server-url https://$ACR_LOGIN_SERVER \
  --docker-registry-server-user $ACR_USERNAME \
  --docker-registry-server-password $ACR_PASSWORD

# Prompt for environment variables
echo ""
echo "⚙️  กรุณาใส่ Environment Variables:"
read -p "DISCORD_TOKEN: " DISCORD_TOKEN
read -p "ADMIN_USER_ID: " ADMIN_USER_ID

# Set environment variables
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --settings \
    DISCORD_TOKEN="$DISCORD_TOKEN" \
    ADMIN_USER_ID="$ADMIN_USER_ID" \
    WEBSITES_PORT=8080 \
    WEBSITES_CONTAINER_START_TIME_LIMIT=600

# Enable logging
az webapp log config \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --docker-container-logging filesystem

# Get Web App URL
WEB_APP_URL=$(az webapp show --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP --query defaultHostName -o tsv)

echo ""
echo "✅ Deployment สำเร็จ!"
echo "📊 Dashboard URL: https://$WEB_APP_URL"
echo ""
echo "📝 คำสั่งที่เป็นประโยชน์:"
echo "  - ดู logs: az webapp log tail --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP"
echo "  - Restart: az webapp restart --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP"
echo "  - ลบทั้งหมด: az group delete --name $RESOURCE_GROUP --yes"
