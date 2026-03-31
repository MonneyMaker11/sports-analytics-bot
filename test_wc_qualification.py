#!/usr/bin/env python3
"""Test World Cup Qualification matches in bot"""
import sys
sys.path.insert(0, '/Users/ilyailyx/Desktop/sports-analytics-bot')

from api_football_parser import APIFootballParser
import datetime

# Initialize parser
parser = APIFootballParser(api_key="08c6e6aeaf97abc445440c686ac50fab")

print("=== Тестирование квалификации ЧМ в боте ===\n")

# Test 1: Get fixtures for WC Qualification Europe
print("1. Получаем матчи квалификации ЧМ (Европа) на сегодня...")
today = datetime.date.today()
matches_data = parser.get_fixtures_by_date("wc_qual_europe", days=1)

if matches_data:
    for date, matches in matches_data.items():
        print(f"\n   📅 {date}:")
        for match in matches:
            print(f"      ⚽ {match.home_team} vs {match.away_team}")
            print(f"         ID: {match.id} | Статус: {match.status}")
else:
    print("   ❌ Матчи не найдены")

# Test 2: Get match details for one of today's matches
print("\n\n2. Получаем детальную статистику матча...")

# Find a match ID from today's fixtures
today_str = today.strftime("%d.%m.%Y")
wc_matches = []
for date, matches in matches_data.items():
    if today_str in date:
        wc_matches = matches
        break

details = None  # Initialize details variable

if wc_matches:
    match_id = wc_matches[0].id
    print(f"   Выбираем матч: {wc_matches[0].home_team} vs {wc_matches[0].away_team}")
    print(f"   ID: {match_id}\n")
    
    details = parser.get_match_details(match_id)
    
    if details:
        match = details.match
        print(f"   ✅ Матч: {match.home_team} vs {match.away_team}")
        print(f"   ✅ Турнир: {match.tournament}")
        print(f"   ✅ Форма хозяев: {len(details.home_team_form)} матчей")
        print(f"   ✅ Форма гостей: {len(details.away_team_form)} матчей")
        print(f"   ✅ H2H: {len(details.h2h_matches)} матчей")
        
        if details.home_team_form:
            print(f"\n   📈 Форма хозяев (последние 5):")
            for m in details.home_team_form[:5]:
                print(f"      {m['result']} vs {m['opponent']}: {m['score']}")
        
        if details.away_team_form:
            print(f"\n   📈 Форма гостей (последние 5):")
            for m in details.away_team_form[:5]:
                print(f"      {m['result']} vs {m['opponent']}: {m['score']}")
        
        if details.h2h_matches:
            print(f"\n   🎯 H2H (последние 5):")
            for m in details.h2h_matches[:5]:
                print(f"      {m['home_team']} {m['home_score']}:{m['away_score']} {m['away_team']}")
        
        if details.standings:
            print(f"\n   📋 Турнирное положение:")
            for team_id, data in details.standings.items():
                print(f"      {data.get('position', '?')} место | {data.get('points', 0)} очк | Форма: {data.get('form', '?????')}")
    else:
        print("   ❌ Не удалось получить детали матча")
else:
    print("   ❌ Нет матчей для тестирования")

# Test 3: Test Poisson calculator
print("\n\n3. Тестирование Poisson-калькулятора...")
if details:
    from ai_analyzer import EnhancedPoissonCalculator
    
    calc = EnhancedPoissonCalculator()
    stats = calc.calculate_probabilities(details)
    
    print(f"\n   📊 Ожидаемые голы: {stats['home_expected_goals']:.2f} - {stats['away_expected_goals']:.2f}")
    print(f"   📈 Стиль: {stats['home_style']} vs {stats['away_style']}")
    print(f"   🎯 П1: {stats['home_win_pct']}% | X: {stats['draw_pct']}% | П2: {stats['away_win_pct']}%")
    print(f"   ⚽ ТБ 2.5: {stats['over_2_5_pct']}% | ТМ 2.5: {stats['under_2_5_pct']}%")
    print(f"   🎯 Обе забьют: {stats['btts_yes_pct']}%")
    
    scores_str = ", ".join([f"{s['score']} ({s['prob']}%)" for s in stats['likely_scores'][:3]])
    print(f"   🎲 Вероятные счета: {scores_str}")
else:
    print("   ❌ Пропускаем (нет данных матча)")

print("\n✅ Тестирование завершено!")
