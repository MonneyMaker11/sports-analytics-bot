"""
Test script to demonstrate enhanced analytics with diverse predictions.
"""

from api_football_parser import Match, MatchDetails
from ai_analyzer import EnhancedPoissonCalculator

# Create sample match data with different scenarios
def create_test_match(home_team, away_team, home_form, away_form, h2h=None):
    """Create test match with specific form patterns."""
    match = Match(
        id="test_001",
        date="2026-03-29",
        home_team=home_team,
        away_team=away_team,
        tournament="Premier League",
        home_score=None,
        away_score=None,
        status="NS"
    )
    
    return MatchDetails(
        match=match,
        home_team_form=home_form,
        away_team_form=away_form,
        h2h_matches=h2h or []
    )


# Scenario 1: Attacking team vs Defensive team
print("=" * 60)
print("СЦЕНАРИЙ 1: Атакующая команда vs Оборонительная")
print("=" * 60)

attacking_form = [
    {"opponent": "Team A", "result": "W", "score": "3:1", "date": 1711500000},
    {"opponent": "Team B", "result": "W", "score": "4:0", "date": 1711400000},
    {"opponent": "Team C", "result": "D", "score": "2:2", "date": 1711300000},
    {"opponent": "Team D", "result": "W", "score": "3:2", "date": 1711200000},
    {"opponent": "Team E", "result": "L", "score": "1:2", "date": 1711100000},
]

defensive_form = [
    {"opponent": "Team A", "result": "D", "score": "0:0", "date": 1711500000},
    {"opponent": "Team B", "result": "W", "score": "1:0", "date": 1711400000},
    {"opponent": "Team C", "result": "D", "score": "1:1", "date": 1711300000},
    {"opponent": "Team D", "result": "D", "score": "0:0", "date": 1711200000},
    {"opponent": "Team E", "result": "W", "score": "2:0", "date": 1711100000},
]

match1 = create_test_match("Man City", "Burnley", attacking_form, defensive_form)
calc = EnhancedPoissonCalculator()
stats1 = calc.calculate_probabilities(match1)

print(f"\n📊 Ожидаемые голы: {stats1['home_expected_goals']:.2f} - {stats1['away_expected_goals']:.2f}")
print(f"📈 Стиль: {stats1['home_style']} vs {stats1['away_style']}")
print(f"\n🎯 Вероятности:")
print(f"   П1: {stats1['home_win_pct']}% | X: {stats1['draw_pct']}% | П2: {stats1['away_win_pct']}%")
print(f"   ТБ 2.5: {stats1['over_2_5_pct']}% | ТМ 2.5: {stats1['under_2_5_pct']}%")
print(f"   Обе забьют: {stats1['btts_yes_pct']}% | Нет: {stats1['btts_no_pct']}%")
scores_str = ", ".join([f"{s['score']} ({s['prob']}%)" for s in stats1['likely_scores'][:3]])
print(f"\n🎲 Вероятные счета: {scores_str}")


# Scenario 2: Two defensive teams (low-scoring expected)
print("\n" + "=" * 60)
print("СЦЕНАРИЙ 2: Две оборонительные команды (низкий тотал)")
print("=" * 60)

def_home = [
    {"opponent": "Team A", "result": "D", "score": "0:0", "date": 1711500000},
    {"opponent": "Team B", "result": "D", "score": "1:1", "date": 1711400000},
    {"opponent": "Team C", "result": "W", "score": "1:0", "date": 1711300000},
    {"opponent": "Team D", "result": "D", "score": "0:0", "date": 1711200000},
    {"opponent": "Team E", "result": "L", "score": "0:1", "date": 1711100000},
]

def_away = [
    {"opponent": "Team A", "result": "D", "score": "0:0", "date": 1711500000},
    {"opponent": "Team B", "result": "D", "score": "0:0", "date": 1711400000},
    {"opponent": "Team C", "result": "D", "score": "1:1", "date": 1711300000},
    {"opponent": "Team D", "result": "W", "score": "1:0", "date": 1711200000},
    {"opponent": "Team E", "result": "D", "score": "0:0", "date": 1711100000},
]

match2 = create_test_match("Atletico", "Juventus", def_home, def_away)
stats2 = calc.calculate_probabilities(match2)

print(f"\n📊 Ожидаемые голы: {stats2['home_expected_goals']:.2f} - {stats2['away_expected_goals']:.2f}")
print(f"📈 Стиль: {stats2['home_style']} vs {stats2['away_style']}")
print(f"\n🎯 Вероятности:")
print(f"   П1: {stats2['home_win_pct']}% | X: {stats2['draw_pct']}% | П2: {stats2['away_win_pct']}%")
print(f"   ТБ 2.5: {stats2['over_2_5_pct']}% | ТМ 2.5: {stats2['under_2_5_pct']}%")
print(f"   Обе забьют: {stats2['btts_yes_pct']}% | Нет: {stats2['btts_no_pct']}%")
print(f"   0-1 гол: {stats2['goals_0_1_pct']}% | 2-3 гола: {stats2['goals_2_3_pct']}%")
scores_str2 = ", ".join([f"{s['score']} ({s['prob']}%)" for s in stats2['likely_scores'][:3]])
print(f"\n🎲 Вероятные счета: {scores_str2}")


# Scenario 3: Two attacking teams (high-scoring expected)
print("\n" + "=" * 60)
print("СЦЕНАРИЙ 3: Две атакующие команды (высокий тотал)")
print("=" * 60)

