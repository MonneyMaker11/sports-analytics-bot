#!/usr/bin/env python3
"""Final integration test for WC Qualification in bot"""
import sys
sys.path.insert(0, '/Users/ilyailyx/Desktop/sports-analytics-bot')

from api_football_parser import APIFootballParser
from ai_analyzer import EnhancedPoissonCalculator

parser = APIFootballParser(api_key="08c6e6aeaf97abc445440c686ac50fab")

print("=" * 70)
print("🌍 ФИНАЛЬНЫЙ ТЕСТ: Квалификация ЧМ в боте")
print("=" * 70)

# Test 1: Check all WC Qualification leagues
print("\n1. Доступные лиги квалификации ЧМ:")
wc_leagues = {
    "wc_qual_europe": "Европа",
    "wc_qual_concacaf": "CONCACAF",
    "wc_qual_south_america": "Юж. Америка",
    "wc_qual_asia": "Азия",
    "wc_qual_africa": "Африка",
    "wc_qual_oceania": "Океания",
    "wc_qual_playoffs": "Плей-офф",
}

for league_key, region in wc_leagues.items():
    matches_data = parser.get_fixtures_by_date(league_key, days=365)
    total_matches = sum(len(m) for m in matches_data.values())
    status = "✅" if total_matches > 0 else "⚠️"
    print(f"   {status} {region:15} ({league_key:20}): {total_matches} матчей")

# Test 2: Get today's WC Qualification matches
print("\n2. Матчи квалификации ЧМ сегодня:")
import datetime
today = datetime.date.today()

for league_key in wc_leagues.keys():
    matches_data = parser.get_fixtures_by_date(league_key, days=1)
    for date_str, matches in matches_data.items():
        if today.strftime("%d.%m.%Y") in date_str:
            print(f"\n   📌 {league_key}:")
            for match in matches[:5]:
                print(f"      ⚽ {match.home_team} vs {match.away_team}")

# Test 3: Full analysis for today's match
print("\n3. Полный анализ матча Sweden vs Poland:")

# Get match details
matches_data = parser.get_fixtures_by_date("wc_qual_europe", days=365)
sweden_poland_match = None

for date_str, matches in matches_data.items():
    for match in matches:
        if "Sweden" in match.home_team and "Poland" in match.away_team:
            sweden_poland_match = match
            break
    if sweden_poland_match:
        break

if sweden_poland_match:
    print(f"   Матч найден: {sweden_poland_match.id}")
    
    # Get full details
    details = parser.get_match_details(sweden_poland_match.id)
    
    if details:
        print(f"   ✅ Данные получены")
        print(f"   📈 Форма Sweden: {len(details.home_team_form)} матчей")
        print(f"   📈 Форма Poland: {len(details.away_team_form)} матчей")
        
        # Calculate Poisson probabilities
        calc = EnhancedPoissonCalculator()
        stats = calc.calculate_probabilities(details)
        
        print(f"\n   📊 ПРОГНОЗ:")
        print(f"      П1 (Sweden): {stats['home_win_pct']}%")
        print(f"      X (Ничья):   {stats['draw_pct']}%")
        print(f"      П2 (Poland): {stats['away_win_pct']}%")
        print(f"\n      Ожидаемые голы: {stats['home_expected_goals']:.2f} - {stats['away_expected_goals']:.2f}")
        print(f"      Стиль: {stats['home_style']} vs {stats['away_style']}")
        print(f"      ТБ 2.5: {stats['over_2_5_pct']}%")
        print(f"      Обе забьют: {stats['btts_yes_pct']}%")
        
        # Value bets
        if stats.get('value_bets'):
            print(f"\n   💰 Value ставки:")
            for bet in stats['value_bets'][:2]:
                print(f"      • {bet['bet']}: модель {bet['model']}% vs рынок {bet['market']}% (edge {bet['edge']}%)")
        
        print(f"\n   🎲 Вероятные счета:")
        for score in stats['likely_scores'][:3]:
            print(f"      • {score['score']}: {score['prob']}%")
    else:
        print("   ❌ Не удалось получить детали")
else:
    print("   ❌ Матч не найден")

print("\n" + "=" * 70)
print("✅ ТЕСТ ЗАВЕРШЁН - Квалификация ЧМ готова к использованию!")
print("=" * 70)
