"""
Test script to verify the enhanced Claude prompt with maximum statistical depth.
"""

from api_football_parser import Match, MatchDetails
from ai_analyzer import AIAnalyzer

# Create comprehensive test match data
def create_test_match():
    """Create realistic test match with full data."""
    match = Match(
        id="test_001",
        date="2026-03-30 20:00",
        home_team="Manchester City",
        away_team="Liverpool",
        tournament="FA Cup",
        home_score=None,
        away_score=None,
        status="NS"
    )

    # Home team form (last 5)
    home_form = [
        {"opponent": "Arsenal", "result": "W", "score": "3:1", "date": 1711500000, "is_home": True},
        {"opponent": "Chelsea", "result": "W", "score": "2:0", "date": 1711400000, "is_home": False},
        {"opponent": "Newcastle", "result": "D", "score": "2:2", "date": 1711300000, "is_home": True},
        {"opponent": "Tottenham", "result": "W", "score": "4:1", "date": 1711200000, "is_home": False},
        {"opponent": "Aston Villa", "result": "L", "score": "1:2", "date": 1711100000, "is_home": True},
    ]

    # Away team form (last 5)
    away_form = [
        {"opponent": "Brighton", "result": "W", "score": "2:1", "date": 1711500000, "is_home": False},
        {"opponent": "West Ham", "result": "W", "score": "3:0", "date": 1711400000, "is_home": True},
        {"opponent": "Fulham", "result": "D", "score": "1:1", "date": 1711300000, "is_home": False},
        {"opponent": "Wolves", "result": "W", "score": "2:0", "date": 1711200000, "is_home": True},
        {"opponent": "Everton", "result": "W", "score": "3:1", "date": 1711100000, "is_home": False},
    ]

    # H2H history
    h2h = [
        {"home_team": "Liverpool", "away_team": "Manchester City", "home_score": 2, "away_score": 1, "date": 1700000000},
        {"home_team": "Manchester City", "away_team": "Liverpool", "home_score": 1, "away_score": 1, "date": 1690000000},
        {"home_team": "Liverpool", "away_team": "Manchester City", "home_score": 3, "away_score": 1, "date": 1680000000},
        {"home_team": "Manchester City", "away_team": "Liverpool", "home_score": 4, "away_score": 1, "date": 1670000000},
        {"home_team": "Liverpool", "away_team": "Manchester City", "home_score": 2, "away_score": 2, "date": 1660000000},
    ]

    # Match statistics (simulated)
    statistics = {
        "Manchester City_Shot on Target": 6.2,
        "Liverpool_Shot on Target": 5.8,
        "Manchester City_Possession": 62,
        "Liverpool_Possession": 58,
        "Manchester City_Pass Accuracy": 88,
        "Liverpool_Pass Accuracy": 85,
    }

    # Odds data
    odds = {
        "bookmakers": [
            {
                "name": "Bet365",
                "markets": [
                    {
                        "name": "Match Winner",
                        "selections": [
                            {"value": "Home", "odd": 2.10},
                            {"value": "Draw", "odd": 3.60},
                            {"value": "Away", "odd": 3.40},
                        ]
                    },
                    {
                        "name": "Over/Under 2.5",
                        "selections": [
                            {"value": "Over", "odd": 1.72},
                            {"value": "Under", "odd": 2.10},
                        ]
                    },
                ]
            }
        ]
    }

    # Standings (format matches _get_standings output - keyed by team_id)
    standings = {
        "1": {  # Home team ID
            "position": 2,
            "points": 68,
            "played": 30,
            "goals_for": 72,
            "goals_against": 28,
            "form": "WWDWL"
        },
        "2": {  # Away team ID
            "position": 1,
            "points": 73,
            "played": 30,
            "goals_for": 68,
            "goals_against": 25,
            "form": "WWDWW"
        }
    }

    return MatchDetails(
        match=match,
        statistics=statistics,
        home_team_form=home_form,
        away_team_form=away_form,
        h2h_matches=h2h,
        odds=odds,
        standings=standings
    )


def test_prompt_generation():
    """Test the enhanced prompt generation."""
    print("=" * 70)
    print("TESTING ENHANCED CLAUDE PROMPT")
    print("=" * 70)

    match_data = create_test_match()
    
    # Create analyzer (will fail without API key, but we can still test prompt)
    try:
        analyzer = AIAnalyzer()
        prompt = analyzer._build_prompt(match_data)
        
        print("\n✅ PROMPT GENERATED SUCCESSFULLY\n")
        print("=" * 70)
        print("FULL PROMPT OUTPUT:")
        print("=" * 70)
        print(prompt)
        print("\n" + "=" * 70)
        print(f"📊 Total prompt length: {len(prompt)} characters")
        
        # Count sections (new format)
        sections = [
            "⚽ ЗАГОЛОВОК",
            "📝 ВСТУПЛЕНИЕ",
            "📊 ОСНОВНЫЕ ВЕРОЯТНОСТИ",
            "📈 ФОРМА",
            "🎯 H2H ТРЕНДЫ",
            "📌 КЛЮЧЕВЫЕ ФАКТОРЫ",
            "🎯 РЕКОМЕНДАЦИИ",
            "⚡ ВЕРДИКТ",
            "⚠️ ДИСКЛЕЙМЕР",
        ]
        
        print("\n" + "=" * 70)
        print("SECTION CHECK (new format):")
        print("=" * 70)
        for section in sections:
            if section in prompt:
                print(f"✓ {section}")
            else:
                print(f"✗ {section} - MISSING!")
        
        # Check data completeness (new format)
        print("\n" + "=" * 70)
        print("DATA COMPLETENESS CHECK (new format):")
        print("=" * 70)
        checks = [
            ("Match info", f"⚽ **{match_data.match.home_team}**" in prompt),
            ("Home form", "ФОРМА:" in prompt),
            ("Away form", f"{match_data.match.away_team}" in prompt),
            ("H2H history", "H2H" in prompt),
            ("Poisson stats", "ВЕРОЯТНОСТИ" in prompt),
            ("xG metrics", "xG" in prompt),
            ("Style info", "Стиль:" in prompt),
            ("Fatigue", "Усталость:" in prompt),
            ("Likely scores", "СЧЕТА" in prompt),
            ("Value bets", "РЫНОК:" in prompt),
        ]
        
        for check_name, result in checks:
            print(f"{'✓' if result else '✗'} {check_name}")
        
        return prompt
        
    except ValueError as e:
        print(f"\n⚠️ AIAnalyzer initialization failed (expected without API key): {e}")
        print("\nTesting prompt generation directly...")
        
        # Test without initializing analyzer
        from ai_analyzer import EnhancedPoissonCalculator
        
        calc = EnhancedPoissonCalculator()
        stats = calc.calculate_probabilities(match_data)
        
        print(f"\n✅ Poisson stats calculated:")
        print(f"   Home win: {stats['home_win_pct']}%")
        print(f"   Draw: {stats['draw_pct']}%")
        print(f"   Away win: {stats['away_win_pct']}%")
        print(f"   Over 2.5: {stats['over_2_5_pct']}%")
        print(f"   BTTS: {stats['btts_yes_pct']}%")
        print(f"   Expected goals: {stats['expected_total_goals']}")
        print(f"   Home style: {stats['home_style']}")
        print(f"   Away style: {stats['away_style']}")
        print(f"   H2H trend: {stats['h2h_trend']}")
        
        return None


if __name__ == "__main__":
    test_prompt_generation()
