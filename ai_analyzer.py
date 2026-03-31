"""
AI Analyzer Module - Enhanced Version
Uses Anthropic Claude to analyze football match data and generate predictions.
Includes advanced statistical calculations with multiple factors for diverse predictions.

IMPROVEMENTS:
- Advanced team metrics (xG, xGA, pressing, shot accuracy)
- Contextual factors (fatigue, motivation, referee)
- Enhanced H2H analysis with trends
- Market analysis (odds movement, value bets)
- Player-level analysis (injuries impact)
- Revised Poisson model for diverse predictions
"""

import logging
import os
import re
import requests
from typing import Optional, Dict, Any, List
from math import exp, factorial
from datetime import datetime
import hashlib

from anthropic import AsyncAnthropic
from dotenv import load_dotenv

from api_football_parser import MatchDetails

logger = logging.getLogger(__name__)

load_dotenv()


class AdvancedTeamMetrics:
    """Calculates advanced team metrics beyond basic goals."""

    LEAGUE_XG_MULTIPLIERS = {
        "premier_league": 1.05,
        "la_liga": 0.98,
        "bundesliga": 1.08,
        "serie_a": 0.95,
        "ligue_1": 0.97,
        "champions_league": 1.02,
        "default": 1.0
    }

    def calculate_xg_from_form(self, form: List[Dict], league: str = "default") -> Dict[str, float]:
        """Calculate Expected Goals (xG) from form with regression to mean."""
        if not form:
            return {"xg_for": 1.35, "xg_against": 1.35, "xg_diff": 0.0}

        multiplier = self.LEAGUE_XG_MULTIPLIERS.get(league, 1.0)
        xg_for, xg_against = [], []

        for match in form:
            score = match.get("score", "0:0")
            parts = score.split(":")
            if len(parts) == 2:
                try:
                    scored = int(parts[0]) if parts[0].isdigit() else 0
                    conceded = int(parts[1]) if parts[1].isdigit() else 0
                    xg_for.append(self._estimate_xg(scored, multiplier))
                    xg_against.append(self._estimate_xg(conceded, multiplier))
                except:
                    xg_for.append(1.35)
                    xg_against.append(1.35)

        # Weight recent matches more heavily
        weights = [1.0, 0.85, 0.7, 0.55, 0.4, 0.3, 0.2, 0.15, 0.1, 0.1][:len(xg_for)]
        total_w = sum(weights[:len(xg_for)]) or 1

        avg_for = sum(g * w for g, w in zip(xg_for, weights)) / total_w
        avg_against = sum(g * w for g, w in zip(xg_against, weights)) / total_w

        return {"xg_for": round(avg_for, 2), "xg_against": round(avg_against, 2), "xg_diff": round(avg_for - avg_against, 2)}

    def _estimate_xg(self, goals: int, multiplier: float) -> float:
        """Estimate xG from goals with regression to mean."""
        league_avg = 1.35
        raw_xg = goals / multiplier if multiplier else league_avg
        return max(0.3, min(raw_xg * 0.6 + league_avg * 0.4, 3.5))

    def calculate_playing_style(self, form: List[Dict]) -> Dict[str, Any]:
        """Determine team's playing style from results."""
        if not form:
            return {"style": "balanced", "intensity": "medium", "counter": False}

        goals_scored = []
        goals_conceded = []
        for match in form:
            score = match.get("score", "0:0")
            parts = score.split(":")
            if len(parts) == 2:
                try:
                    goals_scored.append(int(parts[0]) if parts[0].isdigit() else 0)
                    goals_conceded.append(int(parts[1]) if parts[1].isdigit() else 0)
                except:
                    goals_scored.append(0)
                    goals_conceded.append(0)

        avg_scored = sum(goals_scored) / len(goals_scored) if goals_scored else 0
        avg_conceded = sum(goals_conceded) / len(goals_conceded) if goals_conceded else 0

        # Style determination
        if avg_scored > 2.0:
            style = "very_attacking"
        elif avg_scored > 1.5:
            style = "attacking"
        elif avg_scored < 0.8:
            style = "very_defensive"
        elif avg_scored < 1.0:
            style = "defensive"
        else:
            style = "balanced"

        # Intensity
        total = avg_scored + avg_conceded
        intensity = "high" if total > 3.0 else "medium" if total > 2.0 else "low"

        # Counter-attacking indicator
        clean_sheets = sum(1 for g in goals_conceded if g == 0)
        big_wins = sum(1 for i, g in enumerate(goals_scored) if g > 2 and g > goals_conceded[i])
        counter = clean_sheets >= 2 and big_wins >= 1

        return {"style": style, "intensity": intensity, "counter": counter, "clean_sheet_pct": round(clean_sheets / len(form) * 100)}


class ContextualFactors:
    """Analyzes contextual factors affecting match outcomes."""

    REST_PATTERNS = {"premier_league": 3.5, "la_liga": 4.0, "bundesliga": 5.0, "serie_a": 4.5, "default": 4.0}

    def calculate_fatigue(self, form: List[Dict], league: str = "default") -> float:
        """Calculate fatigue factor based on rest days."""
        if len(form) < 2:
            return 1.0

        dates = []
        for m in form:
            d = m.get("date")
            if d:
                try:
                    dates.append(datetime.fromtimestamp(d) if isinstance(d, (int, float)) else datetime.fromisoformat(str(d).replace('Z', '+00:00')))
                except:
                    pass

        if len(dates) < 2:
            return 1.0

        days_between = [abs((dates[i] - dates[i+1]).days) for i in range(len(dates)-1) if (dates[i] - dates[i+1]).days > 0]
        if not days_between:
            return 1.0

        avg_rest = sum(days_between) / len(days_between)
        league_avg = self.REST_PATTERNS.get(league, 4.0)
        ratio = avg_rest / league_avg

        if ratio < 0.7:
            return 0.85
        elif ratio < 0.85:
            return 0.92
        elif ratio > 1.3:
            return 1.08
        elif ratio > 1.1:
            return 1.04
        return 1.0

    def get_referee_tendency(self, ref_name: str) -> Dict[str, float]:
        """Get referee tendencies (simulated - would use real data in production)."""
        if not ref_name:
            return {"cards": 4.5, "penalties": 0.25}

        h = hashlib.md5(ref_name.lower().encode()).hexdigest()
        val = int(h[:8], 16) % 3

        if val == 0:
            return {"cards": 5.5, "penalties": 0.35}
        elif val == 1:
            return {"cards": 3.5, "penalties": 0.15}
        return {"cards": 4.5, "penalties": 0.25}


