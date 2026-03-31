"""
API-Football Parser Module
Uses API-Football (v3) for all football data.
Free tier: 100 requests/day
Docs: https://api-football.com/documentation
"""

import logging
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


@dataclass
class Match:
    """Represents a football match."""
    id: str
    date: str
    home_team: str
    away_team: str
    home_team_id: str = ""
    away_team_id: str = ""
    tournament: str = ""
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    status: str = ""
    venue: str = ""
    referee: str = ""


@dataclass
class MatchDetails:
    """Detailed match information including statistics and history."""
    match: Match
    statistics: Dict = field(default_factory=dict)
    home_team_form: List[Dict] = field(default_factory=list)
    away_team_form: List[Dict] = field(default_factory=list)
    h2h_matches: List[Dict] = field(default_factory=list)
    odds: Dict = field(default_factory=dict)
    lineups: Dict = field(default_factory=dict)
    injuries: Dict = field(default_factory=dict)
    standings: Dict = field(default_factory=dict)  # League position for both teams


class APIFootballParser:
    """
    Parser for API-Football v3.
    Optimized: Fetches entire season fixtures once per day.
    Paid plan: Full access to current season (2025-2026)
    Docs: https://api-football.com/documentation
    """

    BASE_URL = "https://v3.football.api-sports.io"

    # League mappings
    LEAGUE_IDS = {
        # Top European Leagues
        "premier_league": 39,      # Premier League (England)
        "la_liga": 140,            # La Liga (Spain)
        "bundesliga": 78,          # Bundesliga (Germany)
        "serie_a": 135,            # Serie A (Italy)
        "ligue_1": 61,             # Ligue 1 (France)

        # European Competitions
        "champions_league": 2,     # UEFA Champions League
        "europa_league": 3,        # UEFA Europa League
        "conference_league": 848,  # UEFA Conference League

        # International Tournaments
        "world_cup": 1,            # FIFA World Cup
        "euro": 4,                 # UEFA European Championship
        "copa_america": 9,         # Copa America
        "nations_league": 5,       # UEFA Nations League

        # World Cup Qualifications (2026)
        "wc_qual_europe": 32,      # World Cup - Qualification Europe
        "wc_qual_concacaf": 31,    # World Cup - Qualification CONCACAF
        "wc_qual_south_america": 34,  # World Cup - Qualification South America
        "wc_qual_asia": 30,        # World Cup - Qualification Asia
        "wc_qual_africa": 29,      # World Cup - Qualification Africa
        "wc_qual_oceania": 33,     # World Cup - Qualification Oceania
        "wc_qual_playoffs": 37,    # World Cup - Qualification Intercontinental Play-offs

        # Other Top Leagues
        "eredivisie": 88,          # Eredivisie (Netherlands)
        "primeira_liga": 94,       # Primeira Liga (Portugal)
        "mls": 253,                # MLS (USA)
        "brasileirao": 71,         # Brasileirão (Brazil)
        "liga_mx": 262,            # Liga MX (Mexico)

        # Cups
        "fa_cup": 45,              # FA Cup (England)
        "copa_del_rey": 143,       # Copa del Rey (Spain)
        "dfb_pokal": 81,           # DFB Pokal (Germany)
        "coppa_italia": 137,       # Coppa Italia (Italy)
    }

    def __init__(self, api_key: str, request_delay: float = 0.1, timeout: int = 10):
        """
        Initialize the parser.

        Args:
            api_key: API-Football API key
            request_delay: Delay between requests in seconds
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.request_delay = request_delay
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update({
            "x-apisports-key": api_key,
            "Accept": "application/json"
        })

        # Cache for season fixtures (24 hours)
        self._season_cache = {}
        self._cache_ttl = 86400  # 24 hours in seconds

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make API request with error handling.
        Note: Season fixtures caching is handled in _get_season_fixtures.

        Args:
            endpoint: API endpoint (e.g., "/fixtures")
            params: Query parameters

        Returns:
            Response data or None if failed
        """
        url = f"{self.BASE_URL}{endpoint}"

        try:
            time.sleep(self.request_delay)
            response = self.session.get(url, params=params, timeout=self.timeout)

            if response.status_code == 429:
                logger.warning("API-Football rate limit exceeded")
                return None

            if response.status_code != 200:
                logger.error(f"API-Football returned status {response.status_code}")
                return None

            data = response.json()

            if not data.get("get"):
                logger.error(f"Invalid API response: {data}")
                return None

            return data

        except requests.RequestException as e:
            logger.error(f"Request failed for {endpoint}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {endpoint}: {e}")
            return None

    def _get_season_fixtures(self, league: str) -> List[Match]:
        """
        Get ALL fixtures for the entire season (cached for 24 hours).
        This is the OPTIMIZED method - one API call per league per day.

        Args:
            league: League key from LEAGUE_IDS

        Returns:
            List of all Match objects for the season
        """
        if league not in self.LEAGUE_IDS:
            logger.error(f"Unknown league: {league}")
            return []

        league_id = self.LEAGUE_IDS[league]

        # Special season handling for World Cup Qualifications
        # Europe qualification uses 2024 season for 2026 World Cup
        wc_qual_leagues = ["wc_qual_europe", "wc_qual_concacaf", "wc_qual_south_america", 
                          "wc_qual_asia", "wc_qual_africa", "wc_qual_oceania", "wc_qual_playoffs"]
        
        if league in wc_qual_leagues:
            # Most WC qualifications use 2024/2025 season for 2026 World Cup
            if league == "wc_qual_europe":
                season_year = 2024  # Europe uses 2024 season
            else:
                season_year = 2026  # Others use 2026 season
        else:
            # Standard season calculation for regular leagues
            today = datetime.now().date()
            if today.month >= 8:  # Aug-Dec
                season_year = today.year
            else:  # Jan-Jul
                season_year = today.year - 1

        cache_key = f"{league}_{season_year}"
        current_time = time.time()

        # Check cache first
        if cache_key in self._season_cache:
            cache_time, cached_fixtures = self._season_cache[cache_key]
            if current_time - cache_time < self._cache_ttl:
                logger.debug(f"Using cached season fixtures for {league} (season {season_year})")
                return cached_fixtures

        # Fetch all season fixtures in ONE request
        logger.info(f"Fetching ALL fixtures for {league} (season {season_year})...")
        params = {
            "league": league_id,
            "season": season_year
        }

        data = self._make_request("/fixtures", params)

        fixtures = []
        if data and data.get("response"):
            for fixture in data["response"]:
                match = self._parse_fixture(fixture)
                if match:
                    fixtures.append(match)

            # Cache the result
            self._season_cache[cache_key] = (current_time, fixtures)
            logger.info(f"Cached {len(fixtures)} fixtures for {league} (season {season_year})")
        else:
            logger.warning(f"No fixtures returned for {league} season {season_year}")

        return fixtures

    def get_fixtures(self, league: str = "premier_league", days: int = 7) -> List[Match]:
        """
        Get fixtures for the next N days from cached season data.
        FAST - no API call, uses 24h cache.

        Args:
            league: League key from LEAGUE_IDS
            days: Number of days to fetch

        Returns:
            List of Match objects
        """
        # Get all season fixtures from cache
        all_fixtures = self._get_season_fixtures(league)

        # Filter by date range locally
        today = datetime.now().date()
        end_date = today + timedelta(days=days)

        fixtures = []
        for match in all_fixtures:
            try:
                if isinstance(match.date, int):
                    match_datetime = datetime.fromtimestamp(match.date)
                else:
                    match_datetime = datetime.fromisoformat(match.date.replace('Z', '+00:00'))
                
                match_date = match_datetime.date()
                if today <= match_date <= end_date:
                    fixtures.append(match)
            except Exception as e:
                logger.error(f"Failed to parse match date: {e}")

        logger.info(f"Found {len(fixtures)} fixtures for {league} in next {days} days (from cache)")
        return fixtures

    def _date_range(self, start_date, end_date):
        """Generate date range."""
        current = start_date
        while current <= end_date:
            yield current
            current += timedelta(days=1)

    def _parse_fixture(self, fixture: Dict) -> Optional[Match]:
        """Parse fixture data into Match object."""
        try:
            teams = fixture.get("teams", {})
            goals = fixture.get("goals", {})
            fixture_info = fixture.get("fixture", {})
            league = fixture.get("league", {})
            
            return Match(
                id=str(fixture_info.get("id", "")),
                date=fixture_info.get("timestamp", 0),
                home_team=teams.get("home", {}).get("name", "Unknown"),
                away_team=teams.get("away", {}).get("name", "Unknown"),
                home_team_id=str(teams.get("home", {}).get("id", "")),
                away_team_id=str(teams.get("away", {}).get("id", "")),
                tournament=league.get("name", ""),
                home_score=goals.get("home"),
                away_score=goals.get("away"),
                status=fixture_info.get("status", {}).get("long", ""),
                venue=fixture_info.get("venue", {}).get("name", ""),
                referee=fixture_info.get("referee", "")
            )
        except Exception as e:
            logger.error(f"Failed to parse fixture: {e}")
            return None

    def get_match_details(self, match_id: str) -> Optional[MatchDetails]:
        """
        Get detailed match information with comprehensive statistics.

        Args:
            match_id: API-Football fixture ID

        Returns:
            MatchDetails object or None
        """
        # Get fixture details
        params = {"id": match_id}
        data = self._make_request("/fixtures", params)
        
        if not data or not data.get("response"):
            return None
        
        fixture = data["response"][0]
        match = self._parse_fixture(fixture)
        
        if not match:
            return None
        
        details = MatchDetails(match=match)
        
        # Get comprehensive statistics
        details.statistics = self._get_statistics(match_id)
        
        # Get lineups
        details.lineups = self._get_lineups(match_id)
        
        # Get odds
        details.odds = self._get_odds(match_id)
        
        # Get H2H (last 5-10 matches)
        details.h2h_matches = self._get_h2h(match.home_team_id, match.away_team_id, last=10)
        
        # Get team form - LAST 10 MATCHES for more context
        details.home_team_form = self._get_team_form(match.home_team_id, last=10)
        details.away_team_form = self._get_team_form(match.away_team_id, last=10)
        
        # Get injuries
        details.injuries = self._get_injuries(match.home_team_id, match.away_team_id)
        
        # Get league standings for context
        details.standings = self._get_standings(match.tournament, match.home_team_id, match.away_team_id)
        
        logger.info(f"Got FULL details for {match.home_team} vs {match.away_team} with 10-match form")
        
        return details

    def _get_statistics(self, match_id: str) -> Dict:
        """Get match statistics."""
        params = {"fixture": match_id}
        data = self._make_request("/fixtures/statistics", params)
        
        if not data or not data.get("response"):
            return {}
        
        stats = {}
        for team_stats in data["response"]:
            team_name = team_stats.get("team", {}).get("name", "Unknown")
            for stat in team_stats.get("statistics", []):
                key = stat.get("type", "")
                value = stat.get("value")
                if key and value is not None:
                    stats[f"{team_name}_{key}"] = value
        
        return stats

    def _get_lineups(self, match_id: str) -> Dict:
        """Get team lineups."""
        params = {"fixture": match_id}
        data = self._make_request("/fixtures/lineups", params)
        
        if not data or not data.get("response"):
            return {}
        
        return {"lineups": data["response"]}

    def _get_odds(self, match_id: str) -> Dict:
        """Get betting odds."""
        params = {"fixture": match_id}
        data = self._make_request("/odds", params)
        
        if not data or not data.get("response"):
            return {}
        
        return {"odds": data["response"]}

    def _get_h2h(self, home_team_id: str, away_team_id: str, last: int = 5) -> List[Dict]:
        """Get head-to-head history."""
        # Try multiple approaches for national teams vs club teams
        params_options = [
            {"h2h": f"{home_team_id}-{away_team_id}", "last": last},  # Club teams
            {"h2h": f"{home_team_id}-{away_team_id}", "last": last, "season": 2024},  # National teams
            {"h2h": f"{home_team_id}-{away_team_id}", "last": last, "season": 2025},  # National teams current
        ]

        for params in params_options:
            data = self._make_request("/fixtures/headtohead", params)
            if data and data.get("response"):
                break

        if not data or not data.get("response"):
            return []

        h2h = []
        for fixture in data["response"][:last]:
            teams = fixture.get("teams", {})
            goals = fixture.get("goals", {})
            h2h.append({
                "home_team": teams.get("home", {}).get("name", ""),
                "away_team": teams.get("away", {}).get("name", ""),
                "home_score": goals.get("home"),
                "away_score": goals.get("away"),
                "date": fixture.get("fixture", {}).get("timestamp", 0)
            })

        return h2h

    def _get_team_form(self, team_id: str, last: int = 5) -> List[Dict]:
        """Get team's last N matches (form)."""
        if not team_id:
            logger.warning("Empty team_id for form request")
            return []

        # For national teams, use /fixtures with team+league+season
        # For club teams, use /fixtures/team
        data = None

        # Try national team approach first (WC Qualification, Nations League)
        for league_id in [32, 5, 4, 1]:  # WC Qual, Nations League, Euro, World Cup
            for season in [2024, 2025, 2026]:
                params = {"team": team_id, "league": league_id, "season": season}
                logger.info(f"Fetching form for team {team_id}: league={league_id}, season={season}")
                result = self._make_request("/fixtures", params)
                if result and result.get("response"):
                    data = result
                    break
            if data:
                break

        # Fallback to club team approach
        if not data:
            logger.info(f"Trying club team approach for {team_id}")
            params = {"team": team_id, "last": last}
            data = self._make_request("/fixtures/team", params)

        if not data or not data.get("response"):
            logger.warning(f"No form data for team {team_id}")
            return []

        form = []
        for fixture in data["response"][:last]:
            teams = fixture.get("teams", {})
            goals = fixture.get("goals", {})

            # Determine if team won/lost/drew
            home_id = str(teams.get("home", {}).get("id", ""))
            is_home = home_id == team_id

            if is_home:
                team_goals = goals.get("home")
                opp_goals = goals.get("away")
                opponent = teams.get("away", {}).get("name", "")
            else:
                team_goals = goals.get("away")
                opp_goals = goals.get("home")
                opponent = teams.get("home", {}).get("name", "")

            if team_goals is not None and opp_goals is not None:
                if team_goals > opp_goals:
                    result = "W"
                elif team_goals < opp_goals:
                    result = "L"
                else:
                    result = "D"
            else:
                result = "?"

            form.append({
                "opponent": opponent,
                "result": result,
                "score": f"{team_goals if team_goals is not None else '-'}:{opp_goals if opp_goals is not None else '-'}",
                "date": fixture.get("fixture", {}).get("timestamp", 0),
                "is_home": is_home
            })

        logger.info(f"Got form for team {team_id}: {[f['result'] for f in form]}")
        return form

    def _get_injuries(self, home_team_id: str, away_team_id: str) -> Dict:
        """Get team injuries."""
        injuries = {}
        
        for team_id, team_name in [(home_team_id, "home"), (away_team_id, "away")]:
            params = {"team": team_id}
            data = self._make_request("/injuries", params)
            
            if data and data.get("response"):
                injuries[team_name] = [
                    {
                        "player": inj.get("player", {}).get("name", ""),
                        "reason": inj.get("reason", ""),
                        "expected": inj.get("expected", "")
                    }
                    for inj in data["response"]
                ]
        
        return injuries

    def _get_standings(self, league_name: str, home_team_id: str, away_team_id: str) -> Dict:
        """Get league standings for both teams."""
        # Find league ID from name
        league_id = None
        for name, lid in self.LEAGUE_IDS.items():
            if name in league_name.lower() or league_name.lower() in name:
                league_id = lid
                break
        
        if not league_id:
            return {}
        
        # Calculate season year
        today = datetime.now().date()
        season = today.year if today.month >= 8 else today.year - 1
        
        params = {"league": league_id, "season": season}
        data = self._make_request("/standings", params)
        
        if not data or not data.get("response"):
            return {}
        
        standings = {}
        for item in data["response"]:
            for team_data in item.get("league", {}).get("standings", []):
                for team in team_data:
                    team_id_str = str(team.get("team", {}).get("id", ""))
                    if team_id_str in [home_team_id, away_team_id]:
                        standings[team_id_str] = {
                            "position": team.get("rank", 0),
                            "points": team.get("points", 0),
                            "played": team.get("all", {}).get("played", 0),
                            "won": team.get("all", {}).get("won", 0),
                            "draw": team.get("all", {}).get("draw", 0),
                            "lost": team.get("all", {}).get("lost", 0),
                            "goals_for": team.get("all", {}).get("goals", {}).get("for", 0),
                            "goals_against": team.get("all", {}).get("goals", {}).get("against", 0),
                            "form": team.get("form", "")
                        }
        
        return standings

    def get_fixtures_by_date(self, league: str = "premier_league", days: int = 7) -> Dict[str, List[Match]]:
        """
        Get fixtures grouped by date from cached season data.
        INSTANT - uses 24h cache, no API call.

        Args:
            league: League key
            days: Number of days (for reference, not used for API call)

        Returns:
            Dict with date strings as keys and Match lists as values
        """
        # Get all season fixtures from cache
        all_fixtures = self._get_season_fixtures(league)

        fixtures_by_date = {}
        for match in all_fixtures:
            try:
                if isinstance(match.date, int):
                    match_datetime = datetime.fromtimestamp(match.date)
                else:
                    match_datetime = datetime.fromisoformat(match.date.replace('Z', '+00:00'))
                
                date_str = match_datetime.strftime("%d.%m.%Y (%A)")
                
                if date_str not in fixtures_by_date:
                    fixtures_by_date[date_str] = []
                fixtures_by_date[date_str].append(match)
            except Exception as e:
                logger.error(f"Failed to parse match date: {e}")

        logger.info(f"Grouped {sum(len(v) for v in fixtures_by_date.values())} fixtures by date for {league} (from cache)")
        return fixtures_by_date
