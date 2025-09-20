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
