#!/usr/bin/env python3
"""Check available seasons for all leagues"""
import requests

API_KEY = "08c6e6aeaf97abc445440c686ac50fab"
BASE_URL = "https://v3.football.api-sports.io"
headers = {"x-apisports-key": API_KEY}

leagues = {
    "premier_league": 39,
    "wc_qual_europe": 32,
    "champions_league": 2,
}

print("=== Доступные сезоны для лиг ===\n")

for name, league_id in leagues.items():
    params = {"id": league_id}
    resp = requests.get(f"{BASE_URL}/leagues", headers=headers, params=params)
    
    if resp.status_code == 200:
        data = resp.json()
        if data.get('response'):
            league = data['response'][0]
            seasons = league.get('seasons', [])
            current = [s['year'] for s in seasons if s.get('current')]
            
            print(f"{name} (ID: {league_id}):")
            print(f"   Все сезоны: {[s['year'] for s in seasons]}")
            print(f"   Текущий: {current}")
            print()
