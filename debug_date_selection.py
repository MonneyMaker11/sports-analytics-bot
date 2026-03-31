#!/usr/bin/env python3
"""Debug date selection - exact bot logic"""
import sys
sys.path.insert(0, '/Users/ilyailyx/Desktop/sports-analytics-bot')

from api_football_parser import APIFootballParser
import datetime
import re

parser = APIFootballParser(api_key="08c6e6aeaf97abc445440c686ac50fab")

print("=== Debug: _show_date_selection (точная логика бота) ===\n")

# Exact copy from bot
all_matches_by_date = {}
leagues_to_check = [
    "premier_league", "la_liga", "bundesliga", "serie_a", "ligue_1",
    "champions_league", "europa_league",
    "eredivisie", "primeira_liga", "mls", "brasileirao",
    "wc_qual_europe", "wc_qual_concacaf", "wc_qual_south_america",
    "wc_qual_asia", "wc_qual_africa", "wc_qual_oceania", "wc_qual_playoffs",
]

print("Загружаем матчи для лиг...\n")

for league in leagues_to_check:
    matches_data = parser.get_fixtures_by_date(league, days=14)
    league_total = sum(len(m) for m in matches_data.values())
    
    if league_total > 0:
        print(f"✅ {league}: {league_total} матчей")
        
    for date_display, matches in matches_data.items():
        if date_display not in all_matches_by_date:
            all_matches_by_date[date_display] = 0
        all_matches_by_date[date_display] += len(matches)

print(f"\n📅 all_matches_by_date: {len(all_matches_by_date)} дней")

# Show first 10 dates
print("\nДоступные даты:")
for i, (date_key, count) in enumerate(list(all_matches_by_date.items())[:10]):
    print(f"   {date_key}: {count} матчей")

# Create date_counts (exact bot logic)
print("\n\nСоздаём date_counts mapping...")
date_counts = {}
for date_display, count in all_matches_by_date.items():
    date_match = re.match(r"(\d{2}\.\d{2}\.\d{4})", date_display)
    if date_match:
        dmy = date_match.group(1)
        try:
            dt = datetime.datetime.strptime(dmy, "%d.%m.%Y")
            iso_date = dt.strftime("%Y-%m-%d")
            date_counts[iso_date] = count
            print(f"   {date_display} -> {iso_date} = {count}")
        except Exception as e:
            print(f"   ❌ Ошибка парсинга {date_display}: {e}")

# Show buttons (exact bot logic)
today = datetime.date.today()
print(f"\n\n🔘 Кнопки дат (бот покажет эти 14 дней):")
print(f"Сегодня: {today.strftime('%d.%m.%Y (%A)')}\n")

for i in range(14):
    target_date = today + datetime.timedelta(days=i)
    date_str = target_date.strftime("%Y-%m-%d")
    display_date = target_date.strftime("%d.%m (%A)")
    
    match_count = date_counts.get(date_str, 0)
    
    if i == 0:
        btn_text = f"Сегодня ({match_count})"
    elif i == 1:
        btn_text = f"Завтра ({match_count})"
    else:
        btn_text = f"{display_date} ({match_count})"
    
    status = "✅" if match_count > 0 else "❌"
    print(f"   {status} {btn_text}")

# Debug: почему сегодня 0?
print(f"\n\n🔍 Debug: почему может быть 0?")
print(f"   date_str для сегодня: {today.strftime('%Y-%m-%d')}")
print(f"   match_count: {date_counts.get(today.strftime('%Y-%m-%d'), 0)}")
print(f"   Все ключи в date_counts: {list(date_counts.keys())[:10]}")

# Проверка формата даты
print(f"\n\n🔍 Проверка формата дат в all_matches_by_date:")
today_dmy = today.strftime("%d.%m.%Y")
for date_key in all_matches_by_date.keys():
    if today_dmy in date_key or today.strftime("%d.%m") in date_key:
        print(f"   ✅ Найдено совпадение: {date_key} ({all_matches_by_date[date_key]} матчей)")
