#!/usr/bin/env python3
"""Debug WC Qualification display in bot"""
import sys
sys.path.insert(0, '/Users/ilyailyx/Desktop/sports-analytics-bot')

from api_football_parser import APIFootballParser
import datetime

parser = APIFootballParser(api_key="08c6e6aeaf97abc445440c686ac50fab")

print("=== Отладка отображения квалификации ЧМ ===\n")

# Check what date it is
today = datetime.date.today()
print(f"Сегодня: {today.strftime('%d.%m.%Y (%A)')}")
print(f"ISO date: {today.strftime('%Y-%m-%d')}\n")

# Test 1: Check get_fixtures_by_date for wc_qual_europe
print("1. get_fixtures_by_date('wc_qual_europe', days=30):")
matches_data = parser.get_fixtures_by_date("wc_qual_europe", days=30)
print(f"   Найдено дат: {len(matches_data)}")

for date_str, matches in list(matches_data.items())[:5]:
    print(f"\n   📅 {date_str}: {len(matches)} матчей")
    for match in matches[:3]:
        print(f"      • {match.home_team} vs {match.away_team}")

# Test 2: Check if today's date is in the data
print(f"\n\n2. Поиск матчей на сегодня ({today.strftime('%d.%m.%Y')}):")
today_display = today.strftime("%d.%m.%Y (%A)")
found_today = False
for date_str, matches in matches_data.items():
    if today.strftime("%d.%m") in date_str:
        print(f"   ✅ Найдено: {date_str}")
        print(f"   Матчей: {len(matches)}")
        for match in matches:
            print(f"      • {match.home_team} vs {match.away_team}")
        found_today = True
        break

if not found_today:
    print(f"   ❌ Матчей на сегодня не найдено")
    print(f"\n   Доступные даты в кэше:")
    for date_str in list(matches_data.keys())[:10]:
        print(f"      • {date_str}")

# Test 3: Check cache
print(f"\n\n3. Проверка кэша:")
cache_key = f"wc_qual_europe_2024"
if cache_key in parser._season_cache:
    cache_time, cached_fixtures = parser._season_cache[cache_key]
    print(f"   ✅ Кэш найден: {len(cached_fixtures)} матчей")
    print(f"   Время кэша: {datetime.datetime.fromtimestamp(cache_time)}")
    
    # Check match dates
    print(f"\n   Даты матчей в кэше:")
    date_counts = {}
    for match in cached_fixtures:
        try:
            if isinstance(match.date, int):
                match_dt = datetime.datetime.fromtimestamp(match.date)
            else:
                match_dt = datetime.datetime.fromisoformat(str(match.date).replace('Z', '+00:00'))
            date_key = match_dt.strftime("%d.%m.%Y")
            if date_key not in date_counts:
                date_counts[date_key] = 0
            date_counts[date_key] += 1
        except:
            pass
    
    # Show dates around today
    for date_key in sorted(date_counts.keys()):
        if today.strftime("%d.%m") in date_key or (today - datetime.timedelta(days=1)).strftime("%d.%m") in date_key or (today + datetime.timedelta(days=1)).strftime("%d.%m") in date_key:
            print(f"      {date_key}: {date_counts[date_key]} матчей")
else:
    print(f"   ❌ Кэш не найден")

# Test 4: Direct API query for today
print(f"\n\n4. Прямой запрос к API на сегодня:")
import requests
params = {"date": today.strftime("%Y-%m-%d"), "league": 32, "season": 2024}
resp = requests.get("https://v3.football.api-sports.io/fixtures", 
                    headers={"x-apisports-key": "08c6e6aeaf97abc445440c686ac50fab"}, 
                    params=params)
if resp.status_code == 200:
    data = resp.json()
    print(f"   Status: {data.get('results', 0)} матчей")
    for fixture in data.get('response', []):
        home = fixture['teams']['home']['name']
        away = fixture['teams']['away']['name']
        status = fixture['fixture']['status']['long']
        time = fixture['fixture']['date'].split('T')[1][:5]
        print(f"   ⚽ {time} | {home} vs {away} | {status}")
