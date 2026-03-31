#!/usr/bin/env python3
"""Force refresh and test WC Qualification"""
import sys
import os
sys.path.insert(0, '/Users/ilyailyx/Desktop/sports-analytics-bot')

# Force reload modules
if 'api_football_parser' in sys.modules:
    del sys.modules['api_football_parser']
if 'main' in sys.modules:
    del sys.modules['main']

from api_football_parser import APIFootballParser
import datetime
import re

print("=" * 70)
print("🔄 ПРИНУДИТЕЛЬНОЕ ОБНОВЛЕНИЕ КЭША")
print("=" * 70)

parser = APIFootballParser(api_key="08c6e6aeaf97abc445440c686ac50fab")

# Clear all cache
print("\n1. Очистка всего кэша...")
parser._season_cache.clear()
print(f"   ✅ Кэш очищен: {len(parser._season_cache)} записей")

# Pre-load WC Qualification Europe
print("\n2. Предзагрузка квалификации ЧМ (Европа)...")
matches_data = parser.get_fixtures_by_date("wc_qual_europe", days=30)
print(f"   ✅ Загружено {len(matches_data)} дат")

# Check today
today = datetime.date.today()
today_str = today.strftime("%Y-%m-%d")
today_display = today.strftime("%d.%m.%Y (%A)")

print(f"\n3. Проверка на сегодня ({today_display}):")

today_matches = []
for date_key, matches in matches_data.items():
    if today_str in date_key or today.strftime("%d.%m") in date_key:
        today_matches = matches
        break

if len(today_matches) > 0:
    print(f"   ✅ НАЙДЕНО {len(today_matches)} МАТЧЕЙ!")
    for match in today_matches:
        print(f"      ⚽ {match.home_team} vs {match.away_team}")
else:
    print(f"   ❌ Матчей не найдено")
    
    # Show available dates
    print(f"\n   Доступные даты:")
    for dk in sorted(matches_data.keys())[:10]:
        print(f"      • {dk}")

# Test bot logic
print("\n\n" + "=" * 70)
print("🤖 ТЕСТ ЛОГИКИ БОТА")
print("=" * 70)

all_matches_by_date = {}
leagues_to_check = [
    "premier_league", "la_liga", "bundesliga", "serie_a", "ligue_1",
    "champions_league", "europa_league",
    "eredivisie", "primeira_liga", "mls", "brasileirao",
    "wc_qual_europe", "wc_qual_concacaf", "wc_qual_south_america",
    "wc_qual_asia", "wc_qual_africa", "wc_qual_oceania", "wc_qual_playoffs",
]

print("\nЗагрузка матчей для всех лиг...")
for league in leagues_to_check:
    matches_data = parser.get_fixtures_by_date(league, days=14)
    for date_display, matches in matches_data.items():
        if date_display not in all_matches_by_date:
            all_matches_by_date[date_display] = 0
        all_matches_by_date[date_display] += len(matches)

print(f"   ✅ Загружено {len(all_matches_by_date)} дней с матчами")

# Create date_counts
date_counts = {}
for date_display, count in all_matches_by_date.items():
    date_match = re.match(r"(\d{2}\.\d{2}\.\d{4})", date_display)
    if date_match:
        dmy = date_match.group(1)
        try:
            dt = datetime.datetime.strptime(dmy, "%d.%m.%Y")
            iso_date = dt.strftime("%Y-%m-%d")
            date_counts[iso_date] = count
        except:
            pass

# Show buttons
print(f"\n🔘 Кнопки дат (как в боте):")
for i in range(7):
    target_date = today + datetime.timedelta(days=i)
    date_str = target_date.strftime("%Y-%m-%d")
    match_count = date_counts.get(date_str, 0)
    
    if i == 0:
        label = "Сегодня"
    elif i == 1:
        label = "Завтра"
    else:
        label = target_date.strftime("%d.%m")
    
    status = "✅" if match_count > 0 else "❌"
    print(f"   {status} {label} ({match_count})")

print("\n" + "=" * 70)
if date_counts.get(today_str, 0) > 0:
    print(f"✅ ВСЁ РАБОТАЕТ! Бот покажет 'Сегодня ({date_counts[today_str]})'")
else:
    print(f"❌ ПРОБЛЕМА! Бот покажет 'Сегодня (0)'")
print("=" * 70)
