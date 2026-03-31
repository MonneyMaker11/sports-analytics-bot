#!/usr/bin/env python3
"""Clear parser cache"""
import sys
sys.path.insert(0, '/Users/ilyailyx/Desktop/sports-analytics-bot')

from api_football_parser import APIFootballParser

parser = APIFootballParser(api_key="08c6e6aeaf97abc445440c686ac50fab")

print("Очистка кэша...")
parser._season_cache.clear()
print(f"Кэш очищен. Текущий размер: {len(parser._season_cache)}")

# Pre-load WC Qualification
print("\nПредзагрузка квалификации ЧМ...")
matches = parser.get_fixtures_by_date("wc_qual_europe", days=30)
print(f"Загружено {len(matches)} дат с матчами")

import datetime
today = datetime.date.today()
for date_str, m in matches.items():
    if today.strftime("%d.%m") in date_str:
        print(f"\n✅ Матчи на сегодня ({date_str}):")
        for match in m:
            print(f"   • {match.home_team} vs {match.away_team}")