att_home = [
    {"opponent": "Team A", "result": "W", "score": "3:2", "date": 1711500000},
    {"opponent": "Team B", "result": "W", "score": "4:3", "date": 1711400000},
    {"opponent": "Team C", "result": "D", "score": "2:2", "date": 1711300000},
    {"opponent": "Team D", "result": "W", "score": "3:1", "date": 1711200000},
    {"opponent": "Team E", "result": "L", "score": "2:3", "date": 1711100000},
]

att_away = [
    {"opponent": "Team A", "result": "W", "score": "3:1", "date": 1711500000},
    {"opponent": "Team B", "result": "D", "score": "2:2", "date": 1711400000},
    {"opponent": "Team C", "result": "W", "score": "4:2", "date": 1711300000},
    {"opponent": "Team D", "result": "W", "score": "3:0", "date": 1711200000},
    {"opponent": "Team E", "result": "L", "score": "1:3", "date": 1711100000},
]

match3 = create_test_match("Liverpool", "Dortmund", att_home, att_away)
stats3 = calc.calculate_probabilities(match3)

print(f"\n📊 Ожидаемые голы: {stats3['home_expected_goals']:.2f} - {stats3['away_expected_goals']:.2f}")
print(f"📈 Стиль: {stats3['home_style']} vs {stats3['away_style']}")
print(f"\n🎯 Вероятности:")
print(f"   П1: {stats3['home_win_pct']}% | X: {stats3['draw_pct']}% | П2: {stats3['away_win_pct']}%")
print(f"   ТБ 2.5: {stats3['over_2_5_pct']}% | ТМ 2.5: {stats3['under_2_5_pct']}%")
print(f"   Обе забьют: {stats3['btts_yes_pct']}% | Нет: {stats3['btts_no_pct']}%")
print(f"   4+ голов: {stats3['goals_4+_pct']}%")
scores_str3 = ", ".join([f"{s['score']} ({s['prob']}%)" for s in stats3['likely_scores'][:3]])
print(f"\n🎲 Вероятные счета: {scores_str3}")


# Scenario 4: H2H dominance effect
print("\n" + "=" * 60)
print("СЦЕНАРИЙ 4: Влияние H2H тренда")
print("=" * 60)

h2h_dominance = [
    {"home_team": "Team X", "away_team": "Team Y", "home_score": 2, "away_score": 0, "date": 1700000000},
    {"home_team": "Team Y", "away_team": "Team X", "home_score": 0, "away_score": 3, "date": 1690000000},
    {"home_team": "Team X", "away_team": "Team Y", "home_score": 1, "away_score": 0, "date": 1680000000},
    {"home_team": "Team Y", "away_team": "Team X", "home_score": 1, "away_score": 2, "date": 1670000000},
]

neutral_form = [
    {"opponent": "Team A", "result": "W", "score": "1:0", "date": 1711500000},
    {"opponent": "Team B", "result": "D", "score": "1:1", "date": 1711400000},
    {"opponent": "Team C", "result": "W", "score": "2:1", "date": 1711300000},
    {"opponent": "Team D", "result": "L", "score": "0:1", "date": 1711200000},
    {"opponent": "Team E", "result": "W", "score": "1:0", "date": 1711100000},
]

match4 = create_test_match("Team X", "Team Y", neutral_form, neutral_form, h2h_dominance)
stats4 = calc.calculate_probabilities(match4)

print(f"\n📊 Ожидаемые голы: {stats4['home_expected_goals']:.2f} - {stats4['away_expected_goals']:.2f}")
print(f"📈 H2H тренд: {stats4['h2h_trend']}")
print(f"\n🎯 Вероятности:")
print(f"   П1: {stats4['home_win_pct']}% | X: {stats4['draw_pct']}% | П2: {stats4['away_win_pct']}%")
print(f"   ТБ 2.5: {stats4['over_2_5_pct']}% | ТМ 2.5: {stats4['under_2_5_pct']}%")
print(f"   Обе забьют: {stats4['btts_yes_pct']}%")
scores_str4 = ", ".join([f"{s['score']} ({s['prob']}%)" for s in stats4['likely_scores'][:3]])
print(f"\n🎲 Вероятные счета: {scores_str4}")


# Summary comparison
print("\n" + "=" * 60)
print("📊 СРАВНЕНИЕ ВСЕХ СЦЕНАРИЕВ")
print("=" * 60)

scenarios = [
    ("Атака vs Защита", stats1),
    ("Защита vs Защита", stats2),
    ("Атака vs Атака", stats3),
    ("H2H доминирование", stats4),
]

print(f"\n{'Сценарий':<25} {'Тотал':<8} {'ТБ 2.5%':<10} {'Обе заб%':<10} {'П1%':<8} {'X%':<6} {'П2%':<6}")
print("-" * 75)

for name, stats in scenarios:
    total = stats['expected_total_goals']
    over = stats['over_2_5_pct']
    btts = stats['btts_yes_pct']
    h = stats['home_win_pct']
    d = stats['draw_pct']
    a = stats['away_win_pct']
    print(f"{name:<25} {total:<8.2f} {over:<10} {btts:<10} {h:<8} {d:<6} {a:<6}")

print("\n✅ Разнообразие прогнозов достигнуто за счёт:")
print("   1. Учёта стиля игры (атакующий/оборонительный)")
print("   2. Фактора усталости команд")
print("   3. H2H трендов")
print("   4. Match-specific variance (±20%)")
print("   5. xG-метрик вместо простых голов")
