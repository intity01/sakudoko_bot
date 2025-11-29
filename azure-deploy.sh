#!/bin/bash

# Azure Deployment Script for Sakudoko Discord Bot
# สำหรับนักศึกษาที่มี Azure for Students

set -e

echo "🚀 Starting Azure Deployment..."

# Configuration
RESOURCE_GROUP="discord-bot-rg"
LOCATION="southeastasia"
ACR_NAME="sakudokobotregistry"
CONTAINER_NAME="sakudoko-bot"
IMAGE_NAME="sakudoko-bot:latest"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI ไม่ได้ติดตั้ง กรุณาติดตั้งก่อน: https://docs.microsoft.com/cli/azure/install-azure-cli"
    exit 1
fi

# Login to Azure
echo "📝 Logging in to Azure..."
az login

# Create Resource Group
echo "📦 Creating Resource Group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Container Registry
echo "🐳 Creating Azure Container Registry..."
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

# Build and push Docker image
echo "🔨 Building and pushing Docker image..."
az acr build --registry $ACR_NAME --image $IMAGE_NAME .

# Prompt for environment variables
echo ""
echo "⚙️  กรุณาใส่ Environment Variables:"
read -p "DISCORD_TOKEN: " DISCORD_TOKEN
read -p "ADMIN_USER_ID: " ADMIN_USER_ID

# Deploy Container Instance
echo "🚀 Deploying Container Instance..."
az container create \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --image $ACR_NAME.azurecr.io/$IMAGE_NAME \
  --registry-login-server $ACR_NAME.azurecr.io \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --dns-name-label $CONTAINER_NAME \
  --ports 8080 \
  --environment-variables \
    DISCORD_TOKEN="$DISCORD_TOKEN" \
    ADMIN_USER_ID="$ADMIN_USER_ID" \
  --cpu 1 \
  --memory 1.5 \
  --restart-policy Always

# Get container URL
CONTAINER_FQDN=$(az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --query ipAddress.fqdn -o tsv)

echo ""
echo "✅ Deployment สำเร็จ!"
echo "📊 Dashboard URL: http://$CONTAINER_FQDN:8080"
echo ""
echo "📝 คำสั่งที่เป็นประโยชน์:"
echo "  - ดู logs: az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --follow"
echo "  - Restart: az container restart --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"
echo "  - ลบทั้งหมด: az group delete --name $RESOURCE_GROUP --yes"