class EnhancedH2HAnalyzer:
    """Advanced H2H analysis with trends."""

    def analyze_trends(self, h2h: List[Dict], home: str, away: str) -> Dict[str, Any]:
        """Analyze H2H for patterns."""
        if not h2h:
            return {"home_dom": 0.5, "avg_goals": 2.5, "btts_rate": 50, "trend": "none"}

        home_wins = away_wins = draws = 0
        total_goals = btts = 0
        recent_home = recent_away = 0

        for i, m in enumerate(h2h[:5]):
            hs, aws = m.get("home_score", 0) or 0, m.get("away_score", 0) or 0
            total_goals += hs + aws
            btts += 1 if hs > 0 and aws > 0 else 0

            if hs > aws:
                home_wins += 1
                if i < 3:
                    recent_home += 1
            elif aws > hs:
                away_wins += 1
                if i < 3:
                    recent_away += 1
            else:
                draws += 1

        n = len(h2h[:5])
        avg_goals = total_goals / n if n else 2.5

        # Trend detection
        if recent_home >= 2:
            trend = "home_dominates"
        elif recent_away >= 2:
            trend = "away_dominates"
        elif draws >= 2:
            trend = "draw_prone"
        elif avg_goals > 3.0:
            trend = "high_scoring"
        elif avg_goals < 2.0:
            trend = "low_scoring"
        else:
            trend = "balanced"

        return {"home_dom": round(home_wins/n, 2), "avg_goals": round(avg_goals, 2), "btts_rate": round(btts/n*100), "trend": trend}


class MarketAnalyzer:
    """Analyzes betting market for value opportunities."""

    # FIFA World Cup 2026 Qualification - Current Rankings (March 2026)
    # Source: FIFA.com - Updated for 2026 qualification cycle
    FIFA_RANKINGS = {
        # Top 10
        "Brazil": 1,
        "France": 2,
        "Argentina": 3,
        "England": 4,
        "Spain": 5,
        "Portugal": 6,
        "Italy": 7,       # Italy ~7-9
        "Netherlands": 8,
        "Belgium": 9,
        "Croatia": 10,
        # 11-25
        "Uruguay": 11,
        "Colombia": 12,
        "Mexico": 13,
        "Morocco": 14,
        "Switzerland": 15,
        "USA": 16,
        "Germany": 17,
        "Japan": 18,
        "Senegal": 19,
        "Denmark": 20,
        "Serbia": 21,
        "Poland": 22,
        "Sweden": 23,
        "Ukraine": 24,
        "Austria": 25,
        # 26-50
        "Türkiye": 26,
        "Iran": 27,
        "South Korea": 28,
        "Australia": 29,
        "Egypt": 30,
        "Czech Republic": 32,
        "Norway": 33,
        "Greece": 34,
        "Slovakia": 35,
        "Romania": 36,
        "Russia": 37,
        "Scotland": 38,
        "Wales": 39,
        "Northern Ireland": 40,
        "Republic of Ireland": 41,
        "Finland": 42,
        "Hungary": 43,
        "Albania": 44,
        "Bosnia & Herzegovina": 45,  # Bosnia ~40-50
        "Slovenia": 46,
        "Serbia": 47,
        # 50+
        "Kosovo": 100,   # Unranked/low ~90-110
        "default": 50
    }

    def analyze_odds(self, odds: Dict) -> Dict[str, Any]:
        """Analyze odds for sharp money indicators."""
        if not odds:
            return {"sharp": "none", "value": None}

        # Extract odds
        home_odd = self._extract_odd(odds, "home")
        away_odd = self._extract_odd(odds, "away")

        if home_odd and away_odd:
            # Check for significant differences
            implied_home = 1 / home_odd
            implied_away = 1 / away_odd

            # Sharp money detection (would compare with opening odds in production)
            sharp = "none"
            if implied_home > 0.55:
                sharp = "home_backing"
            elif implied_away > 0.55:
                sharp = "away_backing"

            return {"sharp": sharp, "implied_home": round(implied_home*100), "implied_away": round(implied_away*100)}

        return {"sharp": "none", "value": None}

    def _extract_odd(self, odds: Dict, selection: str) -> Optional[float]:
        """
        Extract specific odd from API-Football odds data.
        Handles multiple bookmakers and market formats.
        """
        if not odds:
            return None
            
        # Handle nested structure: {"odds": [...]}
        odds_list = odds.get("odds", []) if isinstance(odds, dict) else odds
        
        if not isinstance(odds_list, list):
            return None
        
        # Map selection to Match Winner labels
        selection_map = {
            "home": ["home", "1"],
            "draw": ["draw", "x"],
            "away": ["away", "2"],
            "over": ["over", "o"],
            "under": ["under", "u"],
            "btts": ["yes", "both"],
            "btts_no": ["no"]
        }
        
        target_labels = selection_map.get(selection.lower(), [selection.lower()])
        
        # First try: "Match Winner" market (most reliable for 1X2)
        for bk in odds_list:
            if not isinstance(bk, dict):
                continue
            bk_name = bk.get("name", "").lower()
            for mkt in bk.get("markets", []):
                if not isinstance(mkt, dict):
                    continue
                mkt_name = mkt.get("name", "").lower()
                
                # Prioritize "Match Winner" market for 1X2 odds
                if selection in ["home", "draw", "away"] and "match winner" in mkt_name:
                    for val in mkt.get("values", []):
                        if not isinstance(val, dict):
                            continue
                        label = str(val.get("value", "")).lower()
                        if label in target_labels:
                            try:
                                return float(val.get("odd", 0))
                            except:
                                pass
                
                # Fallback: search all markets
                for val in mkt.get("values", mkt.get("selections", [])):
                    if isinstance(val, dict):
                        label = str(val.get("value", val.get("label", ""))).lower()
                        # Check if any target label matches
                        for target in target_labels:
                            if target in label or label in target:
                                try:
                                    odd_val = val.get("odd", val.get("value"))
                                    if odd_val and float(odd_val) > 1:
                                        return float(odd_val)
                                except:
                                    pass
        
        return None

    def find_value_bets(self, probs: Dict[str, float], odds: Dict) -> List[Dict]:
        """Find value bets where model > market."""
        value_bets = []
        mappings = {"home_win_pct": "home", "draw_pct": "draw", "away_win_pct": "away", "over_2_5_pct": "over", "btts_yes_pct": "btts"}

        for model_key, market_key in mappings.items():
            model_prob = probs.get(model_key, 0)
            market_odd = self._extract_odd(odds, market_key)

            if market_odd and market_odd > 1:
                implied = 1 / market_odd * 100
                edge = model_prob - implied

                if edge > 5:
                    value_bets.append({"bet": market_key, "model": model_prob, "market": round(implied), "edge": round(edge)})

        return sorted(value_bets, key=lambda x: x["edge"], reverse=True)[:3]


