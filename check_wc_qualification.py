#!/usr/bin/env python3
"""Check World Cup Qualification leagues in API-Football"""
import requests
import os

API_KEY = os.getenv("API_FOOTBALL_KEY", "08c6e6aeaf97abc445440c686ac50fab")
BASE_URL = "https://v3.football.api-sports.io"

headers = {"x-apisports-key": API_KEY}

# Search for World Cup Qualification leagues
print("=== Поиск квалификационных лиг ===\n")

# Test 1: Search by name "World Cup Qualification"
print("1. Поиск по названию 'World Cup Qualification'...")
params = {"search": "World Cup Qualification"}
resp = requests.get(f"{BASE_URL}/leagues", headers=headers, params=params)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"Найдено лиг: {data.get('results', 0)}\n")
    for league in data.get('response', []):
        print(f"  • {league['league']['name']} (ID: {league['league']['id']}, Country: {league['country']['name']})")
        print(f"    Seasons: {[s['year'] for s in league.get('seasons', [])]}")
        print()

# Test 2: Search for "WC Qualification"
print("\n2. Поиск по названию 'WC Qualification'...")
params = {"search": "WC Qualification"}
resp = requests.get(f"{BASE_URL}/leagues", headers=headers, params=params)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"Найдено лиг: {data.get('results', 0)}\n")
    for league in data.get('response', []):
        print(f"  • {league['league']['name']} (ID: {league['league']['id']}, Country: {league['country']['name']})")
        print(f"    Seasons: {[s['year'] for s in league.get('seasons', [])]}")
        print()

# Test 3: Check UEFA qualifiers specifically
print("\n3. Поиск по названию 'UEFA'...")
params = {"search": "UEFA"}
resp = requests.get(f"{BASE_URL}/leagues", headers=headers, params=params)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"Найдено лиг: {data.get('results', 0)}\n")
    for league in data.get('response', []):
        print(f"  • {league['league']['name']} (ID: {league['league']['id']}, Country: {league['country']['name']})")
        print(f"    Seasons: {[s['year'] for s in league.get('seasons', [])]}")
        print()

# Test 4: Check specific known qualification league IDs
print("\n4. Проверка известных ID квалификаций:")
known_ids = {
    "UEFA Group C": 32,  # World Cup Qualification UEFA
    "UEFA Nations League": 5,
    "World Cup": 1,
}

for name, league_id in known_ids.items():
    params = {"id": league_id}
    resp = requests.get(f"{BASE_URL}/leagues", headers=headers, params=params)
    if resp.status_code == 200:
        data = resp.json()
        if data.get('response'):
            league = data['response'][0]
            print(f"\n  {name} (ID: {league_id}):")
            print(f"    Полное название: {league['league']['name']}")
            print(f"    Страна: {league['country']['name']}")
            print(f"    Seasons: {[s['year'] for s in league.get('seasons', []) if s.get('current')]}")

# Test 5: Get today's fixtures to see what's available
print("\n\n=== МАТЧИ СЕГОДНЯ (проверка на квалификацию ЧМ) ===")
import datetime
today = datetime.datetime.now().strftime("%Y-%m-%d")
params = {"date": today}
resp = requests.get(f"{BASE_URL}/fixtures", headers=headers, params=params)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"Всего матчей сегодня: {data.get('results', 0)}\n")
    
    wc_qual_matches = []
    for fixture in data.get('response', [])[:20]:  # First 20
        league_name = fixture.get('league', {}).get('name', '')
        if 'qualif' in league_name.lower() or 'world cup' in league_name.lower():
            wc_qual_matches.append(fixture)
            home = fixture['teams']['home']['name']
            away = fixture['teams']['away']['name']
            time = fixture['fixture']['date'].split('T')[1][:5]
            print(f"  ⚽ {time} | {home} vs {away}")
            print(f"     Лига: {league_name} (ID: {fixture['league']['id']})")
            print()
    
    if not wc_qual_matches:
        print("  Матчей квалификации ЧМ сегодня не найдено")
        print("\n  Все лиги сегодня:")
        seen_leagues = set()
        for fixture in data.get('response', [])[:30]:
            league = fixture.get('league', {})
            league_key = f"{league['name']} ({league['id']})"
            if league_key not in seen_leagues:
                print(f"    • {league['name']} (ID: {league['id']}, Country: {league['country']['name']})")
                seen_leagues.add(league_key)
