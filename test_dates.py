#!/usr/bin/env python3
from flashscore_parser import FlashscoreParser
import os
from dotenv import load_dotenv
import datetime

load_dotenv()

parser = FlashscoreParser(football_data_api_key=os.getenv('FOOTBALL_DATA_API_KEY'))

# Test get_matches_by_date
print("Testing la_liga...")
result = parser.get_matches_by_date('la_liga', days=14)
print('Result type:', type(result))
print('Keys:', list(result.keys())[:5])
for k, v in list(result.items())[:3]:
    print(f'  {k}: {len(v)} matches')
    if v:
        print(f'    First match date: {v[0].date}')

# Test date matching
print("\n\nDate matching test:")
today = datetime.date.today()
for i in range(3):
    target_date = today + datetime.timedelta(days=i)
    date_str = target_date.strftime("%Y-%m-%d")
    display_date = target_date.strftime("%d.%m.%Y (%A)")
    print(f"Looking for: {date_str}")
    print(f"Display date: {display_date}")
    
    # Check if date_str is in any key
    for key in result.keys():
        if date_str in key:
            print(f"  FOUND in key: {key}")
        elif key.startswith(target_date.strftime("%d.%m")):
            print(f"  FOUND (starts with): {key}")
