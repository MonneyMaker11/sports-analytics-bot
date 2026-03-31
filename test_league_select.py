#!/usr/bin/env python3
"""Test league selection in bot"""
import sys
sys.path.insert(0, '/Users/ilyailyx/Desktop/sports-analytics-bot')

from api_football_parser import APIFootballParser
import datetime
import re

parser = APIFootballParser(api_key="08c6e6aeaf97abc445440c686ac50fab")

print("=== Тест выбора лиги (как в боте) ===\n")

# Simulate date selection (today)
today = datetime.date.today()
date_str = today.strftime("%Y-%m-%d")
print(f"Выбранная дата: {date_str} ({today.strftime('%d.%m.%Y (%A)')})\n")

# Test leagues dict (like in bot)
leagues = {
    "wc_qual_europe": "🌍 Квалификация ЧМ (Европа)",
    "premier_league": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League",
}

for league_key, league_name in leagues.items():
    print(f"Проверка {league_key}:")
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
                    print(f"   ✅ Найдено совпадение: {date_display} -> {match_count} матчей")
                    break
            except Exception as e:
                print(f"   Ошибка: {e}")
    
    if match_count == 0:
        print(f"   ❌ Матчей не найдено на {date_str}")
        print(f"   Доступные даты:")
        for d in list(matches_data.keys())[:5]:
            print(f"      • {d}")
    
    print(f"   Результат: {league_name} ({match_count})\n")
