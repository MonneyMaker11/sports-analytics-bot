"""Debug script to check Bosnia vs Italy match data."""

import os
import json
from dotenv import load_dotenv
from api_football_parser import APIFootballParser

load_dotenv()

api_key = os.getenv("API_FOOTBALL_KEY")
parser = APIFootballParser(api_key=api_key)

# Find Bosnia vs Italy match
matches = parser.get_fixtures("wc_qual_europe", days=30)

for match in matches:
    if "Bosnia" in match.home_team or "Italy" in match.away_team:
        print(f"\n{'='*60}")
        print(f"Match: {match.home_team} vs {match.away_team}")
        print(f"Date: {match.date}")
        print(f"Tournament: {match.tournament}")
        print(f"ID: {match.id}")
        
        # Get full details
        details = parser.get_match_details(match.id)
        
        if details:
            print(f"\n--- Team Form ---")
            print(f"Home form: {details.home_team_form}")
            print(f"Away form: {details.away_team_form}")
            
            print(f"\n--- H2H ---")
            print(f"H2H matches: {details.h2h_matches}")
            
            print(f"\n--- Odds (RAW) ---")
            print(json.dumps(details.odds, indent=2, default=str))
            
            # Try to extract odds manually
            odds_data = details.odds.get("odds", [])
            if isinstance(odds_data, list):
                print(f"\n--- Parsed Odds ---")
                for bk in odds_data[:3]:  # First 3 bookmakers
                    if isinstance(bk, dict):
                        bk_name = bk.get("name", "Unknown")
                        print(f"\n{bk_name}:")
                        for mkt in bk.get("markets", [])[:5]:
                            if isinstance(mkt, dict):
                                mkt_name = mkt.get("name", "Unknown")
                                print(f"  Market: {mkt_name}")
                                selections = mkt.get("values", mkt.get("selections", []))
                                for sel in selections[:5]:
                                    if isinstance(sel, dict):
                                        label = sel.get("value", sel.get("label", "N/A"))
                                        odd = sel.get("odd", sel.get("value", "N/A"))
                                        print(f"    {label}: {odd}")
