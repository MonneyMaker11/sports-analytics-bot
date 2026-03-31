#!/usr/bin/env python3
"""Test full bot flow"""
import sys
sys.path.insert(0, '/Users/ilyailyx/Desktop/sports-analytics-bot')

from api_football_parser import APIFootballParser
import datetime
import re

parser = APIFootballParser(api_key="08c6e6aeaf97abc445440c686ac50fab")

print("=== Полный тест потока бота ===\n")

# Step 1: Date selection (like in _show_date_selection)
print("1. Выбор даты (как в _show_date_selection):")
all_matches_by_date = {}
leagues_to_check = [
    "premier_league", "la_liga", "bundesliga", "serie_a", "ligue_1",
    "champions_league", "europa_league",
    "eredivisie", "primeira_liga", "mls", "brasileirao",
    "wc_qual_europe",  # Add WC qualification
]

for league in leagues_to_check:
    matches_data = parser.get_fixtures_by_date(league, days=14)
    for date_display, matches in matches_data.items():
        if date_display not in all_matches_by_date:
            all_matches_by_date[date_display] = 0
        all_matches_by_date[date_display] += len(matches)

print(f"   Всего дней с матчами: {len(all_matches_by_date)}")

# Create date_counts mapping
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

# Show date buttons
today = datetime.date.today()
print(f"\n   Кнопки дат (следующие 14 дней):")
for i in range(7):  # Show first 7 days
    target_date = today + datetime.timedelta(days=i)
    date_str = target_date.strftime("%Y-%m-%d")
    match_count = date_counts.get(date_str, 0)
    
    if i == 0:
        btn_text = f"Сегодня ({match_count})"
    elif i == 1:
        btn_text = f"Завтра ({match_count})"
    else:
        btn_text = f"{target_date.strftime('%d.%m')} ({match_count})"
    
    marker = "✅" if match_count > 0 else "❌"
    print(f"   {marker} {btn_text}")

# Step 2: League selection
print(f"\n\n2. Выбор лиги для {today.strftime('%Y-%m-%d')}:")
leagues = {
    "wc_qual_europe": "🌍 Квалификация ЧМ (Европа)",
    "wc_qual_concacaf": "🌍 Квалификация ЧМ (CONCACAF)",
    "wc_qual_south_america": "🌍 Квалификация ЧМ (Юж. Америка)",
    "wc_qual_asia": "🌍 Квалификация ЧМ (Азия)",
    "wc_qual_africa": "🌍 Квалификация ЧМ (Африка)",
    "wc_qual_oceania": "🌍 Квалификация ЧМ (Океания)",
    "wc_qual_playoffs": "🌍 Квалификация ЧМ (Плей-офф)",
}

date_str = today.strftime("%Y-%m-%d")
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
    
    marker = "✅" if match_count > 0 else "❌"
    print(f"   {marker} {league_name} ({match_count})")
