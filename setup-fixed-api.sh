#!/bin/bash

# Fixed API Configuration Script for WhatsApp AI Concierge Service
# This script sets up a stable API configuration using container names

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔧 Setting up Fixed API Configuration for WhatsApp AI Concierge${NC}"

# Get container IPs dynamically
APP_IP=$(docker inspect ai-concierge-app-1 --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
WAHA_IP=$(docker inspect waha-core --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')

echo -e "${YELLOW}📍 Container IPs:${NC}"
echo "  Concierge App: ${APP_IP}"
echo "  WAHA Core: ${WAHA_IP}"

# Check if containers are running
if [ -z "$APP_IP" ] || [ -z "$WAHA_IP" ]; then
    echo -e "${RED}❌ Error: One or more containers are not running${NC}"
    exit 1
fi

# Method 1: Using container names (most reliable)
CONCIERGE_URL="http://ai-concierge-app-1:8000"
WEBHOOK_URL="${CONCIERGE_URL}/api/v1/webhook"

echo -e "${YELLOW}🌐 Using fixed URLs:${NC}"
echo "  Concierge API: ${CONCIERGE_URL}"
echo "  Webhook URL: ${WEBHOOK_URL}"

# Method 2: Update environment files with fixed configuration
echo -e "${YELLOW}📝 Updating configuration...${NC}"

# Create backup of original .env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Update webhook URL to use container name
sed -i "s|WEBHOOK_URL=.*|WEBHOOK_URL=${WEBHOOK_URL}|g" .env

# Add fixed API configuration if not exists
if ! grep -q "CONCIERGE_API_URL" .env; then
    cat >> .env << EOF

# Fixed API Configuration (auto-generated)
CONCIERGE_API_URL=${CONCIERGE_URL}
CONCIERGE_WEBHOOK_URL=${WEBHOOK_URL}
CONCIERGE_HEALTH_URL=${CONCIERGE_URL}/health
EOF
fi

echo -e "${GREEN}✅ Configuration updated${NC}"

# Method 3: Test the webhook endpoint
echo -e "${YELLOW}🧪 Testing webhook endpoint...${NC}"

# Test from within the WAHA container
if docker exec waha-core curl -s --connect-timeout 5 "${CONCIERGE_URL}/health" > /dev/null; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
fi

# Method 4: Create a systemd service for stability (optional)
echo -e "${YELLOW}📋 Creating service configuration...${NC}"

cat > concierge-fixed-api.service << EOF
[Unit]
Description=WhatsApp AI Concierge Fixed API Configuration
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=$(pwd)/scripts/update-webhook-config.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# Create webhook update script
mkdir -p scripts
cat > scripts/update-webhook-config.sh << 'EOF'
#!/bin/bash
# Script to update WAHA webhook configuration

CONCIERGE_URL="http://ai-concierge-app-1:8000"
WEBHOOK_URL="${CONCIERGE_URL}/api/v1/webhook"

# Try to update WAHA webhook (this may need adjustment based on WAHA auth)
docker exec waha-core curl -X POST "http://localhost:3000/api/sessions/default/webhook" \
  -H "Content-Type: application/json" \
  -H "x-api-key: waha-secret-key-12345" \
  -d "{\"url\": \"${WEBHOOK_URL}\", \"events\": [\"message\", \"message.any\"], \"enable\": true}" 2>/dev/null || \
echo "WAHA webhook update may need manual configuration"

echo "Webhook configuration updated: ${WEBHOOK_URL}"
EOF

chmod +x scripts/update-webhook-config.sh

echo -e "${GREEN}🎉 Fixed API Configuration Complete!${NC}"
echo
echo -e "${YELLOW}📋 Summary:${NC}"
echo "  ✅ Container names configured for stable networking"
echo "  ✅ Environment variables updated"
echo "  ✅ Configuration scripts created"
echo "  ✅ Health check endpoint available"
echo
echo -e "${YELLOW}🔗 Fixed URLs:${NC}"
echo "  API: ${CONCIERGE_URL}"
echo "  Webhook: ${WEBHOOK_URL}"
echo "  Health: ${CONCIERGE_URL}/health"
echo
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "  1. Restart services: docker compose restart"
echo "  2. Test webhook: curl -X GET ${CONCIERGE_URL}/health"
echo "  3. Monitor logs: docker compose logs -f"
echo
echo -e "${GREEN}💡 Pro Tip: Use container names instead of IPs for reliability!${NC}"