#!/usr/bin/env python3
"""Debug match details"""
import sys
sys.path.insert(0, '/Users/ilyailyx/Desktop/sports-analytics-bot')

from api_football_parser import APIFootballParser
import logging

logging.basicConfig(level=logging.INFO)

parser = APIFootballParser(api_key="08c6e6aeaf97abc445440c686ac50fab")

match_id = "1537581"
print(f"Получаем детали матча {match_id}...")

details = parser.get_match_details(match_id)

if details:
    print(f"✅ Матч: {details.match.home_team} vs {details.match.away_team}")
    print(f"✅ Турнир: {details.match.tournament}")
    print(f"✅ Форма хозяев: {len(details.home_team_form)}")
    print(f"✅ Форма гостей: {len(details.away_team_form)}")
    print(f"✅ H2H: {len(details.h2h_matches)}")
else:
    print("❌ Details is None")
