#!/usr/bin/env python3
"""Seed initial services into Supabase (run once)."""
import os
import requests

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

headers = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

services = [
    {
        "code": "CATECHESE_SJB_DAKAR",
        "title": "Catéchèse St Jean Bosco Dakar",
        "description": "Informations, inscriptions, horaires, documents requis.",
        "keywords": ["catechese", "cathéchèse", "sjb", "bosco", "dakar", "infos"],
        "enabled": True,
        "display_options": "1) Informations sur la catéchèse\n2) Procédure d'inscription\n3) Horaires et lieux\n4) Documents requis",
        "flow": {"default_subservice": "infos"}
    }
]

def main():
    if not SUPABASE_URL or not SERVICE_KEY:
        print("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        return
    url = f"{SUPABASE_URL}/rest/v1/services"
    for s in services:
        r = requests.post(url, headers=headers, json=s, verify=False, timeout=20)
        print(s["code"], r.status_code, r.text)

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    main()

