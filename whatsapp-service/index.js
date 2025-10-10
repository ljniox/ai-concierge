const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion } = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');
const express = require('express');
const cors = require('cors');
const fs = require('fs-extra');
const path = require('path');
const qrcode = require('qrcode-terminal');
const crypto = require('crypto');

// Load environment variables
require('dotenv').config();

class WhatsAppService {
    constructor() {
        this.sock = null;
        this.qrCode = null;
        this.connectionStatus = 'disconnected';
        this.authInfo = null;
        this.instanceName = 'gust-ia';
        this.phoneNumber = '221773387902';

        // Create auth directory
        this.authDir = path.join(__dirname, 'auth', this.instanceName);
        fs.ensureDirSync(this.authDir);

        // Express app for API
        this.app = express();
        this.port = process.env.WHATSAPP_PORT || 3001;

        this.setupExpress();
        this.setupWhatsApp();
    }

    setupExpress() {
        this.app.use(cors());
        this.app.use(express.json());

        // Health check endpoint
        this.app.get('/health', (req, res) => {
            res.json({
                status: 'ok',
                connection: this.connectionStatus,
                instanceName: this.instanceName,
                phoneNumber: this.phoneNumber
            });
        });

        // Get QR code endpoint
        this.app.get('/qrcode', (req, res) => {
            if (this.qrCode) {
                res.json({
                    success: true,
                    qrcode: this.qrCode,
                    status: this.connectionStatus
                });
            } else {
                res.json({
                    success: false,
                    message: 'QR code not available',
                    status: this.connectionStatus
                });
            }
        });

        // Send message endpoint
        this.app.post('/send-message', async (req, res) => {
            try {
                const { phone, message } = req.body;

                if (!this.sock || this.connectionStatus !== 'connected') {
                    return res.status(400).json({
                        success: false,
                        message: 'WhatsApp not connected'
                    });
                }

                if (!phone || !message) {
                    return res.status(400).json({
                        success: false,
                        message: 'Phone and message required'
                    });
                }

                const jid = phone.includes('@s.whatsapp.net') ? phone : `${phone}@s.whatsapp.net`;

                await this.sock.sendMessage(jid, {
                    text: message
                });

                res.json({
                    success: true,
                    message: 'Message sent successfully'
                });
            } catch (error) {
                console.error('Error sending message:', error);
                res.status(500).json({
                    success: false,
                    message: error.message
                });
            }
        });

        // Webhook endpoint for receiving messages
        this.app.post('/webhook', async (req, res) => {
            try {
                const { phone, message, messageId } = req.body;

                // Forward to AI Concierge webhook
                const webhookUrl = process.env.AI_CONCIERGE_WEBHOOK_URL || 'http://localhost:8000/api/v1/webhook';

                // Transform message to WAHA format expected by AI Concierge
                const wahaPayload = {
                    event: "message",
                    session: this.instanceName,
                    payload: {
                        key: {
                            remoteJid: phone,
                            id: messageId,
                            fromMe: false
                        },
                        message: {
                            conversation: message
                        },
                        messageTimestamp: Math.floor(Date.now() / 1000),
                        from: phone,
                        id: messageId,
                        timestamp: Math.floor(Date.now() / 1000),
                        hasMedia: false
                    }
                };

                const response = await fetch(webhookUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(wahaPayload)
                });

                if (response.ok) {
                    const result = await response.json();

                    // Send the AI response back to WhatsApp
                    if (result.response) {
                        const jid = phone.includes('@s.whatsapp.net') ? phone : `${phone}@s.whatsapp.net`;
                        await this.sock.sendMessage(jid, {
                            text: result.response
                        });
                    }
                }

                res.json({ success: true });
            } catch (error) {
                console.error('Webhook error:', error);
                res.status(500).json({ success: false, message: error.message });
            }
        });
    }

    async setupWhatsApp() {
        try {
            console.log('🚀 Initializing WhatsApp service...');

            const { state, saveCreds } = await useMultiFileAuthState(this.authDir);
            const { version } = await fetchLatestBaileysVersion();

            this.sock = makeWASocket({
                version,
                auth: state,
                printQRInTerminal: true,
                mobile: false,
                connectTimeoutMs: 60000,
                qrTimeout: 0,
                defaultQueryTimeoutMs: undefined,
                keepAliveIntervalMs: 25000,
                browser: ['Gust-IA', 'Chrome', '120.0.0.0'],
                markOnlineOnConnect: true,
            });

            // Event listeners
            this.sock.ev.on('connection.update', (update) => {
                const { connection, lastDisconnect, qr } = update;

                console.log('Connection update:', update);

                if (qr) {
                    this.qrCode = qr;
                    this.connectionStatus = 'qr';
                    console.log('📱 QR Code generated!');
                    qrcode.generate(qr, { small: true });
                }

                if (connection === 'close') {
                    const shouldReconnect = (lastDisconnect?.error instanceof Boom)?.output?.statusCode !== DisconnectReason.loggedOut;
                    console.log('Connection closed. Reconnecting:', shouldReconnect);

                    if (shouldReconnect) {
                        this.connectionStatus = 'reconnecting';
                        setTimeout(() => this.setupWhatsApp(), 5000);
                    } else {
                        this.connectionStatus = 'disconnected';
                        console.log('Logged out, please scan QR code again');
                    }
                }

                if (connection === 'open') {
                    this.connectionStatus = 'connected';
                    console.log('✅ WhatsApp connected successfully!');
                    console.log(`📞 Connected with number: ${this.phoneNumber}`);
                }

                if (connection === 'connecting') {
                    this.connectionStatus = 'connecting';
                    console.log('🔄 Connecting to WhatsApp...');
                }
            });

            this.sock.ev.on('creds.update', saveCreds);

            this.sock.ev.on('messages.upsert', async (m) => {
                const msg = m.messages[0];
                if (!msg.message) return;

                const messageType = Object.keys(msg.message)[0];

                if (messageType === 'conversation' || messageType === 'extendedTextMessage') {
                    const text = msg.message.conversation || msg.message.extendedTextMessage.text;
                    const from = msg.key.remoteJid;
                    const sender = from.replace('@s.whatsapp.net', '');

                    console.log(`📨 New message from ${sender}: ${text}`);

                    // Forward message to AI Concierge
                    await this.forwardToAIConcierge(sender, text, msg.key.id);
                }
            });

            this.sock.ev.on('auth.update', (auth) => {
                console.log('Auth update:', auth);
            });

            this.connectionStatus = 'initializing';

        } catch (error) {
            console.error('Error setting up WhatsApp:', error);
            this.connectionStatus = 'error';
        }
    }

    async forwardToAIConcierge(phone, message, messageId) {
        try {
            const webhookUrl = process.env.AI_CONCIERGE_WEBHOOK_URL || 'http://localhost:8000/api/v1/webhook';

            // Transform message to WAHA format expected by AI Concierge
            const wahaPayload = {
                event: "message",
                session: this.instanceName,
                payload: {
                    key: {
                        remoteJid: `${phone}@s.whatsapp.net`,
                        id: messageId,
                        fromMe: false
                    },
                    message: {
                        conversation: message
                    },
                    messageTimestamp: Math.floor(Date.now() / 1000),
                    from: phone,
                    id: messageId,
                    timestamp: Math.floor(Date.now() / 1000),
                    hasMedia: false
                }
            };

            const response = await fetch(webhookUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(wahaPayload)
            });

            if (response.ok) {
                const result = await response.json();

                // Send the AI response back to WhatsApp
                if (result.response) {
                    await this.sendMessage(phone, result.response);
                }
            } else {
                console.error('Failed to forward to AI Concierge:', response.statusText);
            }
        } catch (error) {
            console.error('Error forwarding to AI Concierge:', error);
        }
    }

    async sendMessage(phone, message) {
        try {
            if (!this.sock || this.connectionStatus !== 'connected') {
                throw new Error('WhatsApp not connected');
            }

            const jid = phone.includes('@s.whatsapp.net') ? phone : `${phone}@s.whatsapp.net`;

            await this.sock.sendMessage(jid, {
                text: message
            });

            console.log(`📤 Message sent to ${phone}: ${message}`);
        } catch (error) {
            console.error('Error sending message:', error);
            throw error;
        }
    }

    start() {
        this.app.listen(this.port, () => {
            console.log(`🌐 WhatsApp API server running on port ${this.port}`);
            console.log(`📱 QR Code: http://localhost:${this.port}/qrcode`);
            console.log(`🔗 Health Check: http://localhost:${this.port}/health`);
        });
    }
}

// Start the service
const whatsappService = new WhatsAppService();
whatsappService.start();

// Handle graceful shutdown
process.on('SIGINT', () => {
    console.log('\n🛑 Shutting down WhatsApp service...');
    if (whatsappService.sock) {
        whatsappService.sock.end();
    }
    process.exit(0);
});