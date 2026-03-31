#!/usr/bin/env python3
"""Check World Cup Qualification matches today"""
import requests
import datetime

API_KEY = "08c6e6aeaf97abc445440c686ac50fab"
BASE_URL = "https://v3.football.api-sports.io"
headers = {"x-apisports-key": API_KEY}

print("=== МАТЧИ КВАЛИФИКАЦИИ ЧМ СЕГОДНЯ ===\n")

# Get today's fixtures
today = datetime.datetime.now().strftime("%Y-%m-%d")

# Check World Cup Qualification Europe (ID: 32)
print("1. Квалификация ЧМ (Европа, ID: 32):")
params = {"league": 32, "season": 2024, "date": today}
resp = requests.get(f"{BASE_URL}/fixtures", headers=headers, params=params)
if resp.status_code == 200:
    data = resp.json()
    print(f"   Найдено матчей: {data.get('results', 0)}\n")
    for fixture in data.get('response', []):
        home = fixture['teams']['home']['name']
        away = fixture['teams']['away']['name']
        time = fixture['fixture']['date'].split('T')[1][:5]
        venue = fixture['fixture']['venue']['name']
        print(f"   ⚽ {time} | {home} vs {away}")
        print(f"      Стадион: {venue}\n")

# Check all fixtures today and filter for qualifications
print("\n2. Все квалификационные матчи сегодня:")
params = {"date": today}
resp = requests.get(f"{BASE_URL}/fixtures", headers=headers, params=params)
if resp.status_code == 200:
    data = resp.json()
    qual_leagues = {}
    for fixture in data.get('response', []):
        league_name = fixture.get('league', {}).get('name', '').lower()
        if 'qualification' in league_name or 'qualifier' in league_name:
            league_id = fixture['league']['id']
            if league_id not in qual_leagues:
                qual_leagues[league_id] = {
                    'name': fixture['league']['name'],
                    'matches': []
                }
            home = fixture['teams']['home']['name']
            away = fixture['teams']['away']['name']
            time = fixture['fixture']['date'].split('T')[1][:5]
            qual_leagues[league_id]['matches'].append(f"{time} | {home} vs {away}")
    
    for league_id, info in qual_leagues.items():
        print(f"\n   📌 {info['name']} (ID: {league_id}):")
        for match in info['matches'][:10]:  # Show first 10
            print(f"      • {match}")

# Get all available World Cup Qualification leagues
print("\n\n=== ВСЕ ЛИГИ КВАЛИФИКАЦИИ ЧМ В API ===")
qual_search_terms = ["World Cup Qualification", "WC Qualification", "Qualification"]

found_leagues = set()
for term in qual_search_terms:
    params = {"search": term}
    resp = requests.get(f"{BASE_URL}/leagues", headers=headers, params=params)
    if resp.status_code == 200:
        data = resp.json()
        for league in data.get('response', []):
            league_id = league['league']['id']
            if league_id not in found_leagues:
                found_leagues.add(league_id)
                print(f"\n  • {league['league']['name']} (ID: {league_id})")
                print(f"    Страна: {league['country']['name']}")
                seasons = [s['year'] for s in league.get('seasons', []) if s.get('current')]
                print(f"    Текущий сезон: {seasons}")

# Check specific known IDs
print("\n\n=== ПРОВЕРКА КОНКРЕТНЫХ ID ===")
known_qual_ids = [32, 33, 34, 35, 36, 37, 38, 39, 40]  # Common qualification IDs
for league_id in known_qual_ids:
    params = {"id": league_id}
    resp = requests.get(f"{BASE_URL}/leagues", headers=headers, params=params)
    if resp.status_code == 200:
        data = resp.json()
        if data.get('response'):
            league = data['response'][0]
            name = league['league']['name']
            country = league['country']['name']
            seasons = [s['year'] for s in league.get('seasons', []) if s.get('current')]
            print(f"  ID {league_id}: {name} ({country}) - Сезон: {seasons}")
