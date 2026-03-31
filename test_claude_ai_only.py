#!/usr/bin/env python3
"""
Test script for Claude AI-only analysis with API + Web Search
Tests the full flow: API data → Claude AI → Analysis
"""

import os
import asyncio
import logging
from dotenv import load_dotenv
from api_football_parser import APIFootballParser
from ai_analyzer import AIAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

async def test_claude_analysis():
    """Test Claude AI analysis with real API data."""
    
    print("=" * 80)
    print("🧪 CLAUDE AI-ONLY ANALYSIS TEST (API + Web Search)")
    print("=" * 80)
    
    # Check API keys
    api_football_key = os.getenv("API_FOOTBALL_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_football_key:
        print("❌ API_FOOTBALL_KEY not set!")
        return False
    
    if not anthropic_key:
        print("❌ ANTHROPIC_API_KEY not set!")
        print("⚠️  Running in data-only mode (no AI analysis)")
    
    # Initialize
    parser = APIFootballParser(api_key=api_football_key)
    analyzer = AIAnalyzer() if anthropic_key else None
    
    # Get WC Qualification matches
    print("\n📅 Fetching WC Qualification matches...")
    matches = parser.get_fixtures("wc_qual_europe", days=30)
    
    if not matches:
        print("❌ No matches found!")
        return False
    
    print(f"✅ Found {len(matches)} matches")
    
    # Find Bosnia vs Italy
    target_match = None
    for match in matches:
        if "Bosnia" in match.home_team and "Italy" in match.away_team:
            target_match = match
            break
    
    if not target_match:
        print(f"⚠️  Bosnia vs Italy not found, using first match")
        target_match = matches[0]
    
    print(f"\n📌 Selected: {target_match.home_team} vs {target_match.away_team}")
    print(f"   Tournament: {target_match.tournament}")
    
    # Get match details
    print("\n🔍 Fetching match details from API...")
    details = parser.get_match_details(target_match.id)
    
    if not details:
        print("❌ Failed to get match details!")
        return False
    
    print("✅ Match details received")
    
    # Show API data
    print("\n" + "=" * 80)
    print("📊 API DATA SUMMARY")
    print("=" * 80)
    
    print(f"\n📈 ФОРМА:")
    home_form = details.home_team_form[:5]
    away_form = details.away_team_form[:5]
    home_results = "".join([m.get("result", "?") for m in home_form])
    away_results = "".join([m.get("result", "?") for m in away_form])
    print(f"   {details.match.home_team}: {home_results}")
    print(f"   {details.match.away_team}: {away_results}")
    
    print(f"\n🎯 H2H:")
    h2h = details.h2h_matches[:3]
    for m in h2h:
        print(f"   {m.get('home_team', '?')} {m.get('home_score', '?')}:{m.get('away_score', '?')} {m.get('away_team', '?')}")
    
    print(f"\n💰 ODDS:")
    odds = details.odds.get("odds", []) if details.odds else []
    if odds and len(odds) > 0:
        print(f"   {len(odds)} bookmakers available")
    else:
        print(f"   No odds data available")
    
    # Run AI analysis
    if analyzer:
        print("\n" + "=" * 80)
        print("🤖 CLAUDE AI ANALYSIS")
        print("=" * 80)
        
        try:
            print("\n⏳ Sending data to Claude (with web search enabled)...")
            analysis = await analyzer.generate_analysis(details)
            
            print("\n" + "=" * 80)
            print("📋 AI ANALYSIS RESULT")
            print("=" * 80)
            print("\n" + analysis)
            print("\n" + "=" * 80)
            
            # Validate response
            print("\n✅ VALIDATION:")
            
            checks = []
            
            # Check for required sections
            checks.append(("Has header", "⚽" in analysis or "vs" in analysis))
            checks.append(("Has probabilities", "%" in analysis and ("П1" in analysis or "П2" in analysis)))
            checks.append(("Has form section", "ФОРМА" in analysis.upper() or "FORM" in analysis.upper()))
            checks.append(("Has H2H", "H2H" in analysis.upper()))
            checks.append(("Has recommendations", "РЕКОМЕНДАЦИИ" in analysis.upper() or "1." in analysis))
            checks.append(("Has disclaimer", "⚠" in analysis or "ДИСКЛЕЙМЕР" in analysis.upper()))
            
            all_pass = True
            for name, passed in checks:
                status = "✅" if passed else "❌"
                print(f"   {status} {name}")
                if not passed:
                    all_pass = False
            
            print("\n" + "=" * 80)
            if all_pass:
                print("🎉 ALL CHECKS PASSED!")
            else:
                print("⚠️  Some checks failed")
            print("=" * 80)
            
            return all_pass
            
        except Exception as e:
            print(f"\n❌ AI analysis failed: {e}")
            logger.exception("Full error:")
            return False
    else:
        print("\n⚠️  AI analysis skipped (no ANTHROPIC_API_KEY)")
        print("✅ API data fetch successful!")
        return True


if __name__ == "__main__":
    print("\n🚀 Starting test...\n")
    
    result = asyncio.run(test_claude_analysis())
    
    print(f"\n{'✅ TEST PASSED' if result else '❌ TEST FAILED'}\n")
    exit(0 if result else 1)
