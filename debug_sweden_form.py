#!/usr/bin/env python3
"""Debug Sweden form with season parameter"""
import requests

API_KEY = "08c6e6aeaf97abc445440c686ac50fab"
BASE_URL = "https://v3.football.api-sports.io"
headers = {"x-apisports-key": API_KEY}

print("=== Sweden form с season параметром ===\n")

# Test with season only (no last)
params = {"team": 5, "season": 2024}
resp = requests.get(f"{BASE_URL}/fixtures", headers=headers, params=params)
print(f"1. fixtures?team=5&season=2024")
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"   Results: {data.get('results', 0)}")
    for fixture in data.get('response', [])[:5]:
        date = fixture['fixture']['date'][:10]
        home = fixture['teams']['home']['name']
        away = fixture['teams']['away']['name']
        league = fixture['league']['name']
        print(f"   {date}: {home} vs {away} ({league})")

# Test with league + season
print("\n\n2. fixtures?team=5&league=32&season=2024 (WC Qualification)")
params = {"team": 5, "league": 32, "season": 2024}
resp = requests.get(f"{BASE_URL}/fixtures", headers=headers, params=params)
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"   Results: {data.get('results', 0)}")
    for fixture in data.get('response', []):
        date = fixture['fixture']['date'][:10]
        home = fixture['teams']['home']['name']
        away = fixture['teams']['away']['name']
        print(f"   {date}: {home} vs {away}")

# Test with league 5 (UEFA Nations League)
print("\n\n3. fixtures?team=5&league=5&season=2024 (Nations League)")
params = {"team": 5, "league": 5, "season": 2024}
resp = requests.get(f"{BASE_URL}/fixtures", headers=headers, params=params)
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"   Results: {data.get('results', 0)}")
    for fixture in data.get('response', [])[:5]:
        date = fixture['fixture']['date'][:10]
        home = fixture['teams']['home']['name']
        away = fixture['teams']['away']['name']
        print(f"   {date}: {home} vs {away}")

# Test all leagues for Sweden 2024
print("\n\n4. fixtures?team=5&season=2024 (ALL leagues)")
params = {"team": 5, "season": 2024}
resp = requests.get(f"{BASE_URL}/fixtures", headers=headers, params=params)
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"   Results: {data.get('results', 0)}")
    for fixture in data.get('response', [])[:10]:
        date = fixture['fixture']['date'][:10]
        home = fixture['teams']['home']['name']
        away = fixture['teams']['away']['name']
        league = fixture['league']['name']
        print(f"   {date}: {home} vs {away} ({league})")
