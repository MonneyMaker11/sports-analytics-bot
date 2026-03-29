#!/usr/bin/env python3
from flashscore_parser import FlashscoreParser
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('FOOTBALL_DATA_API_KEY')
print(f'API Key: {api_key}')

parser = FlashscoreParser(football_data_api_key=api_key)

print("\n=== Testing La Liga ===")
result = parser.get_matches_by_date('la_liga', days=14)
print('Dates found:', len(result))
for k, v in list(result.items())[:5]:
    print(f'  {k}: {len(v)} matches')
    if v:
        print(f'    Example: {v[0].home_team} vs {v[0].away_team}')

print("\n=== Testing Bundesliga ===")
result2 = parser.get_matches_by_date('bundesliga', days=14)
print('Dates found:', len(result2))
for k, v in list(result2.items())[:3]:
    print(f'  {k}: {len(v)} matches')
