#!/usr/bin/env python3
"""
Manual test of auto-reply functionality
"""

import asyncio
from auto_reply_service import auto_reply_service
from auto_reply_config import auto_reply_config

# Test webhook data (simulating real WAHA webhook)
test_webhook_data = {
    'id': 'evt_01k52as4sv2vssjncnz17x77ta',
    'timestamp': 1757793784637,
    'event': 'message',
    'session': 'default',
    'me': {
        'id': '221773387902@c.us',
        'pushName': '\u200eJameservices',
        'lid': '217394232447137:2@lid'
    },
    'payload': {
        'id': 'false_221765005555@c.us_3A1736EC0F71B53A0CCF',
        'timestamp': 1757793784,
        'from': '221765005555@c.us',
        'fromMe': False,
        'source': 'app',
        'body': 'bonjour test',
        'hasMedia': False,
        'media': {
            'key': {
                'remoteJid': '221765005555@s.whatsapp.net',
                'fromMe': False,
                'id': '3A1736EC0F71B53A0CCF',
                'senderLid': '58119531020472@lid'
            },
            'messageTimestamp': 1757793784,
            'pushName': 'James',
            'broadcast': False,
            'message': {
                'conversation': 'bonjour test',
                'messageContextInfo': {
                    'deviceListMetadata': {
                        'senderKeyHash': 'y7hNXXnRCggj0A==',
                        'senderTimestamp': '1757413441',
                        'recipientKeyHash': 'X7v/4Wmcqb0G0Q==',
                        'recipientTimestamp': '1757544604'
                    },
                    'deviceListMetadataVersion': 2,
                    'messageSecret': 'DEbCIXIvVPuVy29Odp87solRtmID7ZKoUSRrfIMSCOA='
                },
                'status': 3
            }
        },
        'ack': 2,
        'ackName': 'DEVICE',
        'replyTo': None,
        '_data': {
            'key': {
                'remoteJid': '221765005555@s.whatsapp.net',
                'fromMe': False,
                'id': '3A1736EC0F71B53A0CCF',
                'senderLid': '58119531020472@lid'
            },
            'messageTimestamp': 1757793784,
            'pushName': 'James',
            'broadcast': False,
            'message': {
                'conversation': 'bonjour test',
                'messageContextInfo': {
                    'deviceListMetadata': {
                        'senderKeyHash': 'y7hNXXnRCggj0A==',
                        'senderTimestamp': '1757413441',
                        'recipientKeyHash': 'X7v/4Wmcqb0G0Q==',
                        'recipientTimestamp': '1757544604'
                    },
                    'deviceListMetadataVersion': 2,
                    'messageSecret': 'DEbCIXIvVPuVy29Odp87solRtmID7ZKoUSRrfIMSCOA='
                },
                'status': 3
            }
        }
    },
    'engine': 'NOWEB',
    'environment': {
        'version': '2025.9.2',
        'engine': 'NOWEB',
        'tier': 'CORE',
        'browser': None
    }
}

async def test_auto_reply():
    """Test auto-reply functionality"""
    print("🧪 Testing auto-reply functionality...")
    print("=" * 50)

    # Test 1: Check if we should reply
    print("📋 Test 1: Should reply check")
    should_reply = auto_reply_config.should_reply(test_webhook_data)
    print(f"Should reply: {should_reply}")

    # Test 2: Test phone number extraction
    print("\n📱 Test 2: Phone number extraction")
    payload = test_webhook_data.get('payload', {})
    raw_from = payload.get('from', '')
    media = payload.get('media', {})
    remote_jid = media.get('key', {}).get('remoteJid', '') if isinstance(media, dict) else ''

    print(f"Raw from: '{raw_from}'")
    print(f"Remote JID: '{remote_jid}'")

    if remote_jid:
        from_number = remote_jid.replace('@c.us', '').replace('@s.whatsapp.net', '')
        print(f"Extracted from remoteJid: '{from_number}'")
    else:
        from_number = raw_from.replace('@c.us', '').replace('@s.whatsapp.net', '')
        print(f"Extracted from from field: '{from_number}'")

    # Test 3: Test message extraction
    print("\n💬 Test 3: Message extraction")
    message_text = test_webhook_data['payload']['body']
    print(f"Message text: '{message_text}'")

    # Test 4: Test reply message generation
    print("\n🤖 Test 4: Reply message generation")
    reply_text = auto_reply_config.get_reply_message(message_text)
    print(f"Reply text: '{reply_text}'")

    # Test 5: Try to send actual reply
    print("\n📤 Test 5: Sending actual reply")
    try:
        success = await auto_reply_service.send_reply(test_webhook_data)
        print(f"Reply sent successfully: {success}")
    except Exception as e:
        print(f"Error sending reply: {e}")

if __name__ == "__main__":
    asyncio.run(test_auto_reply())