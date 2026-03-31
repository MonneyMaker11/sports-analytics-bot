"""
Advanced Probability Calculator - Ideal Version
Combines multiple data sources for realistic probabilities:
1. Market odds (primary - most accurate)
2. Team form & stats (secondary)
3. FIFA/ELO ratings (for national teams)
4. Poisson model (tertiary)
"""

import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dotenv import load_dotenv

from api_football_parser import APIFootballParser, MatchDetails

logger = logging.getLogger(__name__)
load_dotenv()


class IdealProbabilityCalculator:
    """
    Professional-grade probability calculator.
    Priority: Market Odds > Team Form > Statistical Model
    """

    # League average goals (2025-26 season data)
    LEAGUE_AVG_GOALS = {
        "premier_league": 2.85,
        "la_liga": 2.65,
        "bundesliga": 3.10,
        "serie_a": 2.70,
        "ligue_1": 2.55,
        "champions_league": 2.90,
        "europa_league": 2.75,
        "wc_qual_europe": 2.45,
        "default": 2.70
    }

    # Home advantage by league (2025-26 data)
    HOME_ADVANTAGE = {
        "premier_league": 1.12,
        "la_liga": 1.15,
        "bundesliga": 1.08,
        "serie_a": 1.14,
        "ligue_1": 1.16,
        "champions_league": 1.05,
        "europa_league": 1.08,
        "wc_qual_europe": 1.06,  # National teams - lower home advantage
        "default": 1.12
    }

    def __init__(self, parser: APIFootballParser):
        self.parser = parser

    def calculate_ideal_probabilities(self, match_data: MatchDetails) -> Dict[str, Any]:
        """
        Calculate probabilities using the ideal multi-source approach.
        
        Priority:
        1. Market odds (60-80% weight) - most accurate reflection of reality
        2. Team form (15-30% weight) - recent performance
        3. Statistical model (5-10% weight) - Poisson with adjustments
        """
        match = match_data.match
        league_key = self._get_league_key(match.tournament)
        is_national = self._is_national_teams_match(match_data)

        result = {
            "match": f"{match.home_team} vs {match.away_team}",
            "tournament": match.tournament,
            "is_national": is_national,
            "league_key": league_key
        }

        # === STEP 1: Extract Market Odds (HIGHEST PRIORITY) ===
        market_data = self._extract_market_odds(match_data.odds)
        result["market"] = market_data

        if market_data["available"] and market_data["home_odd"] and market_data["away_odd"]:
            # Calculate market-implied probabilities (remove vig)
            market_probs = self._calculate_market_probabilities(
                market_data["home_odd"],
                market_data["draw_odd"],
                market_data["away_odd"]
            )
            result["market_probs"] = market_probs
            result["vig_removed"] = True

            # Market weight depends on data availability
            market_weight = 0.75 if is_national else 0.70
            form_weight = 0.20 if is_national else 0.25
            model_weight = 0.05 if is_national else 0.05

            result["weights"] = {
                "market": market_weight,
                "form": form_weight,
                "model": model_weight
            }
        else:
            # No market odds - use form + model
            market_probs = None
            market_weight = 0.0
            form_weight = 0.60
            model_weight = 0.40

            result["weights"] = {
                "market": 0.0,
                "form": form_weight,
                "model": model_weight
            }
            logger.warning(f"No market odds for {match.home_team} vs {match.away_team}")

        # === STEP 2: Calculate Form-Based Probabilities ===
        form_data = self._analyze_team_form(match_data)
        result["form"] = form_data

        form_probs = self._calculate_form_probabilities(
            form_data,
            league_key,
            is_national
        )
        result["form_probs"] = form_probs

        # === STEP 3: Calculate Model-Based Probabilities (Poisson) ===
        model_data = self._calculate_model_probs(match_data, league_key, is_national)
        result["model"] = model_data
        model_probs = model_data["probs"]
        result["model_probs"] = model_probs

        # === STEP 4: Blend All Sources ===
        final_probs = self._blend_probabilities(
            market_probs=market_probs,
            form_probs=form_probs,
            model_probs=model_probs,
            weights=result["weights"]
        )

        result["final"] = final_probs

        # === STEP 5: Add Confidence Score ===
        result["confidence"] = self._calculate_confidence(
            market_data=market_data,
            form_data=form_data,
            is_national=is_national
        )

        # === STEP 6: Add Value Bets ===
        result["value_bets"] = self._find_value_bets(
            final_probs=final_probs,
            market_odds=market_data
        )

        logger.info(
            f"Ideal: {match.home_team} {final_probs['home_win_pct']:.0f}% | "
            f"X {final_probs['draw_pct']:.0f}% | "
            f"{match.away_team} {final_probs['away_win_pct']:.0f}% "
            f"(Market: {market_data['available']}, Confidence: {result['confidence']['score']})"
        )

        return result

    def _extract_market_odds(self, odds: Dict) -> Dict[str, Any]:
        """Extract best available market odds from multiple bookmakers."""
        result = {
            "available": False,
            "home_odd": None,
            "draw_odd": None,
            "away_odd": None,
            "bookmakers_count": 0,
            "best_home_odd": None,
            "best_away_odd": None
        }

        if not odds:
            return result

        # Handle nested structure
        odds_list = odds.get("odds", []) if isinstance(odds, dict) else odds
        if not isinstance(odds_list, list):
            return result

        bookmakers = []
        home_odds = []
        draw_odds = []
        away_odds = []

        for bk in odds_list:
            if not isinstance(bk, dict):
                continue

            bk_name = bk.get("name", "Unknown")
            markets = bk.get("markets", [])

            if not isinstance(markets, list):
                continue

            for mkt in markets:
                if not isinstance(mkt, dict):
                    continue

                mkt_name = mkt.get("name", "").lower()

                # Only use "Match Winner" market for 1X2
                if "match winner" not in mkt_name:
                    continue

                values = mkt.get("values", [])
                if not isinstance(values, list):
                    continue

                for val in values:
                    if not isinstance(val, dict):
                        continue

                    label = str(val.get("value", "")).lower()
                    odd = val.get("odd")

                    try:
                        odd_float = float(odd) if odd else None
                        if not odd_float or odd_float < 1.01:
                            continue

                        if label in ["home", "1"]:
                            home_odds.append(odd_float)
                        elif label in ["draw", "x"]:
                            draw_odds.append(odd_float)
                        elif label in ["away", "2"]:
                            away_odds.append(odd_float)
                    except (ValueError, TypeError):
                        continue

            if home_odds or draw_odds or away_odds:
                bookmakers.append(bk_name)

        result["bookmakers_count"] = len(bookmakers)
        result["bookmakers"] = bookmakers[:5]  # Top 5

        if home_odds and draw_odds and away_odds:
            result["available"] = True
            # Use average odds (or best - could be configurable)
            result["home_odd"] = sum(home_odds) / len(home_odds)
            result["draw_odd"] = sum(draw_odds) / len(draw_odds)
            result["away_odd"] = sum(away_odds) / len(away_odds)
            result["best_home_odd"] = max(home_odds)
            result["best_away_odd"] = max(away_odds)

        return result

    def _calculate_market_probabilities(
        self,
        home_odd: float,
        draw_odd: float,
        away_odd: float
    ) -> Dict[str, float]:
        """
        Calculate probabilities from market odds with vig removal.
        Uses proportional method for fair probabilities.
        """
        # Raw implied probabilities
        home_implied = 1 / home_odd
        draw_implied = 1 / draw_odd
        away_implied = 1 / away_odd

        # Total market (includes vig)
        total_implied = home_implied + draw_implied + away_implied

        # Vig (overround)
        vig = total_implied - 1.0
        vig_pct = vig * 100

        # Remove vig proportionally
        home_prob = (home_implied / total_implied) * 100
        draw_prob = (draw_implied / total_implied) * 100
        away_prob = (away_implied / total_implied) * 100

        # Ensure exactly 100%
        total = home_prob + draw_prob + away_prob
        home_prob = round(home_prob / total * 100, 1)
        draw_prob = round(draw_prob / total * 100, 1)
        away_prob = round(away_prob / total * 100, 1)

        return {
            "home_win_pct": home_prob,
            "draw_pct": draw_prob,
            "away_win_pct": away_prob,
            "vig_pct": round(vig_pct, 2),
            "source": "market"
        }

    def _analyze_team_form(self, match_data: MatchDetails) -> Dict[str, Any]:
        """Analyze team form from recent matches."""
        home_form = match_data.home_team_form[:5]
        away_form = match_data.away_team_form[:5]

        def calc_form_stats(form: List[Dict], is_home: bool) -> Dict:
            if not form:
                return {
                    "points_per_game": 1.0,
                    "goals_scored_avg": 1.35,
                    "goals_conceded_avg": 1.35,
                    "form_rating": 1.0,
                    "results": ""
                }

            points = 0
            goals_scored = 0
            goals_conceded = 0
            results = []

            for m in form:
                score = m.get("score", "0:0")
                result = m.get("result", "?")
                results.append(result)

                try:
                    parts = score.split(":")
                    if len(parts) == 2:
                        gs = int(parts[0]) if parts[0].isdigit() else 0
                        gc = int(parts[1]) if parts[1].isdigit() else 0
                        goals_scored += gs
                        goals_conceded += gc
                except:
                    pass

                if result == "W":
                    points += 3
                elif result == "D":
                    points += 1

            n = len(form)
            form_rating = points / (n * 3)  # 0-1 scale

            return {
                "points_per_game": points / n,
                "goals_scored_avg": goals_scored / n,
                "goals_conceded_avg": goals_conceded / n,
                "form_rating": form_rating,
                "results": "".join(results)
            }

        home_stats = calc_form_stats(home_form, is_home=True)
        away_stats = calc_form_stats(away_form, is_home=False)

        return {
            "home": home_stats,
            "away": away_stats,
            "home_form_raw": home_form,
            "away_form_raw": away_form
        }

    def _calculate_form_probabilities(
        self,
        form_data: Dict,
        league_key: str,
        is_national: bool
    ) -> Dict[str, float]:
        """Calculate probabilities based on team form."""
        home = form_data["home"]
        away = form_data["away"]

        # Form strength (0-2 scale, 1 = average)
        home_strength = home["form_rating"] * 2
        away_strength = away["form_rating"] * 2

        # Goal-based adjustment
        home_attack = home["goals_scored_avg"] / 1.35
        home_defense = 1.35 / max(home["goals_conceded_avg"], 0.5)
        away_attack = away["goals_scored_avg"] / 1.35
        away_defense = 1.35 / max(away["goals_conceded_avg"], 0.5)

        # Expected goals from form
        home_xg = (home_attack * away_defense) * self.HOME_ADVANTAGE.get(league_key, 1.12)
        away_xg = (away_attack * home_defense)

        # Simple probability from xG
        total_xg = home_xg + away_xg
        if total_xg > 0:
            home_base = home_xg / total_xg * 100
            away_base = away_xg / total_xg * 100
        else:
            home_base = away_base = 50

        # Draw probability based on strength similarity
        strength_diff = abs(home_strength - away_strength)
        draw_base = 25 - strength_diff * 5  # Less draw if teams very different
        draw_base = max(15, min(30, draw_base))

        # Normalize
        remaining = 100 - draw_base
        total_base = home_base + away_base
        home_prob = home_base / total_base * remaining
        away_prob = away_base / total_base * remaining

        return {
            "home_win_pct": round(home_prob, 1),
            "draw_pct": round(draw_base, 1),
            "away_win_pct": round(away_prob, 1),
            "source": "form"
        }

    def _calculate_model_probs(
        self,
        match_data: MatchDetails,
        league_key: str,
        is_national: bool
    ) -> Dict[str, Any]:
        """Calculate Poisson-based model probabilities with realistic adjustments."""
        from ai_analyzer import EnhancedPoissonCalculator

        calc = EnhancedPoissonCalculator()
        probs = calc.calculate_probabilities(match_data)

        # Override with more conservative estimates for national teams
        if is_national:
            # National teams: regress toward mean
            league_avg = self.LEAGUE_AVG_GOALS.get(league_key, 2.70)
            expected_total = probs.get("expected_total_goals", league_avg)

            # Regress expected goals toward league average
            regressed_total = expected_total * 0.7 + league_avg * 0.3
            probs["expected_total_goals"] = round(regressed_total, 2)

        return {
            "probs": probs,
            "expected_goals": probs.get("expected_total_goals", 2.70),
            "home_xg": probs.get("home_expected_goals", 1.35),
            "away_xg": probs.get("away_expected_goals", 1.35)
        }

    def _blend_probabilities(
        self,
        market_probs: Optional[Dict],
        form_probs: Dict,
        model_probs: Dict,
        weights: Dict[str, float]
    ) -> Dict[str, float]:
        """Blend probabilities from all sources."""
        market_w = weights.get("market", 0.0)
        form_w = weights.get("form", 0.0)
        model_w = weights.get("model", 0.0)

        # Start with market if available
        if market_probs and market_w > 0:
            home = market_probs["home_win_pct"] * market_w
            draw = market_probs["draw_pct"] * market_w
            away = market_probs["away_win_pct"] * market_w
        else:
            home = draw = away = 0.0

        # Add form component
        if form_w > 0:
            home += form_probs["home_win_pct"] * form_w
            draw += form_probs["draw_pct"] * form_w
            away += form_probs["away_win_pct"] * form_w

        # Add model component
        if model_w > 0:
            home += model_probs["home_win_pct"] * model_w
            draw += model_probs["draw_pct"] * model_w
            away += model_probs["away_win_pct"] * model_w

        # Normalize to 100%
        total = home + draw + away
        if total > 0:
            home = home / total * 100
            draw = draw / total * 100
            away = away / total * 100

        # Round and ensure exactly 100%
        home = round(home)
        draw = round(draw)
        away = 100 - home - draw

        return {
            "home_win_pct": int(home),
            "draw_pct": int(draw),
            "away_win_pct": int(away),
            "expected_total_goals": model_probs.get("expected_total_goals", 2.70),
            "over_2_5_pct": model_probs.get("over_2_5_pct", 50),
            "btts_yes_pct": model_probs.get("btts_yes_pct", 50)
        }

    def _calculate_confidence(
        self,
        market_data: Dict,
        form_data: Dict,
        is_national: bool
    ) -> Dict[str, Any]:
        """Calculate confidence score for the prediction."""
        score = 0
        factors = []

        # Market availability (highest impact)
        if market_data["available"]:
            score += 40
            factors.append("market_odds")
            if market_data["bookmakers_count"] >= 3:
                score += 10
                factors.append("multiple_bookmakers")
        else:
            factors.append("no_market")

        # Form data quality
        home_form = form_data["home"]["results"]
        away_form = form_data["away"]["results"]

        if len(home_form) >= 5 and "?" not in home_form:
            score += 15
            factors.append("home_form")
        if len(away_form) >= 5 and "?" not in away_form:
            score += 15
            factors.append("away_form")

        # National teams get slight penalty (less predictable)
        if is_national:
            score -= 10
            factors.append("national_penalty")

        # Cap at 100
        score = min(100, max(0, score))

        # Rating
        if score >= 80:
            rating = "VERY HIGH"
        elif score >= 60:
            rating = "HIGH"
        elif score >= 40:
            rating = "MEDIUM"
        else:
            rating = "LOW"

        return {
            "score": score,
            "rating": rating,
            "factors": factors
        }

    def _find_value_bets(
        self,
        final_probs: Dict,
        market_odds: Dict
    ) -> List[Dict]:
        """Find value bets where our probability > market probability."""
        value_bets = []

        if not market_odds["available"]:
            return value_bets

        bets = [
            ("home_win_pct", "home_odd", "П1"),
            ("draw_pct", "draw_odd", "X"),
            ("away_win_pct", "away_odd", "П2")
        ]

        for prob_key, odd_key, label in bets:
            our_prob = final_probs.get(prob_key, 0)
            odd = market_odds.get(odd_key)

            if odd and odd > 1:
                market_prob = 1 / odd * 100
                edge = our_prob - market_prob

                if edge >= 5:  # At least 5% edge
                    value_bets.append({
                        "bet": label,
                        "our_prob": our_prob,
                        "market_prob": round(market_prob, 1),
                        "odd": odd,
                        "edge": round(edge, 1),
                        "recommendation": "VALUE" if edge >= 10 else "CONSIDER"
                    })

        return sorted(value_bets, key=lambda x: x["edge"], reverse=True)[:3]

    def _get_league_key(self, tournament: str) -> str:
        """Extract league key from tournament name."""
        if not tournament:
            return "default"

        name = tournament.lower()
        mapping = {
            "premier": "premier_league",
            "la liga": "la_liga",
            "bundesliga": "bundesliga",
            "serie a": "serie_a",
            "ligue 1": "ligue_1",
            "champions": "champions_league",
            "europa": "europa_league",
            "world cup": "wc_qual_europe",
            "wc qual": "wc_qual_europe",
            "qualification": "wc_qual_europe"
        }

        for key, value in mapping.items():
            if key in name:
                return value
        return "default"

    def _is_national_teams_match(self, match_data: MatchDetails) -> bool:
        """Check if this is a national teams match."""
        tournament = match_data.match.tournament.lower() if match_data.match.tournament else ""
        keywords = ["world cup", "wc qual", "euro", "nations league", "copa america", "qualification"]
        return any(kw in tournament for kw in keywords)

    def format_analysis(self, result: Dict) -> str:
        """Format the analysis for display."""
        lines = []

        # Header
        lines.append(f"📊 **IDEAL ANALYSIS** ({result['match']})")
        lines.append(f"🏆 {result['tournament']}")
        lines.append("")

        # Market odds
        market = result["market"]
        if market["available"]:
            lines.append(f"💰 **КОЭФФИЦИЕНТЫ БУКМЕКЕРОВ** ({market['bookmakers_count']} БК):")
            lines.append(f"   П1: {market['home_odd']:.2f} | X: {market['draw_odd']:.2f} | П2: {market['away_odd']:.2f}")
            if market.get("best_home_odd") and market.get("best_away_odd"):
                lines.append(f"   Лучшие: П1 {market['best_home_odd']:.2f} | П2 {market['best_away_odd']:.2f}")
            lines.append("")

        # Final probabilities
        final = result["final"]
        lines.append(f"🎯 **ВЕРОЯТНОСТИ** (Confidence: {result['confidence']['rating']})")
        lines.append(f"   П1: {final['home_win_pct']}% | X: {final['draw_pct']}% | П2: {final['away_win_pct']}%")
        lines.append("")

        # Form
        form = result["form"]
        lines.append(f"📈 **ФОРМА КОМАНД:**")
        lines.append(f"   🏠 {form['home']['results']} (PPG: {form['home']['points_per_game']:.1f})")
        lines.append(f"   ✈️ {form['away']['results']} (PPG: {form['away']['points_per_game']:.1f})")
        lines.append("")

        # Goals
        lines.append(f"⚽ **ГОЛЫ:**")
        lines.append(f"   Ожидаемый тотал: {final['expected_total_goals']}")
        lines.append(f"   ТМ 2.5: {100 - final['over_2_5_pct']}% | ТБ 2.5: {final['over_2_5_pct']}%")
        lines.append(f"   Обе забьют: {final['btts_yes_pct']}%")
        lines.append("")

        # Value bets
        if result["value_bets"]:
            lines.append(f"💎 **VALUE BETS:**")
            for bet in result["value_bets"]:
                lines.append(
                    f"   {bet['bet']} @ {bet['odd']:.2f} "
                    f"(Мы: {bet['our_prob']}% vs Рынок: {bet['market_prob']}%, Edge: {bet['edge']}%)"
                )
            lines.append("")

        # Methodology note
        weights = result["weights"]
        lines.append(f"ℹ️ _Метод: {'Market' if weights['market'] > 0 else 'Form'} "
                    f"({weights['market']*100:.0f}%) + "
                    f"Form ({weights['form']*100:.0f}%) + "
                    f"Model ({weights['model']*100:.0f}%)_")

        return "\n".join(lines)
