"""Test script to verify Bosnia vs Italy probability fixes."""

import os
import json
from dotenv import load_dotenv
from api_football_parser import APIFootballParser
from ai_analyzer import EnhancedPoissonCalculator

load_dotenv()

api_key = os.getenv("API_FOOTBALL_KEY")
parser = APIFootballParser(api_key=api_key)
calc = EnhancedPoissonCalculator()

# Find Bosnia vs Italy match
matches = parser.get_fixtures("wc_qual_europe", days=30)

print("=" * 70)
print("TESTING BOSNIA vs ITALY PROBABILITY FIX")
print("=" * 70)

for match in matches:
    if "Bosnia" in match.home_team and "Italy" in match.away_team:
        print(f"\n📌 Match: {match.home_team} vs {match.away_team}")
        print(f"   Tournament: {match.tournament}")
        print(f"   Date: {match.date}")
        
        # Get full details
        details = parser.get_match_details(match.id)
        
        if details:
            print(f"\n🔍 ODDS DATA:")
            print(f"   Odds available: {bool(details.odds)}")
            if details.odds:
                print(f"   Odds type: {type(details.odds)}")
                if isinstance(details.odds, dict):
                    print(f"   Odds keys: {list(details.odds.keys())}")
                    odds_list = details.odds.get("odds", [])
                    print(f"   Number of bookmakers: {len(odds_list) if isinstance(odds_list, list) else 'N/A'}")
                    if isinstance(odds_list, list) and len(odds_list) > 0:
                        first_bk = odds_list[0] if isinstance(odds_list[0], dict) else None
                        if first_bk:
                            print(f"   First bookmaker: {first_bk.get('name', 'Unknown')}")
                            markets = first_bk.get("markets", [])
                            print(f"   Number of markets: {len(markets) if isinstance(markets, list) else 'N/A'}")
                            # Find Match Winner market
                            for mkt in markets[:5]:
                                if isinstance(mkt, dict) and "match winner" in mkt.get("name", "").lower():
                                    print(f"   ✓ Found 'Match Winner' market: {mkt.get('name')}")
                                    vals = mkt.get("values", [])[:3]
                                    for v in vals:
                                        if isinstance(v, dict):
                                            print(f"      {v.get('value')}: {v.get('odd')}")
            
            # Calculate probabilities
            stats = calc.calculate_probabilities(details)
            
            print(f"\n📊 RESULTS:")
            print(f"   Is National Teams Match: {stats.get('is_national_teams', False)}")
            print(f"   Blended with Market: {stats.get('blended', False)}")
            
            if stats.get('market_home_odd'):
                print(f"\n💰 MARKET ODDS:")
                print(f"   Home (Bosnia): {stats['market_home_odd']:.2f}")
                print(f"   Draw: {stats['market_draw_odd']:.2f}")
                print(f"   Away (Italy): {stats['market_away_odd']:.2f}")
            
            print(f"\n🎯 PROBABILITIES:")
            print(f"   Home Win (Bosnia): {stats['home_win_pct']}%")
            print(f"   Draw: {stats['draw_pct']}%")
            print(f"   Away Win (Italy): {stats['away_win_pct']}%")
            
            # Verify probabilities are realistic
            print(f"\n✅ VALIDATION:")
            
            # Bosnia should be ~12-15% (not 52%!)
            bosnia_ok = 8 <= stats['home_win_pct'] <= 20
            print(f"   Bosnia win% realistic (8-20%): {'✅ PASS' if bosnia_ok else '❌ FAIL'} ({stats['home_win_pct']}%)")
            
            # Italy should be favorite ~55-65%
            italy_ok = 50 <= stats['away_win_pct'] <= 70
            print(f"   Italy win% realistic (50-70%): {'✅ PASS' if italy_ok else '❌ FAIL'} ({stats['away_win_pct']}%)")
            
            # Draw should be ~20-28%
            draw_ok = 18 <= stats['draw_pct'] <= 30
            print(f"   Draw% realistic (18-30%): {'✅ PASS' if draw_ok else '❌ FAIL'} ({stats['draw_pct']}%)")
            
            # Sum should be 100
            total = stats['home_win_pct'] + stats['draw_pct'] + stats['away_win_pct']
            sum_ok = total == 100
            print(f"   Sum = 100%: {'✅ PASS' if sum_ok else '❌ FAIL'} ({total}%)")
            
            # Market odds should be extracted correctly
            if stats.get('market_home_odd'):
                # Bosnia should be ~7.0-8.5
                bosnia_odd_ok = 6.0 <= stats['market_home_odd'] <= 9.5
                print(f"   Bosnia odd realistic (6.0-9.5): {'✅ PASS' if bosnia_odd_ok else '❌ FAIL'} ({stats['market_home_odd']})")
                
                # Italy should be ~1.45-1.60
                italy_odd_ok = 1.40 <= stats['market_away_odd'] <= 1.70
                print(f"   Italy odd realistic (1.40-1.70): {'✅ PASS' if italy_odd_ok else '❌ FAIL'} ({stats['market_away_odd']})")
            
            print(f"\n📈 ADDITIONAL STATS:")
            print(f"   Expected Total Goals: {stats['expected_total_goals']}")
            print(f"   Over 2.5: {stats['over_2_5_pct']}%")
            print(f"   BTTS Yes: {stats['btts_yes_pct']}%")
            likely_scores_str = ", ".join([f"{s['score']} ({s['prob']}%)" for s in stats['likely_scores'][:3]])
            print(f"   Likely Scores: {likely_scores_str}")
            
            print("\n" + "=" * 70)
            
            # Overall result
            bosnia_odd_ok = stats.get('market_home_odd') is None or 6.0 <= stats['market_home_odd'] <= 9.5
            italy_odd_ok = stats.get('market_away_odd') is None or 1.40 <= stats['market_away_odd'] <= 1.70
            all_pass = bosnia_ok and italy_ok and draw_ok and sum_ok and bosnia_odd_ok and italy_odd_ok
            if all_pass:
                print("🎉 ALL TESTS PASSED! Probabilities are now realistic.")
            else:
                print("⚠️ Some tests failed. Review the model.")
            print("=" * 70)
            
            break

if not any("Bosnia" in m.home_team and "Italy" in m.away_team for m in matches):
    print("❌ Bosnia vs Italy match not found in fixtures!")
    print(f"   Available matches: {[(m.home_team, m.away_team) for m in matches[:10]]}")