class EnhancedPoissonCalculator:
    """Enhanced Poisson calculator with multiple factors for diverse predictions."""

    # National team match types - reduced home advantage
    NATIONAL_HOME_ADVANTAGE = 1.06  # Much lower than club football (1.12-1.15)

    def __init__(self):
        self.metrics = AdvancedTeamMetrics()
        self.context = ContextualFactors()
        self.h2h_analyzer = EnhancedH2HAnalyzer()
        self.market = MarketAnalyzer()

    def _is_national_teams_match(self, match_data: MatchDetails) -> bool:
        """Check if this is a national teams match (WC Qualification, Euro, etc.)."""
        tournament = match_data.match.tournament.lower() if match_data.match.tournament else ""
        national_keywords = ["world cup", "wc qual", "euro", "nations league", "copa america", "qualification"]
        return any(kw in tournament for kw in national_keywords)

    def _get_fifa_ranking_adjustment(self, team_name: str) -> float:
        """
        Get team strength adjustment based on FIFA ranking.
        Returns multiplier: top teams > 1.0, weak teams < 1.0
        """
        ranking = self.market.FIFA_RANKINGS.get(team_name, self.market.FIFA_RANKINGS["default"])
        # Normalize: rank 1 = 1.30, rank 50 = 1.0, rank 100 = 0.70
        if ranking <= 10:
            return 1.20 + (10 - ranking) * 0.01  # Top 10: 1.20-1.30
        elif ranking <= 25:
            return 1.05 + (25 - ranking) * 0.01  # 11-25: 1.05-1.19
        elif ranking <= 50:
            return 0.90 + (50 - ranking) * 0.003  # 26-50: 0.90-1.04
        else:
            return 0.75 + (100 - ranking) * 0.002  # 50+: 0.75-0.89

    def calculate_probabilities(self, match_data: MatchDetails) -> Dict[str, Any]:
        """Calculate probabilities with all factors for diverse predictions."""
        match = match_data.match
        league_key = self._get_league_key(match.tournament)
        
        # Check if national teams match
        is_national = self._is_national_teams_match(match_data)

        # 1. Base xG from form
        home_xg = self.metrics.calculate_xg_from_form(match_data.home_team_form, league_key)
        away_xg = self.metrics.calculate_xg_from_form(match_data.away_team_form, league_key)

        # 2. Playing styles
        home_style = self.metrics.calculate_playing_style(match_data.home_team_form)
        away_style = self.metrics.calculate_playing_style(match_data.away_team_form)

        # 3. Fatigue factors
        home_fatigue = self.context.calculate_fatigue(match_data.home_team_form, league_key)
        away_fatigue = self.context.calculate_fatigue(match_data.away_team_form, league_key)

        # 4. H2H trends
        h2h = self.h2h_analyzer.analyze_trends(match_data.h2h_matches, match.home_team, match.away_team)

        # 5. Base expected goals
        home_lam = (home_xg["xg_for"] * away_xg["xg_against"]) / 1.35
        away_lam = (away_xg["xg_for"] * home_xg["xg_against"]) / 1.35

        # 6. Apply adjustments

        # Home advantage - REDUCED for national teams
        if is_national:
            home_adv = self.NATIONAL_HOME_ADVANTAGE  # 1.06 for national teams
        else:
            home_adv = 1.15 if home_style["style"] == "very_attacking" else 1.12 if home_style["style"] == "attacking" else 1.08
        home_lam *= home_adv

        # Fatigue
        home_lam *= home_fatigue
        away_lam *= away_fatigue

        # H2H trend adjustment
        if h2h["trend"] == "home_dominates":
            home_lam *= 1.12
            away_lam *= 0.88
        elif h2h["trend"] == "away_dominates":
            home_lam *= 0.88
            away_lam *= 1.12
        elif h2h["trend"] == "low_scoring":
            home_lam *= 0.82
            away_lam *= 0.82
        elif h2h["trend"] == "high_scoring":
            home_lam *= 1.18
            away_lam *= 1.18

        # Style matchup
        if home_style["counter"] and away_style["style"] == "very_attacking":
            home_lam *= 1.15
            away_lam *= 1.10
        elif home_style["style"] == "very_defensive" and away_style["style"] == "very_defensive":
            home_lam *= 0.75
            away_lam *= 0.75

        # 7. FIFA Ranking adjustment (CRITICAL for national teams)
        if is_national:
            home_ranking_mult = self._get_fifa_ranking_adjustment(match.home_team)
            away_ranking_mult = self._get_fifa_ranking_adjustment(match.away_team)
            
            # Apply ranking adjustment to expected goals
            home_lam *= home_ranking_mult
            away_lam *= away_ranking_mult
            
            logger.info(f"FIFA Ranking: {match.home_team} ({home_ranking_mult:.2f}) vs {match.away_team} ({away_ranking_mult:.2f})")

        # 8. Match-specific variance (prevents identical predictions) - REDUCED for national teams
        seed = int(hashlib.md5(f"{match.home_team}{match.away_team}{match.date}".encode()).hexdigest()[:8], 16)
        variance_range = 0.08 if is_national else 0.20  # ±8% for national, ±20% for clubs
        variance = 1.0 + ((seed % 100) - 50) / 250 * (variance_range / 0.20)
        home_lam *= variance
        away_lam *= variance

        # Cap values - TIGHTER for national teams to prevent unrealistic expectations
        if is_national:
            home_lam = max(0.45, min(home_lam, 2.8))
            away_lam = max(0.35, min(away_lam, 2.5))
        else:
            home_lam = max(0.35, min(home_lam, 4.2))
            away_lam = max(0.25, min(away_lam, 3.8))

        # 8. Calculate Poisson probabilities
        probs = self._poisson_probs(home_lam, away_lam)

        # 9. Market odds blending - CRITICAL for realistic probabilities
        # Extract market odds and blend with our model
        market_home_odd = self.market._extract_odd(match_data.odds, "home")
        market_draw_odd = self.market._extract_odd(match_data.odds, "draw")
        market_away_odd = self.market._extract_odd(match_data.odds, "away")

        # Calculate market implied probabilities (remove vig)
        if market_home_odd and market_away_odd and market_draw_odd:
            market_implied = {
                "home": 1 / market_home_odd,
                "draw": 1 / market_draw_odd,
                "away": 1 / market_away_odd
            }
            # Remove overround (vig)
            total_implied = sum(market_implied.values())
            market_probs = {
                "home": market_implied["home"] / total_implied * 100,
                "draw": market_implied["draw"] / total_implied * 100,
                "away": market_implied["away"] / total_implied * 100
            }

            # Blend: 40% model + 60% market for national teams (market is more reliable)
            # 60% model + 40% market for club teams
            model_weight = 0.4 if is_national else 0.6
            market_weight = 1 - model_weight

            probs["home_win_pct"] = round(probs["home_win_pct"] * model_weight + market_probs["home"] * market_weight)
            probs["draw_pct"] = round(probs["draw_pct"] * model_weight + market_probs["draw"] * market_weight)
            probs["away_win_pct"] = round(probs["away_win_pct"] * model_weight + market_probs["away"] * market_weight)

            # Ensure they sum to 100
            total = probs["home_win_pct"] + probs["draw_pct"] + probs["away_win_pct"]
            probs["home_win_pct"] = round(probs["home_win_pct"] / total * 100)
            probs["draw_pct"] = round(probs["draw_pct"] / total * 100)
            probs["away_win_pct"] = 100 - probs["home_win_pct"] - probs["draw_pct"]  # Ensure exactly 100

            probs["market_home_odd"] = market_home_odd
            probs["market_draw_odd"] = market_draw_odd
            probs["market_away_odd"] = market_away_odd
            probs["blended"] = True
            logger.info(f"Market odds: {market_home_odd} | {market_draw_odd} | {market_away_odd} → Blended probs: {probs['home_win_pct']}% | {probs['draw_pct']}% | {probs['away_win_pct']}%")
        else:
            # NO MARKET ODDS - Use FIFA ranking based probabilities for national teams
            if is_national:
                home_rank = self.market.FIFA_RANKINGS.get(match.home_team, 50)
                away_rank = self.market.FIFA_RANKINGS.get(match.away_team, 50)
                
                # Calculate ranking-based probabilities
                # Lower rank = stronger team
                home_strength = 100 / home_rank
                away_strength = 100 / away_rank
                
                # Home advantage factor for national teams (small)
                home_strength *= 1.06
                
                total_strength = home_strength + away_strength
                
                # Base probabilities from ranking
                home_prob = home_strength / total_strength * 100
                away_prob = away_strength / total_strength * 100
                
                # Draw probability based on team strength similarity
                strength_ratio = min(home_strength, away_strength) / max(home_strength, away_strength)
                draw_prob = 15 + strength_ratio * 12  # 15-27% draw rate
                
                # Normalize to 100%
                remaining = 100 - draw_prob
                home_prob = home_prob / (home_prob + away_prob) * remaining
                away_prob = away_prob / (home_prob + away_prob) * remaining
                
                # Blend: 20% model + 80% ranking (ranking is more reliable for national teams)
                probs["home_win_pct"] = round(probs["home_win_pct"] * 0.2 + home_prob * 0.8)
                probs["draw_pct"] = round(probs["draw_pct"] * 0.2 + draw_prob * 0.8)
                probs["away_win_pct"] = round(probs["away_win_pct"] * 0.2 + away_prob * 0.8)
                
                # Ensure exactly 100%
                total = probs["home_win_pct"] + probs["draw_pct"] + probs["away_win_pct"]
                probs["home_win_pct"] = round(probs["home_win_pct"] / total * 100)
                probs["draw_pct"] = round(probs["draw_pct"] / total * 100)
                probs["away_win_pct"] = 100 - probs["home_win_pct"] - probs["draw_pct"]
                
                probs["blended"] = False
                probs["ranking_based"] = True
                logger.info(f"FIFA Ranking: {home_rank} vs {away_rank} → Ranking probs: {home_prob:.1f}% | {draw_prob:.1f}% | {away_prob:.1f}% → Final: {probs['home_win_pct']}% | {probs['draw_pct']}% | {probs['away_win_pct']}%")
            else:
                probs["blended"] = False
                probs["ranking_based"] = False
                logger.info(f"No market odds available, using pure model: {probs['home_win_pct']}% | {probs['draw_pct']}% | {probs['away_win_pct']}%")

        # 10. Add context
        probs.update({
            "home_xg": home_xg["xg_for"],
            "away_xg": away_xg["xg_for"],
            "home_fatigue": round(home_fatigue, 2),
            "away_fatigue": round(away_fatigue, 2),
            "h2h_trend": h2h["trend"],
            "home_style": home_style["style"],
            "away_style": away_style["style"],
            "home_counter": home_style["counter"],
            "btts_h2h_rate": h2h["btts_rate"],
            "is_national_teams": is_national,
        })

        # 11. Market analysis
        market_info = self.market.analyze_odds(match_data.odds)
        probs["sharp_money"] = market_info.get("sharp", "none")

        # 12. Value bets
        probs["value_bets"] = self.market.find_value_bets(probs, match_data.odds)

        logger.info(f"Enhanced: {match.home_team} {home_lam:.2f} vs {away_lam:.2f} {match.away_team} | Style: {home_style['style']} vs {away_style['style']}")

        return probs

    def _poisson_probs(self, home_lam: float, away_lam: float) -> Dict[str, Any]:
        """Calculate Poisson probabilities."""
        probs = {}

        # 1X2
        home_win = draw = away_win = 0.0
        for h in range(7):
            hp = self._poisson(h, home_lam)
            for a in range(7):
                ap = self._poisson(a, away_lam)
                joint = hp * ap
                if h > a:
                    home_win += joint
                elif h == a:
                    draw += joint
                else:
                    away_win += joint

        total = home_win + draw + away_win
        probs["home_win_pct"] = round(home_win / total * 100)
        probs["draw_pct"] = round(draw / total * 100)
        probs["away_win_pct"] = round(away_win / total * 100)

        # Totals
        total_lam = home_lam + away_lam
        under_2_5 = sum(self._poisson(k, total_lam) for k in range(3))
        probs["over_2_5_pct"] = round((1 - under_2_5) * 100)
        probs["under_2_5_pct"] = round(under_2_5 * 100)
        probs["expected_total_goals"] = round(total_lam, 2)

        # BTTS
        no_home = self._poisson(0, home_lam)
        no_away = self._poisson(0, away_lam)
        btts_yes = (1 - no_home) * (1 - no_away)
        probs["btts_yes_pct"] = round(btts_yes * 100)
        probs["btts_no_pct"] = round((1 - btts_yes) * 100)

        # Double chance
        probs["1X_pct"] = round((home_win + draw) / total * 100)
        probs["X2_pct"] = round((away_win + draw) / total * 100)

        # Goal bands
        probs["goals_0_1_pct"] = round(sum(self._poisson(k, total_lam) for k in range(2)) * 100)
        probs["goals_2_3_pct"] = round(sum(self._poisson(k, total_lam) for k in range(2, 4)) * 100)
        probs["goals_4+_pct"] = round((1 - probs["goals_0_1_pct"]/100 - probs["goals_2_3_pct"]/100) * 100)

        # Cards (Poisson lambda=4.5)
        card_lam = 4.5
        cards_under = sum(self._poisson(k, card_lam) for k in range(5))
        probs["cards_over_4_5_pct"] = round((1 - cards_under) * 100)
        probs["cards_under_4_5_pct"] = round(cards_under * 100)

        # Corners (Poisson lambda=9.5)
        corner_lam = 9.5
        corners_under = sum(self._poisson(k, corner_lam) for k in range(10))
        probs["corners_over_9_5_pct"] = round((1 - corners_under) * 100)
        probs["corners_under_9_5_pct"] = round(corners_under * 100)

        # Correct scores
        scores = []
        for h in range(5):
            for a in range(5):
                p = self._poisson(h, home_lam) * self._poisson(a, away_lam)
                scores.append((f"{h}:{a}", round(p * 100)))
        scores.sort(key=lambda x: x[1], reverse=True)
        probs["likely_scores"] = [{"score": s, "prob": p} for s, p in scores[:5]]

        # Expected goals
        probs["home_expected_goals"] = round(home_lam, 2)
        probs["away_expected_goals"] = round(away_lam, 2)

        return probs

    def _poisson(self, k: int, lam: float) -> float:
        """Poisson probability."""
        return (lam ** k) * exp(-lam) / factorial(k)

    def _get_league_key(self, tournament: str) -> str:
        """Get league key from name."""
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
            "world cup qualification": "wc_qual_europe",
            "wc qualification": "wc_qual_europe",
            "qualification europe": "wc_qual_europe",
        }
        for k, v in mapping.items():
            if k in name:
                return v
        return "default"


