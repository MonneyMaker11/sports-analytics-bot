#!/usr/bin/env python3
"""Check today's WC qualification matches"""
import requests
import datetime

API_KEY = "08c6e6aeaf97abc445440c686ac50fab"
BASE_URL = "https://v3.football.api-sports.io"
headers = {"x-apisports-key": API_KEY}

today = datetime.datetime.now().strftime("%Y-%m-%d")

leagues = {
    "wc_qual_europe": (32, 2024),
    "wc_qual_concacaf": (31, 2026),
    "wc_qual_south_america": (34, 2026),
    "wc_qual_asia": (30, 2026),
    "wc_qual_africa": (29, 2023),
    "wc_qual_oceania": (33, 2026),
    "wc_qual_playoffs": (37, 2026),
}

print(f"=== Матчи квалификаций ЧМ на сегодня ({today}) ===\n")

for name, (league_id, season) in leagues.items():
    params = {"league": league_id, "season": season, "date": today}
    resp = requests.get(f"{BASE_URL}/fixtures", headers=headers, params=params)
    
    if resp.status_code == 200:
        data = resp.json()
        count = data.get('results', 0)
        status = "✅" if count > 0 else "❌"
        print(f"{status} {name}: {count} матчей")
        
        if count > 0:
            for fixture in data.get('response', [])[:3]:
                home = fixture['teams']['home']['name']
                away = fixture['teams']['away']['name']
                time = fixture['fixture']['date'].split('T')[1][:5]
                print(f"      ⚽ {time} | {home} vs {away}")
