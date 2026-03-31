#!/usr/bin/env python3
"""Debug national team fixtures"""
import requests
import datetime

API_KEY = "08c6e6aeaf97abc445440c686ac50fab"
BASE_URL = "https://v3.football.api-sports.io"
headers = {"x-apisports-key": API_KEY}

print("=== Поиск матчей национальных сборных ===\n")

# Test 1: Get fixtures by team ID with different parameters
print("1. Sweden fixtures с параметром season:")
for season in [2024, 2025, 2026]:
    params = {"team": 5, "season": season}
    resp = requests.get(f"{BASE_URL}/fixtures", headers=headers, params=params)
    if resp.status_code == 200:
        data = resp.json()
        count = data.get('results', 0)
        if count > 0:
            print(f"   Сезон {season}: {count} матчей")

# Test 2: Get fixtures by date range
print("\n2. Sweden fixtures с параметром date range:")
today = datetime.datetime.now().strftime("%Y-%m-%d")
year_ago = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
next_year = (datetime.datetime.now() + datetime.timedelta(days=365)).strftime("%Y-%m-%d")

params = {"team": 5, "from": year_ago, "to": next_year}
resp = requests.get(f"{BASE_URL}/fixtures", headers=headers, params=params)
if resp.status_code == 200:
    data = resp.json()
    print(f"   За последний год и следующий: {data.get('results', 0)} матчей")
    for fixture in data.get('response', [])[:5]:
        date = fixture['fixture']['date'][:10]
        home = fixture['teams']['home']['name']
        away = fixture['teams']['away']['name']
        league = fixture['league']['name']
        print(f"   {date}: {home} vs {away} ({league})")

# Test 3: Check what leagues Sweden plays in
print("\n3. League fixtures for Sweden (WC Qualification):")
params = {"league": 32, "season": 2024}
resp = requests.get(f"{BASE_URL}/fixtures", headers=headers, params=params)
if resp.status_code == 200:
    data = resp.json()
    print(f"   Матчей в квалификации ЧМ: {data.get('results', 0)}")
    sweden_matches = [f for f in data.get('response', []) 
                      if f['teams']['home']['id'] == 5 or f['teams']['away']['id'] == 5]
    print(f"   Матчей Sweden: {len(sweden_matches)}")
    for fixture in sweden_matches[:5]:
        date = fixture['fixture']['date'][:10]
        home = fixture['teams']['home']['name']
        away = fixture['teams']['away']['name']
        print(f"   {date}: {home} vs {away}")

# Test 4: Check if team endpoint works with league parameter
print("\n4. Sweden fixtures с league + team:")
params = {"team": 5, "league": 32, "season": 2024}
resp = requests.get(f"{BASE_URL}/fixtures", headers=headers, params=params)
if resp.status_code == 200:
    data = resp.json()
    print(f"   Найдено матчей: {data.get('results', 0)}")

# Test 5: Try with country parameter
print("\n5. Поиск по стране 'Sweden':")
params = {"country": "Sweden"}
resp = requests.get(f"{BASE_URL}/teams", headers=headers, params=params)
if resp.status_code == 200:
    data = resp.json()
    print(f"   Найдено команд: {data.get('results', 0)}")
    for team in data.get('response', [])[:3]:
        print(f"   • {team['team']['name']} (ID: {team['team']['id']})")
