#!/usr/bin/env python3
"""Check all WC qualification seasons"""
import requests

API_KEY = "08c6e6aeaf97abc445440c686ac50fab"
BASE_URL = "https://v3.football.api-sports.io"
headers = {"x-apisports-key": API_KEY}

leagues = {
    "wc_qual_europe": 32,
    "wc_qual_concacaf": 31,
    "wc_qual_south_america": 34,
    "wc_qual_asia": 30,
    "wc_qual_africa": 29,
    "wc_qual_oceania": 33,
    "wc_qual_playoffs": 37,
}

print("=== Сезоны квалификаций ЧМ ===\n")

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
            print(f"   Сезоны: {[s['year'] for s in seasons]}")
            print(f"   Текущий: {current}")
            
            # Fix: use correct season
            if current:
                correct_season = current[0]
            else:
                correct_season = seasons[-1]['year'] if seasons else 'N/A'
            print(f"   ✅ Использовать сезон: {correct_season}")
            print()
