#!/usr/bin/env python3
"""Debug fixture API call"""
import requests

API_KEY = "08c6e6aeaf97abc445440c686ac50fab"
BASE_URL = "https://v3.football.api-sports.io"
headers = {"x-apisports-key": API_KEY}

match_id = "1537581"
print(f"API запрос: /fixtures?id={match_id}\n")

params = {"id": match_id}
resp = requests.get(f"{BASE_URL}/fixtures", headers=headers, params=params)

print(f"Status: {resp.status_code}")
print(f"Response: {resp.json()}")
