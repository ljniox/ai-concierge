#!/usr/bin/env python3
"""
Debug script to test phone number extraction from webhook data
"""

import asyncio
import requests
import json
import logging

# Test webhook data structure (from the logs)
test_webhook_data = {
    'id': 'evt_01k52a0xmxk8084571qwjps625',
    'timestamp': 1757792990879,
    'event': 'message',
    'session': 'default',
    'me': {
        'id': '221773387902@c.us',
        'pushName': '\u200eJameservices',
        'lid': '217394232447137:2@lid'
    },
    'payload': {
        'id': 'false_221765005555@c.us_3A874063255DD1BCB135',
        'timestamp': 1757792990,
        'from': '221765005555@c.us',
        'fromMe': False,
        'source': 'app',
        'body': 'Test',
        'hasMedia': False,
        'media': {
            'key': {
                'remoteJid': '221765005555@s.whatsapp.net',
                'fromMe': False,
                'id': '3A874063255DD1BCB135',
                'senderLid': '58119531020472@lid'
            },
            'messageTimestamp': 1757792990,
            'pushName': 'James',
            'broadcast': False,
            'message': {
                'conversation': 'Test',
                'messageContextInfo': {
                    'deviceListMetadata': {
                        'senderKeyHash': 'y7hNXXnRCggj0A==',
                        'senderTimestamp': '1757413441',
                        'recipientKeyHash': 'X7v/4Wmcqb0G0Q==',
                        'recipientTimestamp': '1757544604'
                    },
                    'deviceListMetadataVersion': 2,
                    'messageSecret': 'PIceoIy4QEa1wmHkdHSVXIK/h+DaMDbx/925pBrlk3s='
                }
            },
            'status': 3
        },
        'ack': 2,
        'ackName': 'DEVICE',
        'replyTo': None,
        '_data': {
            'key': {
                'remoteJid': '221765005555@s.whatsapp.net',
                'fromMe': False,
                'id': '3A874063255DD1BCB135',
                'senderLid': '58119531020472@lid'
            },
            'messageTimestamp': 1757792990,
            'pushName': 'James',
            'broadcast': False,
            'message': {
                'conversation': 'Test',
                'messageContextInfo': {
                    'deviceListMetadata': {
                        'senderKeyHash': 'y7hNXXnRCggj0A==',
                        'senderTimestamp': '1757413441',
                        'recipientKeyHash': 'X7v/4Wmcqb0G0Q==',
                        'recipientTimestamp': '1757544604'
                    },
                    'deviceListMetadataVersion': 2,
                    'messageSecret': 'PIceoIy4QEa1wmHkdHSVXIK/h+DaMDbx/925pBrlk3s='
                }
            },
            'status': 3
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

def test_phone_extraction():
    """Test different phone number extraction methods"""
    print("🔍 Testing phone number extraction methods:")
    print("=" * 50)

    # Method 1: Original (broken)
    from_number_1 = test_webhook_data.get('from', '').replace('@c.us', '').replace('@s.whatsapp.net', '')
    print(f"Method 1 (original): '{from_number_1}'")

    # Method 2: Fixed version
    payload = test_webhook_data.get('payload', {})
    from_number_2 = payload.get('from', '').replace('@c.us', '').replace('@s.whatsapp.net', '')
    print(f"Method 2 (fixed): '{from_number_2}'")

    # Method 3: Direct from payload
    from_number_3 = test_webhook_data['payload']['from'].replace('@c.us', '').replace('@s.whatsapp.net', '')
    print(f"Method 3 (direct): '{from_number_3}'")

    # Test chatId formats
    print("\n📱 ChatId format testing:")
    print(f"Raw from field: '{test_webhook_data['payload']['from']}'")
    print(f"Cleaned number: '{from_number_3}'")
    print(f"WhatsApp format: '{from_number_3}@c.us'")

    return from_number_3

if __name__ == "__main__":
    result = test_phone_extraction()
    print(f"\n✅ Extracted phone number: {result}")

    if result:
        print("🎉 Phone number extraction works!")
    else:
        print("❌ Phone number extraction failed!")