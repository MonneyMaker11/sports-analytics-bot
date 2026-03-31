#!/usr/bin/env python3
"""
Проверка, что квалификации ЧМ работают в боте.
Запустите этот скрипт, чтобы убедиться, что всё настроено правильно.
"""
import sys
sys.path.insert(0, '/Users/ilyailyx/Desktop/sports-analytics-bot')

from api_football_parser import APIFootballParser
import datetime
import re

print("=" * 70)
print("🔍 ПРОВЕРКА: Квалификация ЧМ в боте")
print("=" * 70)

parser = APIFootballParser(api_key="08c6e6aeaf97abc445440c686ac50fab")
today = datetime.date.today()

# 1. Проверка LEAGUE_IDS
print("\n1. Проверка LEAGUE_IDS в api_football_parser.py:")
expected_leagues = [
    "wc_qual_europe", "wc_qual_concacaf", "wc_qual_south_america",
    "wc_qual_asia", "wc_qual_africa", "wc_qual_oceania", "wc_qual_playoffs",
]

all_present = True
for league in expected_leagues:
    if league in parser.LEAGUE_IDS:
        print(f"   ✅ {league}: ID {parser.LEAGUE_IDS[league]}")
    else:
        print(f"   ❌ {league}: НЕ НАЙДЕН!")
        all_present = False

if not all_present:
    print("\n❌ ОШИБКА: Не все лиги добавлены в LEAGUE_IDS!")
    sys.exit(1)

# 2. Проверка данных квалификации
print("\n2. Проверка данных квалификации ЧМ (Европа):")
matches_data = parser.get_fixtures_by_date("wc_qual_europe", days=30)
print(f"   Найдено дат: {len(matches_data)}")

# Проверка сегодня
today_str = today.strftime("%Y-%m-%d")
today_display = today.strftime("%d.%m.%Y (%A)")

today_matches = []
for date_key, matches in matches_data.items():
    if today_str in date_key or today.strftime("%d.%m") in date_key:
        today_matches = matches
        break

print(f"   Матчей сегодня ({today_display}): {len(today_matches)}")

if len(today_matches) > 0:
    print(f"\n   📋 Матчи на сегодня:")
    for match in today_matches:
        print(f"      ⚽ {match.home_team} vs {match.away_team}")
        print(f"         ID: {match.id}")
else:
    print(f"\n   ⚠️ Матчей на сегодня не найдено")

# 3. Проверка main.py
print("\n3. Проверка main.py:")

# Проверка leagues_to_check
with open('/Users/ilyailyx/Desktop/sports-analytics-bot/main.py', 'r') as f:
    main_content = f.read()

if 'wc_qual_europe' in main_content:
    print("   ✅ wc_qual_europe найден в main.py")
else:
    print("   ❌ wc_qual_europe НЕ найден в main.py!")

if '"wc_qual_europe"' in main_content or "'wc_qual_europe'" in main_content:
    print("   ✅ Квалификации добавлены в leagues_to_check")
else:
    print("   ❌ Квалификации НЕ добавлены в leagues_to_check!")

# Проверка leagues dict
if 'Квалификация ЧМ' in main_content:
    print("   ✅ Квалификации добавлены в меню лиг")
else:
    print("   ❌ Квалификации НЕ добавлены в меню лиг!")

# 4. Итог
print("\n" + "=" * 70)
print("📊 ИТОГИ")
print("=" * 70)

if len(today_matches) > 0:
    print(f"\n✅ ВСЁ РАБОТАЕТ! Найдено {len(today_matches)} матчей квалификации ЧМ на сегодня.")
    print(f"\n📌 Для запуска бота выполните:")
    print(f"   cd /Users/ilyailyx/Desktop/sports-analytics-bot")
    print(f"   source venv/bin/activate")
    print(f"   python main.py")
else:
    print(f"\n⚠️ Матчей на сегодня не найдено. Это может быть нормально, если сегодня нет игр квалификации.")
    print(f"\n📅 Ближайшие матчи:")
    sorted_dates = sorted(matches_data.keys(), key=lambda x: datetime.datetime.strptime(x.split()[0], "%d.%m.%Y"))
    for date_key in sorted_dates[:5]:
        if datetime.datetime.strptime(date_key.split()[0], "%d.%m.%Y").date() >= today:
            print(f"   {date_key}: {len(matches_data[date_key])} матчей")

print("\n" + "=" * 70)
