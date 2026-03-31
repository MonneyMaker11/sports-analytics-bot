#!/usr/bin/env python3
"""Check real today's date and WC qualification matches"""
import requests
import datetime

API_KEY = "08c6e6aeaf97abc445440c686ac50fab"
BASE_URL = "https://v3.football.api-sports.io"
headers = {"x-apisports-key": API_KEY}

# Get real current date
real_today = datetime.datetime.now()
print(f"📅 РЕАЛЬНАЯ СЕГОДНЯШНЯЯ ДАТА: {real_today.strftime('%Y-%m-%d %A')}")
print(f"   Timestamp: {real_today.timestamp()}\n")

# Check matches for real today
today_str = real_today.strftime("%Y-%m-%d")

print(f"=== Матчи квалификации ЧМ на {today_str} ===\n")

# Check all WC qualification leagues
leagues = {
    "wc_qual_europe": (32, 2024),
    "wc_qual_concacaf": (31, 2026),
    "wc_qual_south_america": (34, 2026),
    "wc_qual_asia": (30, 2026),
    "wc_qual_africa": (29, 2023),
    "wc_qual_oceania": (33, 2026),
    "wc_qual_playoffs": (37, 2026),
}

total_matches = 0
matches_by_league = {}

for name, (league_id, season) in leagues.items():
    params = {"league": league_id, "season": season, "date": today_str}
    resp = requests.get(f"{BASE_URL}/fixtures", headers=headers, params=params)
    
    if resp.status_code == 200:
        data = resp.json()
        count = data.get('results', 0)
        total_matches += count
        
        if count > 0:
            matches_by_league[name] = []
            for fixture in data.get('response', []):
                home = fixture['teams']['home']['name']
                away = fixture['teams']['away']['name']
                time = fixture['fixture']['date'].split('T')[1][:5]
                status = fixture['fixture']['status']['short']
                matches_by_league[name].append({
                    'home': home,
                    'away': away,
                    'time': time,
                    'status': status,
                    'id': fixture['fixture']['id']
                })

if total_matches > 0:
    print(f"✅ ВСЕГО МАТЧЕЙ: {total_matches}\n")
    for league, matches in matches_by_league.items():
        print(f"📌 {league}: {len(matches)} матчей")
        for m in matches:
            print(f"   ⚽ {m['time']} | {m['home']} vs {m['away']} ({m['status']})")
else:
    print("❌ НА СЕГОДНЯ МАТЧЕЙ НЕТ")
    
    # Check next 7 days
    print("\n📅 Проверка следующих 7 дней:")
    for i in range(7):
        check_date = real_today + datetime.timedelta(days=i)
        check_str = check_date.strftime("%Y-%m-%d")
        
        for name, (league_id, season) in [("wc_qual_europe", (32, 2024))]:
            params = {"league": league_id, "season": season, "date": check_str}
            resp = requests.get(f"{BASE_URL}/fixtures", headers=headers, params=params)
            
            if resp.status_code == 200:
                data = resp.json()
                count = data.get('results', 0)
                if count > 0:
                    print(f"\n   ✅ {check_date.strftime('%d.%m.%Y %A')} ({name}): {count} матчей")
                    for fixture in data.get('response', [])[:3]:
                        home = fixture['teams']['home']['name']
                        away = fixture['teams']['away']['name']
                        time = fixture['fixture']['date'].split('T')[1][:5]
                        print(f"      ⚽ {time} | {home} vs {away}")
                    break
