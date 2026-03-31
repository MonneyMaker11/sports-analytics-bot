#!/usr/bin/env python3
"""Debug team form for WC Qualification teams"""
import requests
import logging

logging.basicConfig(level=logging.INFO)

API_KEY = "08c6e6aeaf97abc445440c686ac50fab"
BASE_URL = "https://v3.football.api-sports.io"
headers = {"x-apisports-key": API_KEY}

# Sweden team ID = 5, Poland team ID = 24
print("=== Проверка формы команд квалификации ЧМ ===\n")

# Test 1: Get Sweden's last matches
print("1. Форма Sweden (ID: 5):")
params = {"team": 5, "last": 10}
resp = requests.get(f"{BASE_URL}/fixtures/team", headers=headers, params=params)
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"   Найдено матчей: {data.get('results', 0)}\n")
    for fixture in data.get('response', [])[:5]:
        teams = fixture.get('teams', {})
        goals = fixture.get('goals', {})
        home_team = teams['home']['name']
        away_team = teams['away']['name']
        home_goals = goals.get('home', '-')
        away_goals = goals.get('away', '-')
        
        # Determine result for Sweden
        is_home = teams['home']['id'] == 5
        if is_home:
            sweden_goals = home_goals
            opp_goals = away_goals
            opponent = away_team
        else:
            sweden_goals = away_goals
            opp_goals = home_goals
            opponent = home_team
        
        if sweden_goals > opp_goals:
            result = 'W'
        elif sweden_goals < opp_goals:
            result = 'L'
        else:
            result = 'D'
        
        print(f"   {result} vs {opponent}: {home_goals}-{away_goals}")

# Test 2: Get Poland's last matches
print("\n\n2. Форма Poland (ID: 24):")
params = {"team": 24, "last": 10}
resp = requests.get(f"{BASE_URL}/fixtures/team", headers=headers, params=params)
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"   Найдено матчей: {data.get('results', 0)}\n")
    for fixture in data.get('response', [])[:5]:
        teams = fixture.get('teams', {})
        goals = fixture.get('goals', {})
        home_team = teams['home']['name']
        away_team = teams['away']['name']
        home_goals = goals.get('home', '-')
        away_goals = goals.get('away', '-')
        
        # Determine result for Poland
        is_home = teams['home']['id'] == 24
        if is_home:
            poland_goals = home_goals
            opp_goals = away_goals
            opponent = away_team
        else:
            poland_goals = away_goals
            opp_goals = home_goals
            opponent = home_team
        
        if poland_goals > opp_goals:
            result = 'W'
        elif poland_goals < opp_goals:
            result = 'L'
        else:
            result = 'D'
        
        print(f"   {result} vs {opponent}: {home_goals}-{away_goals}")

# Test 3: Get H2H between Sweden and Poland
print("\n\n3. H2H Sweden vs Poland:")
params = {"h2h": "5-24", "last": 5}
resp = requests.get(f"{BASE_URL}/fixtures/headtohead", headers=headers, params=params)
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"   Найдено матчей: {data.get('results', 0)}\n")
    for fixture in data.get('response', []):
        home = fixture['teams']['home']['name']
        away = fixture['teams']['away']['name']
        home_score = fixture['goals']['home']
        away_score = fixture['goals']['away']
        date = fixture['fixture']['date'][:10]
        print(f"   {date}: {home} {home_score}-{away_score} {away}")
