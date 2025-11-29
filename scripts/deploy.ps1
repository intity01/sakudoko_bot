# Azure Deployment Script
# Simple version without Thai characters

Write-Host "Starting Azure Deployment..." -ForegroundColor Green
Write-Host ""

# Config
$RESOURCE_GROUP = "discord-bot-rg"
$LOCATION = "southeastasia"
$ACR_NAME = "sakudokobotregistry"
$CONTAINER_NAME = "sakudoko-bot"
$IMAGE_NAME = "sakudoko-bot:latest"

# Ask for Discord Token
Write-Host "Enter your Discord Bot Token:" -ForegroundColor Yellow
$DISCORD_TOKEN = Read-Host "DISCORD_TOKEN"

# Ask for User ID
Write-Host "Enter your Discord User ID (or 0 if you don't know):" -ForegroundColor Yellow
$ADMIN_USER_ID = Read-Host "ADMIN_USER_ID"

if ([string]::IsNullOrWhiteSpace($ADMIN_USER_ID)) {
    $ADMIN_USER_ID = "0"
}

Write-Host ""
Write-Host "Configuration:" -ForegroundColor Green
Write-Host "  Token: $($DISCORD_TOKEN.Substring(0,20))..."
Write-Host "  Admin ID: $ADMIN_USER_ID"
Write-Host ""

# Find az.cmd
$azCmd = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
if (-not (Test-Path $azCmd)) {
    $azCmd = "C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
}

if (-not (Test-Path $azCmd)) {
    Write-Host "ERROR: Azure CLI not found" -ForegroundColor Red
    Write-Host "Please install: winget install Microsoft.AzureCLI" -ForegroundColor Yellow
    exit 1
}

Write-Host "Found Azure CLI: $azCmd" -ForegroundColor Green
Write-Host ""

# Step 1: Login
Write-Host "[1/6] Logging in to Azure..." -ForegroundColor Cyan
& $azCmd login
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host "OK" -ForegroundColor Green
Write-Host ""

# Step 2: Create Resource Group
Write-Host "[2/6] Creating Resource Group..." -ForegroundColor Cyan
& $azCmd group create --name $RESOURCE_GROUP --location $LOCATION --output none
Write-Host "OK" -ForegroundColor Green
Write-Host ""

# Step 3: Create Container Registry
Write-Host "[3/6] Creating Container Registry (1-2 min)..." -ForegroundColor Cyan
& $azCmd acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true --output none
Write-Host "OK" -ForegroundColor Green
Write-Host ""

# Step 4: Get credentials
Write-Host "[4/6] Getting credentials..." -ForegroundColor Cyan
$ACR_USERNAME = (& $azCmd acr credential show --name $ACR_NAME --query username -o tsv).Trim()
$ACR_PASSWORD = (& $azCmd acr credential show --name $ACR_NAME --query passwords[0].value -o tsv).Trim()
Write-Host "OK" -ForegroundColor Green
Write-Host ""

# Step 5: Build image
Write-Host "[5/6] Building Docker image (3-5 min)..." -ForegroundColor Cyan
& $azCmd acr build --registry $ACR_NAME --image $IMAGE_NAME .
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build failed" -ForegroundColor Red
    exit 1
}
Write-Host "OK" -ForegroundColor Green
Write-Host ""

# Step 6: Deploy container
Write-Host "[6/6] Deploying container (2-3 min)..." -ForegroundColor Cyan
& $azCmd container create --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --image "$ACR_NAME.azurecr.io/$IMAGE_NAME" --registry-login-server "$ACR_NAME.azurecr.io" --registry-username $ACR_USERNAME --registry-password $ACR_PASSWORD --dns-name-label $CONTAINER_NAME --ports 8080 --environment-variables DISCORD_TOKEN=$DISCORD_TOKEN ADMIN_USER_ID=$ADMIN_USER_ID --cpu 1 --memory 1.5 --restart-policy Always --output none

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Deploy failed" -ForegroundColor Red
    exit 1
}
Write-Host "OK" -ForegroundColor Green
Write-Host ""

# Get URL
$CONTAINER_FQDN = (& $azCmd container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --query ipAddress.fqdn -o tsv).Trim()

Write-Host "========================================" -ForegroundColor Gray
Write-Host "DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Gray
Write-Host ""
Write-Host "Dashboard: http://$CONTAINER_FQDN:8080" -ForegroundColor Yellow
Write-Host ""
Write-Host "Bot will be online in 1-2 minutes" -ForegroundColor Cyan
Write-Host ""
Write-Host "Invite bot:" -ForegroundColor Cyan
Write-Host "https://discord.com/oauth2/authorize?client_id=1438729107578814564&permissions=8&integration_type=0&scope=bot" -ForegroundColor Yellow
Write-Host ""
Write-Host "View logs:" -ForegroundColor Cyan
Write-Host "& '$azCmd' container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --follow" -ForegroundColor Gray
Write-Host ""
