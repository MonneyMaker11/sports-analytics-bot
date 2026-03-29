"""
Flashscore Parser Module
Uses unofficial JSON feeds from Flashscore for football match data.
Also uses Football-Data.org API as fallback for fixtures.

WARNING: Web scraping may violate Flashscore's Terms of Service.
Use responsibly and consider official APIs for production use.
"""

import datetime
import json
import logging
import time
from typing import Optional, Dict, List
from dataclasses import dataclass, field

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


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


class FlashscoreParser:
    """
    Parser for Flashscore football data using unofficial JSON feeds.
    Falls back to HTML parsing if JSON feeds fail.
    """

    BASE_URL = "https://www.flashscore.com"
    FEED_URL = "https://www.flashscore.com/feed/"

    # Football-Data.org API (free tier)
    FOOTBALL_DATA_API = "https://api.football-data.org/v4"
    
    # API-Football for team form and statistics (free: 100 req/day)
    API_FOOTBALL_BASE = "https://v3.football.api-sports.io"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.flashscore.com/",
    }

    LEAGUE_URLS = {
        "premier_league": "/en/football/england/premier-league/fixtures/",
        "la_liga": "/en/football/spain/la-liga/fixtures/",
        "bundesliga": "/en/football/germany/bundesliga/fixtures/",
        "serie_a": "/en/football/italy/serie-a/fixtures/",
        "ligue_1": "/en/football/france/ligue-1/fixtures/",
        "champions_league": "/en/football/europe/champions-league/fixtures/",
    }

    # Football-Data.org competition IDs
    COMPETITION_IDS = {
        "premier_league": "PL",      # Premier League
        "la_liga": "PD",             # Primera Division
        "bundesliga": "BL1",         # Bundesliga
        "serie_a": "SA",             # Serie A
        "ligue_1": "FL1",            # Ligue 1
        "champions_league": "CL",    # Champions League
    }

    def __init__(self, request_delay: float = 1.0, timeout: int = 10, football_data_api_key: Optional[str] = None):
        """
        Initialize the parser.

        Args:
            request_delay: Delay between requests in seconds
            timeout: Request timeout in seconds
            football_data_api_key: Optional API key for football-data.org
        """
        self.request_delay = request_delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.football_data_api_key = football_data_api_key
        self.football_data_session = requests.Session()
        if football_data_api_key:
            self.football_data_session.headers.update({"X-Auth-Token": football_data_api_key})
        
        # Cache for API responses (key: (league, days) -> value: (timestamp, result))
        self._api_cache = {}
        self._cache_ttl = 300  # 5 minutes

    def _make_request(self, url: str, params: Optional[dict] = None) -> Optional[str]:
        """
        Make HTTP request with error handling.
        
        Args:
            url: URL to request
            params: Optional query parameters
            
        Returns:
            Response text or None if failed
        """
        try:
            time.sleep(self.request_delay)
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None

    def _parse_feed_response(self, feed_data: str) -> list:
        """
        Parse Flashscore feed JSON response.
        
        Args:
            feed_data: Raw feed response string
            
        Returns:
            List of match data dictionaries
        """
        try:
            import json
            data = json.loads(feed_data)
            if isinstance(data, dict) and "events" in data:
                return data["events"]
            elif isinstance(data, list):
                return data
            return []
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse feed response: {e}")
            return []

    def get_matches_by_date(self, league: str = "premier_league", days: int = 30) -> dict:
        """
        Get matches grouped by date for the next N days.
        Uses multiple sources: Football-Data.org API, Flashscore feed, HTML parsing.

        Args:
            league: League key from LEAGUE_URLS
            days: Number of days to fetch matches for (default: 30)

        Returns:
            Dict with date strings as keys and lists of Match objects as values
        """
        if league not in self.LEAGUE_URLS:
            logger.error(f"Unknown league: {league}")
            return {}

        matches_by_date = {}
        base_url = f"{self.BASE_URL}{self.LEAGUE_URLS[league]}"

        logger.info(f"Fetching matches for league: {league}, days: {days}")

        # First try Football-Data.org API (most reliable for fixtures)
        api_matches = self._get_matches_from_football_data(league, days)
        if api_matches:
            logger.info(f"Found {len(api_matches)} matches from Football-Data.org API")
            # Group by date
            for match in api_matches:
                try:
                    match_date = datetime.datetime.fromisoformat(match.date.replace('Z', '+00:00')).date()
                    display_date = match_date.strftime("%d.%m.%Y (%A)")
                    if display_date not in matches_by_date:
                        matches_by_date[display_date] = []
                    matches_by_date[display_date].append(match)
                except (ValueError, AttributeError):
                    continue
            
            if matches_by_date:
                logger.info(f"Found {len(matches_by_date)} days with matches from API")
                return matches_by_date

        logger.info("No matches from API, trying Flashscore...")
        
        # Fallback to Flashscore feed
        feed_params = {"lang": "en", "timezone": "UTC"}
        feed_response = self._make_request(self.FEED_URL, feed_params)

        if feed_response:
            events = self._parse_feed_response(feed_response)
            all_matches = self._extract_matches_from_events(events)
            
            if all_matches:
                for day_offset in range(days):
                    day_matches = self._filter_matches_by_day(all_matches, day_offset)
                    if day_matches:
                        target_date = self._get_target_date(day_offset)
                        display_date = target_date.strftime("%d.%m.%Y (%A)")
                        matches_by_date[display_date] = day_matches

        # Fallback to HTML parsing if still no matches
        if not matches_by_date:
            logger.info("Falling back to HTML parsing...")
            html_matches = self._get_matches_from_html(base_url)
            for day_offset in range(days):
                day_matches = self._filter_matches_by_day(html_matches, day_offset)
                if day_matches:
                    target_date = self._get_target_date(day_offset)
                    display_date = target_date.strftime("%d.%m.%Y (%A)")
                    matches_by_date[display_date] = day_matches

        logger.info(f"Found {len(matches_by_date)} days with matches in total")
        return matches_by_date

    def _get_matches_from_football_data(self, league: str, days: int) -> list[Match]:
        """
        Get fixtures from Football-Data.org API.
        Free tier: 10 requests/min, covers major leagues.
        Uses caching to avoid rate limits.

        Args:
            league: League key
            days: Number of days to fetch

        Returns:
            List of Match objects
        """
        if league not in self.COMPETITION_IDS:
            return []
        
        # Check cache first
        cache_key = (league, days)
        current_time = time.time()
        if cache_key in self._api_cache:
            cache_time, cached_result = self._api_cache[cache_key]
            if current_time - cache_time < self._cache_ttl:
                logger.debug(f"Using cached result for {league}")
                return cached_result

        competition_id = self.COMPETITION_IDS[league]
        today = datetime.date.today()
        end_date = today + datetime.timedelta(days=days)

        # Get current season info first (with caching)
        season_info = self._get_current_season(competition_id)
        season = season_info.get("year", 2025) if season_info else 2025

        url = f"{self.FOOTBALL_DATA_API}/competitions/{competition_id}/matches"
        params = {
            "season": season,
        }

        try:
            time.sleep(6)  # Rate limiting: 10 req/min = 6 sec delay
            response = self.football_data_session.get(url, params=params, timeout=self.timeout)

            if response.status_code == 429:
                logger.warning("Football-Data.org API rate limit exceeded")
                return []

            if response.status_code != 200:
                logger.warning(f"Football-Data.org API returned status {response.status_code}")
                return []

            data = response.json()
            matches = []

            # Filter matches by date range
            for match_data in data.get("matches", []):
                match_date_str = match_data.get("utcDate", "")
                if not match_date_str:
                    continue

                try:
                    match_date = datetime.datetime.fromisoformat(match_date_str.replace('Z', '+00:00')).date()
                except (ValueError, AttributeError):
                    continue

                # Only include matches within our date range
                if match_date < today or match_date > end_date:
                    continue

                home_team = match_data.get("homeTeam", {}).get("name", "Unknown")
                away_team = match_data.get("awayTeam", {}).get("name", "Unknown")
                status = match_data.get("status", "SCHEDULED")
                score = match_data.get("score", {})

                match = Match(
                    id=f"fd_{competition_id}_{match_data.get('id', '')}",
                    date=match_date_str,
                    home_team=home_team,
                    away_team=away_team,
                    tournament=data.get("competition", {}).get("name", league),
                    home_score=score.get("fullTime", {}).get("home"),
                    away_score=score.get("fullTime", {}).get("away"),
                    status=status,
                    home_team_id=str(match_data.get("homeTeam", {}).get("id", "")),
                    away_team_id=str(match_data.get("awayTeam", {}).get("id", "")),
                )
                matches.append(match)

            # Cache the result
            self._api_cache[cache_key] = (current_time, matches)
            logger.info(f"Cached {len(matches)} matches for {league}")

            return matches

        except requests.RequestException as e:
            logger.error(f"Football-Data.org API request failed: {e}")
            return []
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse Football-Data.org response: {e}")
            return []

    def _get_current_season(self, competition_id: str) -> dict:
        """
        Get current season info for a competition.

        Args:
            competition_id: League competition ID

        Returns:
            Dict with season info or empty dict
        """
        url = f"{self.FOOTBALL_DATA_API}/competitions/{competition_id}"

        try:
            time.sleep(0.3)
            response = self.football_data_session.get(url, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                current_season = data.get("currentSeason", {})
                if current_season:
                    # Extract year from startDate (e.g., "2025-08-15" -> 2025)
                    start_date = current_season.get("startDate", "")
                    year = int(start_date.split("-")[0]) if start_date else 2025
                    return {"year": year, "id": current_season.get("id")}
            return {}

        except (requests.RequestException, json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to get season info: {e}")
            return {}

    def _get_target_date(self, day_offset: int) -> datetime.date:
        """Get target date by offset from today."""
        today = datetime.date.today()
        return today + datetime.timedelta(days=day_offset)

    def get_available_dates(self, league: str = "premier_league", days: int = 7) -> list[str]:
        """
        Get list of dates that have matches.

        Args:
            league: League key from LEAGUE_URLS
            days: Number of days to check

        Returns:
            List of date display strings
        """
        matches_by_date = self.get_matches_by_date(league, days)
        return list(matches_by_date.keys())

    def _filter_matches_by_day(self, matches: list[Match], day_offset: int) -> list[Match]:
        """
        Filter matches by day offset from today.
        
        Args:
            matches: List of Match objects
            day_offset: 0 for today, 1 for tomorrow, etc.
            
        Returns:
            Filtered list of matches
        """
        today = datetime.date.today()
        target_date = today + datetime.timedelta(days=day_offset)
        target_str = target_date.strftime("%Y-%m-%d")
        
        filtered = []
        for match in matches:
            # Try to match date from timestamp or string
            try:
                if isinstance(match.date, int):
                    # Unix timestamp
                    match_datetime = datetime.datetime.fromtimestamp(match.date)
                    match_date_str = match_datetime.strftime("%Y-%m-%d")
                else:
                    # String date - try various formats
                    match_date_str = str(match.date)
                    # Extract date part if it contains time
                    if " " in match_date_str:
                        match_date_str = match_date_str.split(" ")[0]
                
                if target_str in match_date_str or match_date_str in target_str:
                    filtered.append(match)
            except (ValueError, AttributeError):
                # If date parsing fails, include the match anyway
                filtered.append(match)
        
        return filtered if filtered else matches[:10]  # Return first 10 if no date match

    def _extract_matches_from_events(self, events: list) -> list[Match]:
        """Extract Match objects from feed events."""
        matches = []
        for event in events:
            try:
                match = Match(
                    id=event.get("id", ""),
                    date=event.get("startTimestamp", ""),
                    home_team=event.get("homeTeam", {}).get("name", ""),
                    away_team=event.get("awayTeam", {}).get("name", ""),
                    home_team_id=str(event.get("homeTeam", {}).get("id", "")),
                    away_team_id=str(event.get("awayTeam", {}).get("id", "")),
                    tournament=event.get("tournament", {}).get("name", ""),
                    home_score=event.get("homeScore", {}).get("current"),
                    away_score=event.get("awayScore", {}).get("current"),
                    status=event.get("status", {}).get("type", ""),
                )
                if match.home_team and match.away_team:
                    matches.append(match)
            except (KeyError, AttributeError) as e:
                logger.warning(f"Failed to parse event: {e}")
                continue
        return matches

    def _get_matches_from_html(self, url: str) -> list[Match]:
        """Parse matches from HTML page as fallback."""
        html = self._make_request(url)
        if not html:
            return []

        matches = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # Look for match rows
            match_rows = soup.select("div.event__row")
            
            for row in match_rows:
                try:
                    match_id = row.get("id", "").replace("event_", "")
                    
                    home_team_el = row.select_one("div.event__participant--home")
                    away_team_el = row.select_one("div.event__participant--away")
                    
                    if not home_team_el or not away_team_el:
                        continue

                    home_team = home_team_el.get_text(strip=True)
                    away_team = away_team_el.get_text(strip=True)
                    
                    time_el = row.select_one("div.event__time")
                    date = time_el.get_text(strip=True) if time_el else ""
                    
                    score_el = row.select_one("div.event__scores")
                    home_score, away_score = None, None
                    if score_el:
                        scores = score_el.get_text(strip=True).split(":")
                        if len(scores) == 2:
                            home_score = int(scores[0]) if scores[0].isdigit() else None
                            away_score = int(scores[1]) if scores[1].isdigit() else None

                    match = Match(
                        id=match_id,
                        date=date,
                        home_team=home_team,
                        away_team=away_team,
                        home_score=home_score,
                        away_score=away_score,
                    )
                    matches.append(match)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse match row: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"HTML parsing failed: {e}")

        logger.info(f"Found {len(matches)} matches via HTML parsing")
        return matches

    def get_match_details(self, match_id: str) -> Optional[MatchDetails]:
        """
        Get detailed match information.
        Handles both Flashscore IDs and Football-Data.org IDs.

        Args:
            match_id: Flashscore or Football-Data.org match ID

        Returns:
            MatchDetails object or None if failed
        """
        # Check if this is a Football-Data.org ID (starts with fd_)
        if match_id.startswith("fd_"):
            logger.info(f"Football-Data.org ID detected: {match_id}")
            # Return minimal details - analysis will use form data only
            return self._create_minimal_details(match_id)
        
        # Original Flashscore logic
        # First, get basic match info
        match_url = f"{self.BASE_URL}/match/{match_id}/"
        html = self._make_request(match_url)

        if not html:
            return None

        match = self._parse_match_from_html(html)
        if not match:
            return None

        details = MatchDetails(match=match)

        # Get statistics
        details.statistics = self._get_match_statistics(match_id)

        # Get team form (last 5 matches)
        if match.home_team_id:
            details.home_team_form = self._get_team_form(match.home_team_id)
        if match.away_team_id:
            details.away_team_form = self._get_team_form(match.away_team_id)

        # Get head-to-head history
        details.h2h_matches = self._get_h2h_matches(match_id)

        # Get odds
        details.odds = self._get_match_odds(match_id)

        return details

    def _create_minimal_details(self, match_id: str, match: Optional[Match] = None) -> Optional[MatchDetails]:
        """
        Create minimal MatchDetails for Football-Data.org matches.
        Uses cached data from get_matches_by_date.
        """
        # Try to find match in cache
        for cache_key, (cache_time, cached_matches) in self._api_cache.items():
            for m in cached_matches:
                if m.id == match_id:
                    match = m
                    break
        
        if not match:
            logger.warning(f"Match {match_id} not found in cache")
            return None
        
        # Get team form for both teams
        home_form = []
        away_form = []
        
        if match.home_team_id:
            home_form = self._get_team_form(match.home_team_id)
        if match.away_team_id:
            away_form = self._get_team_form(match.away_team_id)
        
        # Create details with form data
        details = MatchDetails(
            match=match,
            statistics={},
            home_team_form=home_form,
            away_team_form=away_form,
            h2h_matches=[],
            odds={}
        )
        logger.info(f"Created minimal details for {match_id} with form data")
        return details

    def _parse_match_from_html(self, html: str) -> Optional[Match]:
        """Parse basic match info from HTML."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # Extract match ID from page
            match_id = ""
            if "matchId" in html:
                import re
                match = re.search(r'matchId\s*=\s*["\']?(\w+)["\']?', html)
                if match:
                    match_id = match.group(1)

            # Team names
            home_team_el = soup.select_one("div.team--home")
            away_team_el = soup.select_one("div.team--away")
            
            home_team = home_team_el.get_text(strip=True) if home_team_el else ""
            away_team = away_team_el.get_text(strip=True) if away_team_el else ""

            # Tournament
            tournament_el = soup.select_one("div.tournament__name")
            tournament = tournament_el.get_text(strip=True) if tournament_el else ""

            # Date
            date_el = soup.select_one("div.match__date")
            date = date_el.get_text(strip=True) if date_el else ""

            # Score
            score_el = soup.select_one("div.score__current")
            home_score, away_score = None, None
            if score_el:
                scores = score_el.get_text(strip=True).split(":")
                if len(scores) == 2:
                    home_score = int(scores[0]) if scores[0].isdigit() else None
                    away_score = int(scores[1]) if scores[1].isdigit() else None

            return Match(
                id=match_id,
                date=date,
                home_team=home_team,
                away_team=away_team,
                tournament=tournament,
                home_score=home_score,
                away_score=away_score,
            )

        except Exception as e:
            logger.error(f"Failed to parse match from HTML: {e}")
            return None

    def _get_match_statistics(self, match_id: str) -> dict:
        """Get match statistics from feed."""
        stats_url = f"{self.FEED_URL}?uri=/match/{match_id}/statistics/"
        response = self._make_request(stats_url)
        
        if not response:
            return {}

        try:
            import json
            data = json.loads(response)
            statistics = {}
            
            if isinstance(data, dict) and "statistics" in data:
                for stat in data["statistics"]:
                    name = stat.get("name", "")
                    home = stat.get("home", "")
                    away = stat.get("away", "")
                    statistics[name] = {"home": home, "away": away}
                    
            return statistics
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse statistics: {e}")
            return {}

    def _get_team_form(self, team_id: str) -> list:
        """Get team's last 5 matches (form)."""
        form_url = f"{self.FEED_URL}?uri=/team/{team_id}/results/"
        response = self._make_request(form_url)
        
        if not response:
            return []

        try:
            import json
            data = json.loads(response)
            form_matches = []
            
            events = data.get("events", []) if isinstance(data, dict) else data
            for event in events[:5]:  # Last 5 matches
                match_info = {
                    "opponent": "",
                    "result": "",
                    "score": "",
                    "date": "",
                }
                
                home_team = event.get("homeTeam", {}).get("name", "")
                away_team = event.get("awayTeam", {}).get("name", "")
                home_score = event.get("homeScore", {}).get("current", "")
                away_score = event.get("awayScore", {}).get("current", "")
                
                # Determine if team won/lost/drew
                is_home = event.get("homeTeam", {}).get("id") == int(team_id)
                if is_home:
                    match_info["opponent"] = away_team
                    match_info["score"] = f"{home_score}:{away_score}"
                    if home_score > away_score:
                        match_info["result"] = "W"
                    elif home_score < away_score:
                        match_info["result"] = "L"
                    else:
                        match_info["result"] = "D"
                else:
                    match_info["opponent"] = home_team
                    match_info["score"] = f"{away_score}:{home_score}"
                    if away_score > home_score:
                        match_info["result"] = "W"
                    elif away_score < home_score:
                        match_info["result"] = "L"
                    else:
                        match_info["result"] = "D"
                
                match_info["date"] = event.get("startTimestamp", "")
                form_matches.append(match_info)
                
            return form_matches
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse team form: {e}")
            return []

    def _get_h2h_matches(self, match_id: str) -> list:
        """Get head-to-head match history."""
        h2h_url = f"{self.FEED_URL}?uri=/match/{match_id}/head-to-head/"
        response = self._make_request(h2h_url)
        
        if not response:
            return []

        try:
            import json
            data = json.loads(response)
            h2h_matches = []
            
            events = data.get("events", []) if isinstance(data, dict) else data
            for event in events[:5]:  # Last 5 H2H matches
                match_info = {
                    "home_team": event.get("homeTeam", {}).get("name", ""),
                    "away_team": event.get("awayTeam", {}).get("name", ""),
                    "home_score": event.get("homeScore", {}).get("current", ""),
                    "away_score": event.get("awayScore", {}).get("current", ""),
                    "date": event.get("startTimestamp", ""),
                }
                h2h_matches.append(match_info)
                
            return h2h_matches
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse H2H: {e}")
            return []

    def _get_match_odds(self, match_id: str) -> dict:
        """Get pre-match odds."""
        odds_url = f"{self.FEED_URL}?uri=/match/{match_id}/prematch-odds/"
        response = self._make_request(odds_url)
        
        if not response:
            return {}

        try:
            import json
            data = json.loads(response)
            odds = {}
            
            if isinstance(data, dict):
                bookmakers = data.get("bookmakers", [])
                for bookmaker in bookmakers:
                    bookmaker_name = bookmaker.get("name", "Unknown")
                    markets = bookmaker.get("markets", [])
                    for market in markets:
                        market_name = market.get("name", "")
                        selections = market.get("selections", [])
                        odds[bookmaker_name] = {
                            market_name: [
                                {
                                    "name": sel.get("name", ""),
                                    "value": sel.get("odds", ""),
                                }
                                for sel in selections
                            ]
                        }
                        
            return odds
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse odds: {e}")
            return {}


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    parser = FlashscoreParser(request_delay=0.5)
    
    # Get today's matches
    print("Fetching today's matches...")
    matches = parser.get_today_matches("premier_league")
    
    for match in matches:
        print(f"\n{match.home_team} vs {match.away_team}")
        print(f"  Tournament: {match.tournament}")
        print(f"  Date: {match.date}")
        
        if match.id:
            print("  Fetching match details...")
            details = parser.get_match_details(match.id)
            if details:
                print(f"  Statistics: {details.statistics}")
                print(f"  Home form: {details.home_team_form}")
                print(f"  Away form: {details.away_team_form}")
                print(f"  H2H: {details.h2h_matches}")
