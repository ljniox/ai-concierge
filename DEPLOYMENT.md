# WhatsApp Webhook Deployment Guide

## Coolify Deployment

### Prerequisites
- Coolify instance with access to your Git repository
- Docker registry (Coolify built-in or external)
- Domain name for webhook endpoint
- SSL certificate (Coolify can auto-generate with Let's Encrypt)
- **Important**: Compose file must be named `docker-compose.yaml` (Coolify requirement)

### Environment Variables for Coolify

Add these variables in Coolify:

```bash
# WhatsApp Webhook Settings
WEBHOOK_URL=https://your-domain.com/webhook
WEBHOOK_VERIFY_TOKEN=2MqxVV-vtba9Ha2vSn7CWu4qPGfdkEGbS8DzVv6gFaw
SESSION_NAME=default
PORT=8000

# Domain Configuration
DOMAIN=your-domain.com
```

### Deployment Steps

1. **Push to Git Repository**
   ```bash
   git add .
   git commit -m "Add WhatsApp webhook with Coolify deployment"
   git push origin main
   ```

2. **Create Coolify Application**
   - Go to your Coolify dashboard
   - Click "Create Application"
   - Select "Docker Compose" as source type
   - Connect your Git repository
   - Select the branch containing your webhook code

3. **Configure Environment**
   - Add all environment variables from above
   - Set the deployment path to root of repository
   - Configure domain and SSL

4. **Deploy**
   - Click "Deploy" to start the deployment
   - Coolify will build the Docker image and deploy it

### Manual Docker Deployment

If you prefer manual Docker deployment:

1. **Build Image**
   ```bash
   docker build -t whatsapp-webhook .
   ```

2. **Run Container**
   ```bash
   docker run -d \
     --name whatsapp-webhook \
     --restart unless-stopped \
     -p 8000:8000 \
     -e WEBHOOK_URL=https://your-domain.com/webhook \
     -e WEBHOOK_VERIFY_TOKEN=2MqxVV-vtba9Ha2vSn7CWu4qPGfdkEGbS8DzVv6gFaw \
     -e SESSION_NAME=default \
     -e PORT=8000 \
     whatsapp-webhook
   ```

### WAHA Configuration

After deployment, configure WAHA to use your webhook:

1. **Get your webhook URL** - It will be: `https://your-domain.com/webhook`

2. **Configure WAHA Session**
   - Use the webhook_config.py script:
   ```python
   from webhook_config import create_waha_session
   create_waha_session()
   ```

3. **Or manually configure WAHA**:
   ```bash
   curl -u admin:WassProdt!2025 \
     -X POST https://waha-core.niox.ovh/api/sessions \
     -H "Content-Type: application/json" \
     -d '{
       "name": "default",
       "config": {
         "webhook": {
           "webhookUrl": "https://your-domain.com/webhook",
           "events": ["message", "session.status", "chat"],
           "session": "default"
         }
       }
     }'
   ```

### Testing

1. **Health Check**
   ```bash
   curl https://your-domain.com/
   ```

2. **Webhook Verification**
   ```bash
   curl "https://your-domain.com/webhook?hub.mode=subscribe&hub.challenge=12345&hub.verify_token=2MqxVV-vtba9Ha2vSn7CWu4qPGfdkEGbS8DzVv6gFaw"
   ```

### Monitoring

- **Logs**: View logs in Coolify dashboard or with `docker logs whatsapp-webhook`
- **Health Check**: Automatic health check every 30 seconds
- **Auto-restart**: Container restarts on failure

### Security Notes

- The verify token is already generated and secure
- Always use HTTPS in production
- Keep environment variables secure
- Regularly update dependencies

### Troubleshooting

**Common Issues:**

1. **Container fails to start**: Check logs for missing dependencies
2. **Webhook not receiving messages**: Verify WAHA configuration and firewall settings
3. **SSL issues**: Ensure domain is properly configured in Coolify
4. **Port conflicts**: Ensure port 8000 is available

**Debug Commands:**
```bash
# Check container logs
docker logs whatsapp-webhook

# Test webhook endpoint
curl -X POST https://your-domain.com/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": "message"}'

# Check WAHA session status
curl -u admin:WassProdt!2025 https://waha-core.niox.ovh/api/sessions
```