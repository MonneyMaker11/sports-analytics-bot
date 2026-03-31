#!/usr/bin/env python3
"""Debug each step of get_match_details"""
import sys
sys.path.insert(0, '/Users/ilyailyx/Desktop/sports-analytics-bot')

from api_football_parser import APIFootballParser, MatchDetails
import logging

logging.basicConfig(level=logging.INFO)

parser = APIFootballParser(api_key="08c6e6aeaf97abc445440c686ac50fab")

match_id = "1537581"
print(f"Шаги get_match_details для матча {match_id}:\n")

# Step 1: Get fixture details
print("1. Получаем fixture details...")
params = {"id": match_id}
data = parser._make_request("/fixtures", params)
print(f"   data: {data is not None}")
print(f"   response: {data.get('response') if data else None}")

if data and data.get("response"):
    fixture = data["response"][0]
    match = parser._parse_fixture(fixture)
    print(f"   match: {match}")
    
    if match:
        print(f"\n2. Создаём MatchDetails...")
        details = MatchDetails(match=match)
        print(f"   OK")
        
        print(f"\n3. Получаем statistics...")
        stats = parser._get_statistics(match_id)
        print(f"   statistics: {stats}")
        
        print(f"\n4. Получаем lineups...")
        lineups = parser._get_lineups(match_id)
        print(f"   lineups: {lineups}")
        
        print(f"\n5. Получаем odds...")
        odds = parser._get_odds(match_id)
        print(f"   odds: {odds}")
        
        print(f"\n6. Получаем H2H...")
        h2h = parser._get_h2h(match.home_team_id, match.away_team_id, last=10)
        print(f"   h2h: {len(h2h)} матчей")
        
        print(f"\n7. Получаем form...")
        home_form = parser._get_team_form(match.home_team_id, last=10)
        away_form = parser._get_team_form(match.away_team_id, last=10)
        print(f"   home_form: {len(home_form)} матчей")
        print(f"   away_form: {len(away_form)} матчей")
        
        print(f"\n8. Получаем injuries...")
        injuries = parser._get_injuries(match.home_team_id, match.away_team_id)
        print(f"   injuries: {injuries}")
        
        print(f"\n9. Получаем standings...")
        standings = parser._get_standings(match.tournament, match.home_team_id, match.away_team_id)
        print(f"   standings: {standings}")
        
        print(f"\n✅ ВСЕ ШАГИ УСПЕШНЫ!")