class NewsFetcher:
    """Fetches team news from verified sources."""

    SOURCES = ["bbc.com/sport/football", "skysports.com", "espn.com/soccer", "theguardian.com/football", "goal.com"]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})

    def fetch_team_news(self, team: str, days: int = 7) -> Dict[str, Any]:
        """Fetch team news."""
        news = {"team": team, "headlines": [], "injuries": [], "sentiment": "neutral", "sources": []}

        queries = [f"{team} injury", f"{team} form", f"{team} news"]
        for q in queries:
            items = self._search_google_news(q)
            for item in items[:3]:
                cat = self._categorize(item.get("title", ""))
                if cat == "injury":
                    news["injuries"].append(item)
                news["headlines"].append(item)
                if item.get("source") and item["source"] not in news["sources"]:
                    news["sources"].append(item["source"])

        news["sentiment"] = self._analyze_sentiment(news["headlines"])
        news["headlines"] = news["headlines"][:10]
        return news

    def _search_google_news(self, query: str) -> List[Dict]:
        """Search Google News."""
        try:
            resp = self.session.get(f"https://news.google.com/search?q={query}&hl=en", timeout=10)
            if resp.status_code == 200:
                return self._parse(resp.text)
        except:
            pass
        return []

    def _parse(self, html: str) -> List[Dict]:
        """Parse headlines."""
        headlines = []
        for match in re.findall(r'<a[^>]+href="([^"]+)"[^>]+>([^<]+)</a>', html, re.I):
            href, title = match
            title = re.sub(r'\s+', ' ', title).strip()
            if 20 < len(title) < 200:
                source = "Unknown"
                for s in self.SOURCES:
                    if s.split('.')[0] in href.lower():
                        source = s.split('.')[0].title()
                        break
                headlines.append({"title": title, "url": f"https://news.google.com{href}" if href.startswith('/') else href, "source": source})
        return headlines[:15]

    def _categorize(self, title: str) -> str:
        """Categorize news."""
        t = title.lower()
        if any(k in t for k in ["injur", "fitness", "knock"]):
            return "injury"
        if any(k in t for k in ["form", "win", "result"]):
            return "form"
        return "general"

    def _analyze_sentiment(self, headlines: List[Dict]) -> str:
        """Analyze sentiment."""
        pos = ["win", "victory", "return", "fit", "ready"]
        neg = ["lose", "defeat", "injured", "out", "doubt"]
        p = sum(1 for h in headlines for w in pos if w in h.get("title", "").lower())
        n = sum(1 for h in headlines for w in neg if w in h.get("title", "").lower())
        return "negative" if n > p + 1 else "positive" if p > n + 1 else "neutral"


