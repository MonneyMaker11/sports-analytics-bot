#!/usr/bin/env python3
"""Full bot simulation test"""
import sys
sys.path.insert(0, '/Users/ilyailyx/Desktop/sports-analytics-bot')

from api_football_parser import APIFootballParser
import datetime
import re

parser = APIFootballParser(api_key="08c6e6aeaf97abc445440c686ac50fab")

print("=== Полная симуляция бота ===\n")

# Step 1: _show_date_selection
print("1. ШАГ: Выбор даты (_show_date_selection)")
print("=" * 50)

all_matches_by_date = {}
leagues_to_check = [
    "premier_league", "la_liga", "bundesliga", "serie_a", "ligue_1",
    "champions_league", "europa_league",
    "eredivisie", "primeira_liga", "mls", "brasileirao",
    "wc_qual_europe", "wc_qual_concacaf", "wc_qual_south_america",
    "wc_qual_asia", "wc_qual_africa", "wc_qual_oceania", "wc_qual_playoffs",
]

print(f"Проверяем лиги: {', '.join(leagues_to_check)}\n")

for league in leagues_to_check:
    matches_data = parser.get_fixtures_by_date(league, days=14)
    total = sum(len(m) for m in matches_data.values())
    if total > 0:
        print(f"   ✅ {league}: {total} матчей в {len(matches_data)} датах")
    for date_display, matches in matches_data.items():
        if date_display not in all_matches_by_date:
            all_matches_by_date[date_display] = 0
        all_matches_by_date[date_display] += len(matches)

print(f"\n📅 Всего дней с матчами: {len(all_matches_by_date)}")

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
        except Exception as e:
            print(f"Ошибка парсинга {date_display}: {e}")

# Show buttons
today = datetime.date.today()
print(f"\n🔘 Кнопки (следующие 14 дней):")
for i in range(5):
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

# Step 2: on_date_select
print("\n\n2. ШАГ: Выбор лиги (on_date_select)")
print("=" * 50)

date_str = today.strftime("%Y-%m-%d")
print(f"Выбрана дата: {date_str}\n")

leagues = {
    "wc_qual_europe": "🌍 Квалификация ЧМ (Европа)",
    "wc_qual_concacaf": "🌍 Квалификация ЧМ (CONCACAF)",
    "wc_qual_south_america": "🌍 Квалификация ЧМ (Юж. Америка)",
    "wc_qual_asia": "🌍 Квалификация ЧМ (Азия)",
    "wc_qual_africa": "🌍 Квалификация ЧМ (Африка)",
    "wc_qual_oceania": "🌍 Квалификация ЧМ (Океания)",
    "wc_qual_playoffs": "🌍 Квалификация ЧМ (Плей-офф)",
    "premier_league": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League",
}

for league_key, league_name in leagues.items():
    matches_data = parser.get_fixtures_by_date(league_key, days=30)
    match_count = 0
    
    for date_display, matches in matches_data.items():
        date_match = re.match(r"(\d{2}\.\d{2}\.\d{4})", date_display)
        if date_match:
            dmy = date_match.group(1)
            try:
                dt = datetime.datetime.strptime(dmy, "%d.%m.%Y")
                iso_date = dt.strftime("%Y-%m-%d")
                if iso_date == date_str:
                    match_count = len(matches)
                    break
            except:
                pass
    
    status = "✅" if match_count > 0 else "❌"
    print(f"   {status} {league_name} ({match_count})")

# Step 3: on_league_select
print("\n\n3. ШАГ: Выбор матча (on_league_select)")
print("=" * 50)

league = "wc_qual_europe"
print(f"Выбрана лига: {league}\n")

matches_by_date = parser.get_fixtures_by_date(league, days=30)
target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
display_date = target_date.strftime("%d.%m.%Y (%A)")

print(f"Ищем матчи на: {display_date}")

day_matches = []
for date_key, matches in matches_by_date.items():
    if date_str in date_key or display_date.split(" ")[0] in date_key:
        day_matches = matches
        break

if day_matches:
    print(f"\n✅ Найдено {len(day_matches)} матчей:")
    for match in day_matches:
        print(f"   ⚽ {match.home_team} vs {match.away_team}")
        print(f"      ID: {match.id}")
else:
    print("❌ Матчей не найдено!")
    print(f"\nДоступные даты в matches_by_date:")
    for dk in list(matches_by_date.keys())[:10]:
        print(f"   • {dk}")
