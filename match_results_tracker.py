"""
Match Results Tracker Module
Tracks matches users requested analysis for and sends post-match reports.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import json
import os

from telegram import Update
from telegram.ext import Application

logger = logging.getLogger(__name__)


@dataclass
class TrackedMatch:
    """Represents a match being tracked for post-match report."""
    match_id: str
    user_id: int
    home_team: str
    away_team: str
    tournament: str
    match_date: str
    predictions: Dict = field(default_factory=dict)
    report_sent: bool = False


class MatchResultsTracker:
    """
    Tracks matches and sends post-match analysis reports.
    """

    def __init__(self, data_file: str = "tracked_matches.json"):
        self.data_file = data_file
        self.tracked_matches: Dict[str, TrackedMatch] = {}
        self.load_matches()

    def track_match(
        self,
        match_id: str,
        user_id: int,
        home_team: str,
        away_team: str,
        tournament: str,
        match_date: str,
        predictions: Dict
    ) -> None:
        """Add a match to tracking."""
        tracked = TrackedMatch(
            match_id=match_id,
            user_id=user_id,
            home_team=home_team,
            away_team=away_team,
            tournament=tournament,
            match_date=match_date,
            predictions=predictions,
            report_sent=False
        )
        self.tracked_matches[match_id] = tracked
        self.save_matches()
        logger.info(f"Tracking match {match_id}: {home_team} vs {away_team} for user {user_id}")

    def get_tracked_match(self, match_id: str) -> Optional[TrackedMatch]:
        """Get tracked match by ID."""
        return self.tracked_matches.get(match_id)

    def mark_report_sent(self, match_id: str) -> None:
        """Mark report as sent for a match."""
        if match_id in self.tracked_matches:
            self.tracked_matches[match_id].report_sent = True
            self.save_matches()

    def save_matches(self) -> None:
        """Save tracked matches to file."""
        data = {}
        for match_id, match in self.tracked_matches.items():
            data[match_id] = {
                'match_id': match.match_id,
                'user_id': match.user_id,
                'home_team': match.home_team,
                'away_team': match.away_team,
                'tournament': match.tournament,
                'match_date': match.match_date,
                'predictions': match.predictions,
                'report_sent': match.report_sent
            }
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_matches(self) -> None:
        """Load tracked matches from file."""
        if not os.path.exists(self.data_file):
            return
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for match_id, match_data in data.items():
                self.tracked_matches[match_id] = TrackedMatch(
                    match_id=match_data['match_id'],
                    user_id=match_data['user_id'],
                    home_team=match_data['home_team'],
                    away_team=match_data['away_team'],
                    tournament=match_data['tournament'],
                    match_date=match_data['match_date'],
                    predictions=match_data.get('predictions', {}),
                    report_sent=match_data.get('report_sent', False)
                )
            
            logger.info(f"Loaded {len(self.tracked_matches)} tracked matches")
        except Exception as e:
            logger.error(f"Failed to load tracked matches: {e}")

    def cleanup_old_matches(self, days: int = 7) -> None:
        """Remove old tracked matches."""
        cutoff = datetime.now() - timedelta(days=days)
        to_remove = []
        
        for match_id, match in self.tracked_matches.items():
            try:
                match_date = datetime.fromisoformat(match.match_date.replace('Z', '+00:00'))
                if match_date < cutoff or match.report_sent:
                    to_remove.append(match_id)
            except:
                to_remove.append(match_id)
        
        for match_id in to_remove:
            del self.tracked_matches[match_id]
        
        if to_remove:
            self.save_matches()
            logger.info(f"Cleaned up {len(to_remove)} old tracked matches")


class PostMatchReporter:
    """
    Generates and sends post-match analysis reports.
    """

    def __init__(self, tracker: MatchResultsTracker, parser):
        self.tracker = tracker
        self.parser = parser

    def generate_report(self, match_id: str, actual_result: Dict) -> Optional[str]:
        """
        Generate post-match report comparing predictions with actual result.
        
        Args:
            match_id: Match ID
            actual_result: Dict with actual match result (home_score, away_score, etc.)
        
        Returns:
            Formatted report string or None
        """
        tracked = self.tracker.get_tracked_match(match_id)
        if not tracked or tracked.report_sent:
            return None
        
        predictions = tracked.predictions
        home_score = actual_result.get('home_score')
        away_score = actual_result.get('away_score')
        
        if home_score is None or away_score is None:
            return None
        
        # Determine actual result
        if home_score > away_score:
            actual_outcome = "П1"
        elif home_score < away_score:
            actual_outcome = "П2"
        else:
            actual_outcome = "X"
        
        total_goals = home_score + away_score
        btts = "Да" if home_score > 0 and away_score > 0 else "Нет"
        
        # Build report
        report = []
        report.append("⚽ **РЕЗУЛЬТАТ МАТЧА**")
        report.append(f"{tracked.home_team} {home_score}:{away_score} {tracked.away_team}")
        report.append(f"🏆 {tracked.tournament}\n")
        
        # 1X2 Prediction Check
        report.append("📊 **ИСХОД 1X2:**")
        pred_home = predictions.get('home_win_pct', 0)
        pred_draw = predictions.get('draw_pct', 0)
        pred_away = predictions.get('away_win_pct', 0)
        
        if actual_outcome == "П1":
            report.append(f"✅ **П1** (прогноз: {pred_home}%)")
        elif actual_outcome == "X":
            report.append(f"✅ **X** (прогноз: {pred_draw}%)")
        else:
            report.append(f"✅ **П2** (прогноз: {pred_away}%)")
        
        report.append(f"   Фактически: {actual_outcome} ({home_score}:{away_score})\n")
        
        # Total Goals Check
        report.append("⚽ **ТОТАЛ ГОЛОВ:**")
        over_2_5 = predictions.get('over_2_5_pct', 0)
        under_2_5 = predictions.get('under_2_5_pct', 0)
        
        if total_goals > 2.5:
            report.append(f"✅ **ТБ 2.5** (прогноз: {over_2_5}%)")
        else:
            report.append(f"✅ **ТМ 2.5** (прогноз: {under_2_5}%)")
        
        report.append(f"   Фактически: {total_goals} голов\n")
        
        # BTTS Check
        report.append("🎯 **ОБЕ ЗАБЬЮТ:**")
        btts_yes = predictions.get('btts_yes_pct', 0)
        btts_no = predictions.get('btts_no_pct', 0)
        
        if btts == "Да":
            report.append(f"✅ **Да** (прогноз: {btts_yes}%)")
        else:
            report.append(f"✅ **Нет** (прогноз: {btts_no}%)")
        
        report.append(f"   Фактически: {btts}\n")
        
        # Correct Score Check (if available)
        likely_scores = predictions.get('likely_scores', [])
        if likely_scores:
            actual_score = f"{home_score}:{away_score}"
            score_predicted = any(s['score'] == actual_score for s in likely_scores)
            
            report.append("🎲 **ТОЧНЫЙ СЧЕТ:**")
            if score_predicted:
                report.append(f"✅ **Угадан!** {actual_score}")
            else:
                top_score = likely_scores[0] if likely_scores else None
                if top_score:
                    report.append(f"❌ Прогноз: {top_score['score']} ({top_score['prob']}%)")
                    report.append(f"   Фактически: {actual_score}")
            report.append("")
        
        # Summary
        report.append("📈 **ИТОГ:**")
        
        # Calculate accuracy
        accuracy_checks = []
        
        # 1X2
        if actual_outcome == "П1" and pred_home >= 40:
            accuracy_checks.append(True)
        elif actual_outcome == "X" and pred_draw >= 25:
            accuracy_checks.append(True)
        elif actual_outcome == "П2" and pred_away >= 40:
            accuracy_checks.append(True)
        else:
            accuracy_checks.append(False)
        
        # Total
        if (total_goals > 2.5 and over_2_5 >= 50) or (total_goals <= 2.5 and under_2_5 >= 50):
            accuracy_checks.append(True)
        else:
            accuracy_checks.append(False)
        
        # BTTS
        if (btts == "Да" and btts_yes >= 50) or (btts == "Нет" and btts_no >= 50):
            accuracy_checks.append(True)
        else:
            accuracy_checks.append(False)
        
        correct = sum(accuracy_checks)
        total = len(accuracy_checks)
        accuracy = round(correct / total * 100) if total > 0 else 0
        
        if accuracy >= 67:
            report.append(f"✅ Отличный прогноз! Точность: {accuracy}%")
        elif accuracy >= 50:
            report.append(f"⚠️ Неплохо! Точность: {accuracy}%")
        else:
            report.append(f"❌ Неудачный прогноз. Точность: {accuracy}%")
        
        report.append("\n⚠️ _Ставки — это риск. Прошлые результаты не гарантируют будущие._")
        
        return "\n".join(report)

    async def check_and_send_reports(
        self,
        app: Application,
        finished_matches: List[Dict]
    ) -> int:
        """
        Check finished matches and send reports to users.
        
        Args:
            app: Telegram application
            finished_matches: List of finished match results
        
        Returns:
            Number of reports sent
        """
        reports_sent = 0
        
        for match_result in finished_matches:
            match_id = str(match_result.get('fixture', {}).get('id', ''))
            
            if not match_id:
                continue
            
            tracked = self.tracker.get_tracked_match(match_id)
            if not tracked or tracked.report_sent:
                continue
            
            # Check if match is finished
            status = match_result.get('fixture', {}).get('status', {}).get('short', '')
            if status not in ['FT', 'AET', 'PEN']:
                continue
            
            # Get actual result
            goals = match_result.get('goals', {})
            actual_result = {
                'home_score': goals.get('home'),
                'away_score': goals.get('away')
            }
            
            # Generate report
            report = self.generate_report(match_id, actual_result)
            if not report:
                continue
            
            # Send report to user
            try:
                await app.bot.send_message(
                    chat_id=tracked.user_id,
                    text=report,
                    parse_mode='Markdown'
                )
                
                self.tracker.mark_report_sent(match_id)
                reports_sent += 1
                
                logger.info(f"Sent post-match report to user {tracked.user_id} for match {match_id}")
            except Exception as e:
                logger.error(f"Failed to send report to user {tracked.user_id}: {e}")
        
        return reports_sent
