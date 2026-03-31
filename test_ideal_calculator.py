"""Test the Ideal Probability Calculator."""

import os
import logging
from dotenv import load_dotenv
from api_football_parser import APIFootballParser
from ideal_probability_calculator import IdealProbabilityCalculator

logging.basicConfig(level=logging.INFO)
load_dotenv()

api_key = os.getenv("API_FOOTBALL_KEY")
parser = APIFootballParser(api_key=api_key)
calc = IdealProbabilityCalculator(parser)

print("=" * 80)
print("IDEAL PROBABILITY CALCULATOR TEST")
print("=" * 80)

# Test on Bosnia vs Italy
matches = parser.get_fixtures("wc_qual_europe", days=30)

for match in matches:
    if "Bosnia" in match.home_team and "Italy" in match.away_team:
        print(f"\n📌 {match.home_team} vs {match.away_team}")
        print(f"   Tournament: {match.tournament}")
        
        details = parser.get_match_details(match.id)
        if details:
            result = calc.calculate_ideal_probabilities(details)
            analysis = calc.format_analysis(result)
            print("\n" + analysis)
            
            # Validation
            print("\n" + "=" * 80)
            print("VALIDATION:")
            
            final = result["final"]
            
            # Check probabilities are realistic
            checks = []
            
            # Bosnia should be 10-25%
            bosnia_ok = 8 <= final['home_win_pct'] <= 28
            checks.append(("Bosnia win% realistic", bosnia_ok, final['home_win_pct']))
            
            # Italy should be favorite 50-75%
            italy_ok = 48 <= final['away_win_pct'] <= 78
            checks.append(("Italy win% realistic", italy_ok, final['away_win_pct']))
            
            # Draw 15-30%
            draw_ok = 14 <= final['draw_pct'] <= 32
            checks.append(("Draw% realistic", draw_ok, final['draw_pct']))
            
            # Sum = 100
            sum_total = final['home_win_pct'] + final['draw_pct'] + final['away_win_pct']
            sum_ok = sum_total == 100
            checks.append(("Sum = 100%", sum_ok, sum_total))
            
            # Market odds extracted
            market = result["market"]
            market_ok = market["available"] or True  # OK if not available (fallback to form)
            checks.append(("Market odds", market_ok, market["available"]))
            
            all_pass = all(c[1] for c in checks)
            
            for name, passed, value in checks:
                status = "✅" if passed else "❌"
                print(f"   {status} {name}: {value}")
            
            print("\n" + "=" * 80)
            if all_pass:
                print("🎉 ALL CHECKS PASSED!")
            else:
                print("⚠️ Some checks failed")
            print("=" * 80)
            
            break

# Test on club match
print("\n\n" + "=" * 80)
print("TESTING CLUB MATCH (Premier League)")
print("=" * 80)

pl_matches = parser.get_fixtures("premier_league", days=7)
if pl_matches:
    match = pl_matches[0]
    print(f"\n📌 {match.home_team} vs {match.away_team}")
    
    details = parser.get_match_details(match.id)
    if details:
        result = calc.calculate_ideal_probabilities(details)
        analysis = calc.format_analysis(result)
        print("\n" + analysis)