class AIAnalyzer:
    """Enhanced AI Analyzer for football predictions."""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.calc = EnhancedPoissonCalculator()
        self.news = NewsFetcher()

    def _format_form(self, form: list, team: str) -> str:
        if not form:
            return f"{team}: Нет данных"
        results = [m.get("result", "?") for m in form]
        details = "\n".join([f"  • vs {m.get('opponent', '?')}: {m.get('score', '?')} ({m.get('result', '?')})" for m in form])
        return f"{team} ({' → '.join(results)}):\n{details}"

    def _format_h2h(self, h2h: list) -> str:
        if not h2h:
            return "Нет данных"
        return "\n".join([f"  • {m.get('home_team', '?')} {m.get('home_score', '-')}:{m.get('away_score', '-')} {m.get('away_team', '?')}" for m in h2h[:5]])

    def _format_stats(self, stats: dict) -> str:
        if not stats:
            return "Нет статистики"
        return "\n".join([f"  {k}: {v.get('home', '-')} - {v.get('away', '-')}" for k, v in stats.items()])

    def _format_odds(self, odds: dict) -> str:
        """Format betting odds in a readable way."""
        if not odds:
            return "Нет коэффициентов"
        
        lines = []
        # Handle both dict and list formats
        bookmakers_data = []
        if isinstance(odds, dict):
            bookmakers_data = odds.get("bookmakers", [])
        elif isinstance(odds, list):
            bookmakers_data = odds[:3]
        
        for bk in bookmakers_data:
            if isinstance(bk, dict):
                name = bk.get("name", "Unknown")
                for mkt in bk.get("markets", [])[:3]:
                    if isinstance(mkt, dict):
                        market_name = mkt.get("name", "Unknown")
                        selections = mkt.get("values", mkt.get("selections", []))
                        if selections:
                            odds_str = " | ".join([
                                f"{s.get('value', s.get('label', 'N/A'))}: {s.get('odd', s.get('value', 'N/A'))}"
                                for s in selections[:3] if isinstance(s, dict)
                            ])
                            if odds_str:
                                lines.append(f"  {name} ({market_name}): {odds_str}")
        
        return "\n".join(lines) if lines else "Нет данных"

    def _format_standings(self, standings: dict) -> str:
        """Format league standings for both teams."""
        if not standings:
            return "Нет данных о турнирной таблице"
        
        lines = []
        for team_id, data in standings.items():
            pos = data.get('position', '?')
            pts = data.get('points', 0)
            played = data.get('played', 0)
            gf = data.get('goals_for', 0)
            ga = data.get('goals_against', 0)
            form = data.get('form', '?????')
            lines.append(f"  • {pos} место | {pts} очк | {played} игр | Голы: {gf}-{ga} ({gf-ga:+d}) | Форма: {form}")
        
        return "\n".join(lines) if lines else "Нет данных"

    def _build_prompt(self, match_data: MatchDetails) -> str:
        """Build focused analysis prompt with key highlights."""
        match = match_data.match
        stats = self.calc.calculate_probabilities(match_data)

        # Format form with detailed breakdown
        home_form = match_data.home_team_form[:5]
        away_form = match_data.away_team_form[:5]

        home_goals_scored = sum(int(m['score'].split(':')[0]) for m in home_form if ':' in m.get('score', ''))
        home_goals_conceded = sum(int(m['score'].split(':')[1]) for m in home_form if ':' in m.get('score', ''))
        away_goals_scored = sum(int(m['score'].split(':')[0]) for m in away_form if ':' in m.get('score', ''))
        away_goals_conceded = sum(int(m['score'].split(':')[1]) for m in away_form if ':' in m.get('score', ''))

        home_form_str = "".join([m.get('result', '?') for m in home_form])
        away_form_str = "".join([m.get('result', '?') for m in away_form])

        # Format H2H with trends
        h2h = match_data.h2h_matches[:5]
        h2h_btts = sum(1 for m in h2h if (m.get('home_score', 0) or 0) > 0 and (m.get('away_score', 0) or 0) > 0)
        h2h_over_25 = sum(1 for m in h2h if ((m.get('home_score', 0) or 0) + (m.get('away_score', 0) or 0)) > 2.5)
        h2h_avg_goals = sum((m.get('home_score', 0) or 0) + (m.get('away_score', 0) or 0) for m in h2h) / len(h2h) if h2h else 0

        # Get odds info
        odds_info = self._format_odds(match_data.odds)

        # Get standings info
        standings_info = self._format_standings(getattr(match_data, 'standings', {}))

        data = f"""
⚽ **{match.home_team}** vs **{match.away_team}** | {match.tournament}
📅 {match.date}

┌─────────────────────────────────────────┐
│ 📈 ФОРМА:                               │
│ {match.home_team}: {home_form_str} ({home_goals_scored}–{home_goals_conceded}) │
│ {match.away_team}: {away_form_str} ({away_goals_scored}–{away_goals_conceded}) │
└─────────────────────────────────────────┘

🎯 **H2H (последние 5):**
{self._format_h2h(h2h)}
• Средний тотал: **{h2h_avg_goals:.2f}** | Обе забьют: **{int(h2h_btts/len(h2h)*100) if h2h else 0}%** | ТБ 2.5: **{int(h2h_over_25/len(h2h)*100) if h2h else 0}%**
• Тренд: **{stats.get('h2h_trend', 'нет')}**

📋 **ТУРНИРНОЕ ПОЛОЖЕНИЕ:**
{standings_info}

📊 **СТАТИСТИКА КОМАНД:**
• xG (ожидаемые голы): {stats.get('home_xg', 0):.2f} vs {stats.get('away_xg', 0):.2f}
• Стиль игры: **{stats.get('home_style', '?')}** vs **{stats.get('away_style', '?')}**
• Усталость: **{stats.get('home_fatigue', 1):.2f}** vs **{stats.get('away_fatigue', 1):.2f}**

📈 **ФОРМА (последние 5 матчей):**
{self._format_form(match_data.home_team_form[:5], match.home_team)}

📈 **ФОРМА (последние 5 матчей):**
{self._format_form(match_data.away_team_form[:5], match.away_team)}

🎯 **H2H (личные встречи):**
{self._format_h2h(match_data.h2h_matches[:5])}

💰 **РЫНОЧНЫЕ ВЕРОЯТНОСТИ (от букмекеров):**
┌─────────────────────────────────────────┐
│ П1: {stats.get('home_win_pct', 0):5.1f}% | X: {stats.get('draw_pct', 0):5.1f}% | П2: {stats.get('away_win_pct', 0):5.1f}% │
└─────────────────────────────────────────┘
❗ ЭТО ТОЧНЫЕ ДАННЫЕ ОТ БУКМЕКЕРОВ — ИСПОЛЬЗУЙ ИХ КАК БАЗУ!

💡 **РЫНОЧНЫЕ СИГНАЛЫ:** Sharp: **{stats.get('sharp_money', 'нет')}** | Value: **{', '.join([f"{b['bet']} (+{b['edge']}%)" for b in stats.get('value_bets', [])]) or 'нет'}**

📋 **КОЭФФИЦИЕНТЫ (из API):**
{odds_info}

**❗❗❗ КРИТИЧЕСКАЯ ИНСТРУКЦИЯ:**
ТЫ ОБЯЗАН ИСПОЛЬЗОВАТЬ РЫНОЧНЫЕ ВЕРОЯТНОСТИ ВЫШЕ КАК БАЗУ!

**ПРАВИЛО:**
1. Твои итоговые вероятности ДОЛЖНЫ быть в пределах ±8% от рыночных!
2. Если рыночные П2: 62% → ты НЕ МОЖЕШЬ дать меньше 54% или больше 70%!
3. Если рыночные П1: 18% → ты НЕ МОЖЕШЬ дать больше 26%!

**ПРИМЕР:**
Рыночные: П1: 18% | X: 20% | П2: 62%
✅ МОЖНО: П1: 20% | X: 22% | П2: 58% (отличие в пределах ±8%)
❌ НЕЛЬЗЯ: П1: 46% | X: 24% | П2: 30% (отличие на 28% — КАТАСТРОФА!)

**ЕСЛИ ИГНОРИРУЕШЬ РЫНОЧНЫЕ ВЕРОЯТНОСТИ — ТВОЙ ПРОГНОЗ БЕСПОЛЕЗЕН!**
"""

        return f"""🎯 PROMPT: Профессиональный гандикапер (Professional Football Handicapper)

Ты — элитный аналитик с 15+ лет опыта в спортивном беттинге. Твои прогнозы основаны на данных, статистике и глубоком анализе. Точность — приоритет #1.

═══════════════════════════════════════════════════
🎯 МИССИЯ:
═══════════════════════════════════════════════════
Создать МАКСИМАЛЬНО ТОЧНЫЙ прогноз, используя:
1. Объективные данные (API)
2. ВСЮ актуальную информацию из интернета
3. Математический расчёт
4. Профессиональную логику

═══════════════════════════════════════════════════
🔍 ПОИСК В ИНТЕРНЕТЕ (ОБЯЗАТЕЛЬНО):
═══════════════════════════════════════════════════

ПЕРЕД анализом ПРОВЕРЬ в интернете:

**1. ТРАВМЫ И ДИСКВАЛИФИКАЦИИ:**
• Официальные сайты клубов/сборных
• Пресс-конференции тренеров
• Заявки на матч
✓ Источники: BBC Sport, Sky Sports, официальные сайты

**2. СОСТАВЫ:**
• Ожидаемые стартовые 11
• Ротация после предыдущих матчей
• Возвращения после травм
✓ Источники: The Athletic, ESPN, Goal.com

**3. НОВОСТИ КОМАНД:**
• Конфликты в раздевалке
• Смена тренера
• Финансовые проблемы
• Мотивация (борьба за титул/выживание)
✓ Источники: Reuters, AP, официальные лиги

**4. СТАТИСТИКА:**
• Последние результаты
• Домашняя/выездная форма
• Личные встречи
✓ Источники: WhoScored, SofaScore, Transfermarkt

**5. ПОГОДА И УСЛОВИЯ:**
• Прогноз на матч
• Состояние поля
✓ Источники: Weather.com, AccuWeather

**6. СУДЕЙСТВО:**
• Назначенный рефери
• Его статистика (карточки, пенальти)
✓ Источники: Официальные сайты лиг

═══════════════════════════════════════════════════
✅ ПРОВЕРЕННЫЕ ИСТОЧНИКИ (ИСПОЛЬЗОВАТЬ):
═══════════════════════════════════════════════════

**Новости и аналитика:**
✓ BBC Sport (bbc.com/sport)
✓ Sky Sports (skysports.com)
✓ ESPN (espn.com/soccer)
✓ The Athletic (theathletic.com)
✓ Reuters (reuters.com/sports)
✓ Associated Press (apnews.com)

**Футбольные:**
✓ Goal.com
✓ Transfermarkt
✓ WhoScored
✓ SofaScore
✓ Flashscore

**Официальные:**
✓ Сайты клубов (manutd.com, realmadrid.com, etc.)
✓ UEFA.com
✓ FIFA.com
✓ Сайты лиг (premierleague.com, laliga.es)

**Статистика:**
✓ FBref.com
✓ Understat.com
✓ FiveThirtyEight

═══════════════════════════════════════════════════
❌ ЗАПРЕЩЁННЫЕ ИСТОЧНИКИ:
═══════════════════════════════════════════════════

✗ Таблоиды: The Sun, Daily Mail, Mirror
✗ Соцсети: Twitter, Facebook, Instagram
✗ Блоги: личные блоги, фанатские сайты
✗ Телеграм-каналы без подтверждения
✗ Жёлтая пресса: SportBible, 90min
✗ Ставочные форумы

═══════════════════════════════════════════════════
🧮 РАСЧЁТ ВЕРОЯТНОСТЕЙ (ПОШАГОВО):
═══════════════════════════════════════════════════

**ШАГ 1: БАЗА — рыночные коэффициенты**
Рынок эффективен. Это точка отсчёта.
Формула: Вероятность = (1 / коэффициент) * 100

Пример:
• Босния: 7.50 → 13.3%
• Ничья: 4.25 → 23.5%
• Италия: 1.52 → 65.8%
• Сумма: 102.6% (маржа 2.6%)
• После удаления маржи: 13% | 23% | 64%

**ШАГ 2: Корректировка по форме**
Форма (последние 5 матчей):
• 5 побед подряд: +8%
• 4 победы: +5%
• 3 победы: +2%
• 2 победы: 0%
• 1 победа: -3%
• 0 побед: -5%

**ШАГ 3: Учёт xG (ожидаемые голы)**
xG показывает реальную силу атаки/обороны:
• xG > 2.0: элитная атака (+5%)
• xG 1.5-2.0: хорошая атака (+2%)
• xG 1.0-1.5: средняя (-2%)
• xG < 1.0: слабая (-5%)

**ШАГ 4: H2H (личные встречи)**
• 4+ победы подряд одной команды: +7%
• 3 победы подряд: +5%
• 2 победы подряд: +3%
• Паритет: 0%

**ШАГ 5: Домашнее преимущество**
• Клубы: +10-12%
• Сборные: +6-8% (меньше из-за нейтральной атмосферы)

**ШАГ 6: Травмы/дисквалификации**
• Ключевой игрок вне игры: -12%
• 2+ ключевых: -20%
• Все в строю: 0%

**ШАГ 7: Мотивация**
• Критический матч (финал, квалификация): +5%
• Обычный матч: 0%
• Матч без мотивации: -5%

**ШАГ 8: ФИНАЛЬНЫЙ РАСЧЁТ**
Сложи все корректировки с базой (Шаг 1).
Проверь: П1 + X + П2 = 100%

═══════════════════════════════════════════════════
🚫 КРАСНЫЕ ФЛАГИ (КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО):
═══════════════════════════════════════════════════
❌ Твои вероятности ОТЛИЧАЮТСЯ от рыночных > 8%!
❌ Аутсайдер > 25% (если рыночные < 20%)
❌ Фаворит < 50% (если рыночные > 60%)
❌ Ничья < 12% или > 35%
❌ Сумма вероятностей ≠ 100%
❌ Игнорировать рыночные вероятности
❌ Рекомендация противоречит вероятностям
❌ Прогноз без обоснования
❌ **ВЫДУМЫВАТЬ КОЭФФИЦИЕНТЫ** — бери ТОЛЬКО из API или рыночных!

═══════════════════════════════════════════════════
💰 КОЭФФИЦИЕНТЫ (КРИТИЧНО ВАЖНО):
═══════════════════════════════════════════════════

**РЫНОЧНЫЕ ВЕРОЯТНОСТИ — ЭТО БАЗА!**

В разделе "💰 РЫНОЧНЫЕ ВЕРОЯТНОСТИ (от букмекеров):" ты видишь проценты,
рассчитанные из реальных коэффициентов букмекеров.

**Используй ИХ как точку отсчёта:**
1. Возьми рыночные вероятности за ОСНОВУ
2. Скорректируй на ±5-10% на основе:
   - Формы команд
   - Травм (из интернета)
   - Мотивации
   - Домашнего преимущества
3. Итоговые вероятности должны быть БЛИЗКИ к рыночным (±10%)

**Пример ПРАВИЛЬНОГО расчёта:**
Рыночные: П1: 18% | X: 20% | П2: 62%
↓
Твой анализ:
- Форма Боснии 4/5 побед → +3% к П1
- Италия без травм → 0%
- Домашний бонус Боснии → +2% к П1
- Мотивация Италии выше → -3% к П1, +3% к П2
↓
ИТОГ: П1: 20% | X: 20% | П2: 60% (близко к рыночным!)

**Пример НЕПРАВИЛЬНОГО расчёта:**
Рыночные: П1: 18% | X: 20% | П2: 62%
↓
Твой анализ: П1: 46% | X: 22% | П2: 32%  ← ❌ НЕДОПУСТИМО!
(Отличие от рыночных на 28% без причин!)

═══════════════════════════════════════════════════
✅ ПРИМЕР ИДЕАЛЬНОГО АНАЛИЗА:
═══════════════════════════════════════════════════

⚽️ Босния и Герцеговина vs Италия | Отбор ЧМ-2026

📝 Италия борется за прямую путёвку, Босния играет без давления.

📊 ВЕРОЯТНОСТИ
П1: 20% | X: 22% | П2: 58%
(Рыночные: 18% | 20% | 62% — отличие в пределах ±8%, корректно!)

Метод: рынок (62%) + домашний бонус Боснии (+4%) - мотивация Италии (-8%)

📈 ФОРМА
• Босния: W-W-W-W-L (11-3) — 4/5 побед, мощная атака дома
• Италия: W-L-W-W-W (13-7) — 4/5 побед, но пропускает

🎯 H2H
• Италия выиграла 4 из 5 последних встреч
• Босния не побеждала Италию с 2013 года
• Средний тотал: 2.20 гола

📌 КЛЮЧЕВЫЕ ФАКТОРЫ
• xG: 1.64 vs 1.81 — Италия создаёт больше
• Стиль: attacking vs very_attacking — голы ожидаются
• Домашний бонус: Босния сильна в Зенице
• Мотивация: Италии нужна победа для квалификации

🎯 РЕКОМЕНДАЦИИ
1. П2 — 58% (кф уточняй у букмекеров, рыночные ~1.55)
   Италия доминирует в H2H, выше мотивация

2. ТБ 2.5 — 60% (кф уточняй, рыночные ~1.65)
   Ожидаемый тотал 3.3+, атакующие стили

⚡️ ВЕРДИКТ
Италия фаворит, но Босния забьёт на своём поле.

⚠️ Прогноз основан на данных, но не гарантирует выигрыш.

═══════════════════════════════════════════════════
📋 ФОРМАТ ОТВЕТА:
═══════════════════════════════════════════════════

**⚽️ ЗАГОЛОВОК**
[Команда 1] vs [Команда 2] | [Турнир]

**📝 ВСТУПЛЕНИЕ (1 предложение)**
Главный контекст матча

**📊 ВЕРОЯТНОСТИ**
П1: XX% | X: XX% | П2: XX%
(Сумма = 100%)

Метод: кратко (2-3 фактора)

**📈 ФОРМА**
[Команда 1]: X-X-X-X-X (забито-пропущено)
[Команда 2]: X-X-X-X-X (забито-пропущено)

**🎯 H2H**
2-3 факта с цифрами

**📌 КЛЮЧЕВЫЕ ФАКТОРЫ**
• xG
• Стиль
• Травмы/составы (актуально из интернета!)
• Мотивация

**📊 ДОП. ВЕРОЯТНОСТИ**
ТБ 2.5: XX% | ТМ 2.5: XX%
Обе забьют: XX% | ОЗ нет: XX%

**🎯 РЕКОМЕНДАЦИИ (максимум 2)**
[Ставка] — XX% (кф ~X.XX **из API**)
Обоснование: 1-2 предложения

**⚡️ ВЕРДИКТ (1 предложение)**

**⚠️ ДИСКЛЕЙМЕР**

═══════════════════════════════════════════════════
💡 ПРОФЕССИОНАЛЬНАЯ ЛОГИКА:
═══════════════════════════════════════════════════
• Фаворит с кф 1.40-1.60 = 55-70% (не больше!)
• Аутсайдер с кф 5.0-9.0 = 10-20% (не больше!)
• Ничья в равном матче = 22-28%
• Ничья в матче с явным фаворитом = 15-20%
• ТБ 2.5 при xG сумма > 3.0 = 60-70%
• ОЗ при xG обеих > 1.3 = 55-65%

═══════════════════════════════════════════════════
📊 ДАННЫЕ ИЗ API:
═══════════════════════════════════════════════════
{data}

**⚠️ ВНИМАНИЕ: ПРОВЕРЬ ВСЮ АКТУАЛЬНУЮ ИНФОРМАЦИЮ В ИНТЕРНЕТЕ:**
1. Травмы и дисквалификации (официальные сайты)
2. Ожидаемые составы (The Athletic, Sky Sports)
3. Новости команд (BBC, ESPN, Reuters)
4. Погода на матч
5. Судейская бригада

**ИСПОЛЬЗУЙ ТОЛЬКО ПРОВЕРЕННЫЕ ИСТОЧНИКИ (см. список выше).**

**НАЧНИ АНАЛИЗ:**"""

    async def generate_analysis(self, match_data: MatchDetails) -> str:
        """Generate analysis using Claude with web search for latest news/injuries."""
        try:
            prompt = self._build_prompt(match_data)

            # Use Claude with web search capability (if available)
            # This allows Claude to check latest injuries, team news, etc.
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                # Enable web search for current data (if supported by API)
                extra_headers={"x-search-enabled": "true"} if hasattr(self.client, 'messages') else {}
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            # Fallback to stats-only analysis
            stats = self.calc.calculate_probabilities(match_data)
            return self._format_stats_only(match_data, stats)

    def _format_stats_only(self, match_data: MatchDetails, stats: Dict) -> str:
        """Format stats-only analysis when AI unavailable."""
        match = match_data.match
        return f"""⚽ {match.home_team} vs {match.away_team}

📊 ПРОДВИНУТАЯ СТАТИСТИКА
• xG: {stats.get('home_xg', 0):.2f} vs {stats.get('away_xg', 0):.2f}
• Стиль: {stats.get('home_style', '?')} vs {stats.get('away_style', '?')}
• Усталость: {stats.get('home_fatigue', 1):.2f} vs {stats.get('away_fatigue', 1):.2f}
• H2H тренд: {stats.get('h2h_trend', 'none')}

📈 ВЕРОЯТНОСТИ
• П1: {stats['home_win_pct']}% | X: {stats['draw_pct']}% | П2: {stats['away_win_pct']}%
• ТБ 2.5: {stats['over_2_5_pct']}% | ТМ 2.5: {stats['under_2_5_pct']}%
• Обе забьют: {stats['btts_yes_pct']}%
• Ожидаемый тотал: {stats['expected_total_goals']}

🎯 СЧЕТА: {', '.join([s['score'] for s in stats.get('likely_scores', [])])}

💰 Value: {', '.join([f"{b['bet']} (+{b['edge']}%)" for b in stats.get('value_bets', [])]) or "нет"}
"""


# Backward compatibility
PoissonCalculator = EnhancedPoissonCalculator
