"""
Telegram Bot for Football Match Analysis
Uses API-Football for comprehensive match data.
Flow: Sport → Date → League → Match → Analysis
"""

import asyncio
import datetime
import logging
import os
import re
from typing import Optional, Dict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv

from api_football_parser import APIFootballParser, Match, MatchDetails
from ai_analyzer import AIAnalyzer
from match_results_tracker import MatchResultsTracker, PostMatchReporter

logger = logging.getLogger(__name__)

load_dotenv()

# Conversation states
SELECT_SPORT, SELECT_DATE, SELECT_LEAGUE, SELECT_MATCH = range(4)

# Persistent keyboard for easy access
MAIN_KEYBOARD = ReplyKeyboardMarkup([
    [KeyboardButton("📅 Анализ матча")],
    [KeyboardButton("✅ Проверить результаты")],
    [KeyboardButton("ℹ️ Помощь")]
], resize_keyboard=True)


class FootballBot:
    """
    Telegram bot for football match analysis.
    """

    def __init__(self, token: str, default_league: str = "premier_league"):
        """
        Initialize the bot.

        Args:
            token: Telegram bot token
            default_league: Default league to fetch matches for
        """
        api_football_key = os.getenv("API_FOOTBALL_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_football_key:
            logger.error("API_FOOTBALL_KEY not found in environment variables")

        self.parser = APIFootballParser(api_key=api_football_key or "")
        self.analyzer = AIAnalyzer() if anthropic_key else None
        
        if not self.analyzer:
            logger.warning("ANTHROPIC_API_KEY not set - AI analysis will not work!")
        
        self.default_league = default_league

        self.application = Application.builder().token(token).build()
        
        # Initialize match results tracker
        self.tracker = MatchResultsTracker()
        self.reporter = PostMatchReporter(self.tracker, self.parser)
        
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up command and callback handlers."""
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(CommandHandler("checkresults", self.cmd_check_results))

        # Handle keyboard button text as messages
        self.application.add_handler(MessageHandler(
            filters.Regex("^📅 Анализ матча$"),
            self.cmd_start_analysis
        ))
        self.application.add_handler(MessageHandler(
            filters.Regex("^ℹ️ Помощь$"),
            self.cmd_help
        ))
        self.application.add_handler(MessageHandler(
            filters.Regex("^✅ Проверить результаты$"),
            self.cmd_check_results
        ))

        # Conversation handlers
        self.application.add_handler(CallbackQueryHandler(self.on_sport_select, pattern=r"^sport_"))
        self.application.add_handler(CallbackQueryHandler(self.on_date_select, pattern=r"^date_"))
        self.application.add_handler(CallbackQueryHandler(self.on_league_select, pattern=r"^league_"))
        self.application.add_handler(CallbackQueryHandler(self.on_match_select, pattern=r"^match_"))
        self.application.add_handler(CallbackQueryHandler(self.cmd_check_results_inline, pattern=r"^check_results$"))
        self.application.add_handler(CallbackQueryHandler(self.cmd_check_match_report, pattern=r"^check_match_"))
        self.application.add_handler(CallbackQueryHandler(self.cmd_ignore_callback, pattern=r"^separator"))

    async def cmd_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /start command."""
        await update.message.reply_text(
            "👋 Добро пожаловать в бота для анализа спортивных матчей!\n\n"
            "Я помогу вам получить прогнозы на матчи с помощью ИИ и статистики.\n\n"
            "📌 Нажмите кнопку внизу или используйте команды:\n"
            "/start — начать анализ\n"
            "/help — помощь\n\n"
            "🔹 Бот использует API-Football для данных и Claude AI для анализа.",
            reply_markup=MAIN_KEYBOARD
        )
        logger.info(f"User {update.effective_user.id} started the bot")

    async def cmd_start_analysis(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle Analyze button - start sport selection."""
        # Get the message object
        if update.message:
            target = update.message
        else:
            return
        
        # Sport selection keyboard
        sports = {
            "football": "⚽ Футбол",
            "hockey": "🏒 Хоккей (скоро)",
            "basketball": "🏀 Баскетбол (скоро)",
            "tennis": "🎾 Теннис (скоро)",
        }
        
        keyboard = []
        for sport_key, sport_name in sports.items():
            if sport_key == "football":
                keyboard.append([InlineKeyboardButton(sport_name, callback_data=f"sport_{sport_key}")])
            else:
                keyboard.append([InlineKeyboardButton(sport_name, callback_data=f"sport_{sport_key}_coming_soon")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await target.reply_text(
            "🏆 **Выберите вид спорта:**",
            reply_markup=reply_markup
        )

    async def on_sport_select(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle sport selection."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        if "coming_soon" in data:
            await query.answer("Этот вид спорта будет доступен в будущем!", show_alert=True)
            return
        
        sport = data.replace("sport_", "")
        context.user_data["selected_sport"] = sport
        
        if sport != "football":
            await query.edit_message_text("⚽ Футбол выбран!\n\n📅 Загружаю даты...")
        
        # Generate date buttons with match counts
        await self._show_date_selection(query, context)

    async def _show_date_selection(
        self, query, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Show date selection with match counts."""
        await query.edit_message_text("⏳ Загружаю даты с матчами...")
        
        # Get matches for all leagues to count matches per date
        all_matches_by_date = {}
        leagues_to_check = [
            "premier_league", "la_liga", "bundesliga", "serie_a", "ligue_1",
            "champions_league", "europa_league",
            "eredivisie", "primeira_liga", "mls", "brasileirao",
            # World Cup Qualifications
            "wc_qual_europe", "wc_qual_concacaf", "wc_qual_south_america",
            "wc_qual_asia", "wc_qual_africa", "wc_qual_oceania", "wc_qual_playoffs",
        ]
        
        for league in leagues_to_check:
            matches_data = self.parser.get_fixtures_by_date(league, days=14)
            for date_display, matches in matches_data.items():
                if date_display not in all_matches_by_date:
                    all_matches_by_date[date_display] = 0
                all_matches_by_date[date_display] += len(matches)
        
        # Create a mapping from ISO date to match count
        date_counts = {}
        for date_display, count in all_matches_by_date.items():
            date_match = re.match(r"(\d{2}\.\d{2}\.\d{4})", date_display)
            if date_match:
                dmy = date_match.group(1)
                try:
                    dt = datetime.datetime.strptime(dmy, "%d.%m.%Y")
                    iso_date = dt.strftime("%Y-%m-%d")
                    date_counts[iso_date] = count
                except:
                    pass
        
        keyboard = []
        today = datetime.date.today()

        for i in range(14):
            target_date = today + datetime.timedelta(days=i)
            date_str = target_date.strftime("%Y-%m-%d")
            display_date = target_date.strftime("%d.%m (%A)")
            
            match_count = date_counts.get(date_str, 0)
            
            if i == 0:
                btn_text = f"Сегодня ({match_count})"
            elif i == 1:
                btn_text = f"Завтра ({match_count})"
            else:
                btn_text = f"{display_date.split(' ')[0]} ({match_count})"

            keyboard.append([
                InlineKeyboardButton(btn_text, callback_data=f"date_{i}_{date_str}")
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"📅 **Выберите дату** (всего {len(all_matches_by_date)} дней с матчами):",
            reply_markup=reply_markup
        )

    async def on_date_select(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle date selection."""
        query = update.callback_query
        await query.answer()

        data = query.data.split("_")
        day_offset = int(data[1])
        date_str = data[2]

        context.user_data["selected_date"] = date_str
        context.user_data["day_offset"] = day_offset

        # Get match counts per league for selected date
        leagues = {
            # Top European Leagues
            "premier_league": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League",
            "la_liga": "🇪🇸 La Liga",
            "bundesliga": "🇩🇪 Bundesliga",
            "serie_a": "🇮🇹 Serie A",
            "ligue_1": "🇫🇷 Ligue 1",

            # European Competitions
            "champions_league": "🏆 Champions League",
            "europa_league": "🏆 Europa League",
            "conference_league": "🏆 Conference League",

            # International Tournaments
            "world_cup": "🌍 World Cup",
            "euro": "🇪🇺 Euro Championship",
            "nations_league": "🏆 Nations League",

            # World Cup Qualifications 2026
            "wc_qual_europe": "🌍 Квалификация ЧМ (Европа)",
            "wc_qual_concacaf": "🌍 Квалификация ЧМ (CONCACAF)",
            "wc_qual_south_america": "🌍 Квалификация ЧМ (Юж. Америка)",
            "wc_qual_asia": "🌍 Квалификация ЧМ (Азия)",
            "wc_qual_africa": "🌍 Квалификация ЧМ (Африка)",
            "wc_qual_oceania": "🌍 Квалификация ЧМ (Океания)",
            "wc_qual_playoffs": "🌍 Квалификация ЧМ (Плей-офф)",

            # Other Top Leagues
            "eredivisie": "🇳🇱 Eredivisie",
            "primeira_liga": "🇵🇹 Primeira Liga",
            "mls": "🇺🇸 MLS",
            "brasileirao": "🇧🇷 Brasileirão",
            "liga_mx": "🇲🇽 Liga MX",

            # Domestic Cups
            "fa_cup": "🏆 FA Cup",
            "copa_del_rey": "🏆 Copa del Rey",
            "dfb_pokal": "🏆 DFB Pokal",
            "coppa_italia": "🏆 Coppa Italia",
        }

        keyboard = []
        for league_key, league_name in leagues.items():
            matches_data = self.parser.get_fixtures_by_date(league_key, days=30)
            match_count = 0
            for date_display, matches in matches_data.items():
                date_match = re.match(r"(\d{2}\.\d{2}\.\d{4})", date_display)
                if date_match:
                    dmy = date_match.group(1)
                    try:
                        dt = datetime.datetime.strptime(dmy, "%d.%m.%Y")
                        iso_date = dt.strftime("%Y-%m-%d")
                        if iso_date == date_str:
                            match_count = len(matches)
                            break
                    except:
                        pass
            
            btn_text = f"{league_name} ({match_count})" if match_count > 0 else f"{league_name} (0)"
            keyboard.append([
                InlineKeyboardButton(btn_text, callback_data=f"league_{league_key}")
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"📅 Дата: {date_str}\n\n🏆 **Выберите лигу** (в скобках количество матчей):",
            reply_markup=reply_markup
        )

    async def on_league_select(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle league selection."""
        query = update.callback_query
        await query.answer()

        league = query.data.replace("league_", "")
        context.user_data["selected_league"] = league

        await query.edit_message_text("⏳ Загружаю матчи...")

        matches_by_date = self.parser.get_fixtures_by_date(league, days=30)

        date_str = context.user_data.get("selected_date", "")
        target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        display_date = target_date.strftime("%d.%m.%Y (%A)")

        # Find matches for selected date
        day_matches = []
        for date_key, matches in matches_by_date.items():
            if date_str in date_key or display_date.split(" ")[0] in date_key:
                day_matches = matches
                break

        if not day_matches:
            all_matches = []
            for matches in matches_by_date.values():
                all_matches.extend(matches)
            day_matches = all_matches[:20]

        if not day_matches:
            await query.edit_message_text(
                f"😔 На {date_str} матчей не найдено в выбранной лиге.\n\n"
                "Попробуйте другую дату или лигу."
            )
            return

        keyboard = []
        for match in day_matches[:20]:
            button_text = f"{match.home_team} vs {match.away_team}"
            callback_data = f"match_{match.id}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

        reply_markup = InlineKeyboardMarkup(keyboard)

        league_name = context.user_data.get("selected_league", league)

        await query.edit_message_text(
            f"📅 Дата: {display_date}\n"
            f"🏆 Лига: {league_name}\n\n"
            f"⚽ **Выберите матч** ({len(day_matches)} найдено):",
            reply_markup=reply_markup
        )

    async def on_match_select(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle match selection and start analysis."""
        query = update.callback_query
        await query.answer()
        match_id = query.data.replace("match_", "")
        await self._analyze_match(query, match_id)

    async def cmd_help(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /help or Help button."""
        await update.message.reply_text(
            "ℹ️ **Помощь**\n\n"
            "📅 **Анализ матча** — выберите вид спорта, дату, лигу и матч для анализа\n\n"
            "🔹 **Как это работает:**\n"
            "1. Выберите вид спорта (пока только футбол)\n"
            "2. Выберите дату (показывается количество матчей)\n"
            "3. Выберите лигу (показывается количество матчей)\n"
            "4. Выберите матч\n"
            "5. Получите AI прогноз\n\n"
            "✅ **Проверить результаты** — проверить завершенные матчи и получить отчеты\n"
            "Бот отправит отчет, если вы запрашивали анализ и матч уже завершился\n\n"
            "🔹 **Источники данных:**\n"
            "• API-Football — расписание, форма команд, статистика, коэффициенты\n"
            "• Claude AI — анализ данных, поиск актуальных травм и новостей\n"
            "• Интернет — проверка травм, составов, мотивации (авторитетные источники)\n\n"
            "🎯 **Точность:** ~65-70%\n\n"
            "⚠️ Для полного анализа с рекомендациями нужен Anthropic API ключ"
        )

    async def cmd_check_results(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle Check Results button - show list of tracked matches."""
        logger.info(f"User {update.effective_user.id} requested results check")
        
        # Get the message object
        if update.message:
            target = update.message
        elif update.callback_query:
            target = update.callback_query.message
        else:
            return
        
        try:
            # Get all tracked matches
            tracked_match_ids = list(self.tracker.tracked_matches.keys())
            
            if not tracked_match_ids:
                await target.reply_text(
                    "📊 **Нет отслеживаемых матчей**\n\n"
                    "Вы ещё не запрашивали анализ матчей.\n\n"
                    "Как только вы запросите AI анализ любого матча, "
                    "бот будет отслеживать его результат и отправит отчет после завершения."
                )
                return
            
            # Build list of matches with status
            matches_info = []
            
            for match_id in tracked_match_ids:
                tracked = self.tracker.get_tracked_match(match_id)
                if not tracked:
                    continue
                
                # Get current match status from API
                params = {"id": match_id}
                data = self.parser._make_request("/fixtures", params)
                
                status = "❓"
                score = "-:-"
                finished = False
                
                if data and data.get("response"):
                    fixture = data["response"][0]
                    status = fixture.get("fixture", {}).get("status", {}).get("short", "?")
                    goals = fixture.get("goals", {})
                    home_score = goals.get("home", "-")
                    away_score = goals.get("away", "-")
                    score = f"{home_score}:{away_score}"
                    finished = status in ['FT', 'AET', 'PEN', 'ET']
                
                matches_info.append({
                    'match_id': match_id,
                    'home_team': tracked.home_team,
                    'away_team': tracked.away_team,
                    'tournament': tracked.tournament,
                    'status': status,
                    'score': score,
                    'finished': finished,
                    'report_sent': tracked.report_sent
                })
            
            # Create keyboard with matches
            keyboard = []
            
            # Add finished matches first
            finished_matches = [m for m in matches_info if m['finished']]
            pending_matches = [m for m in matches_info if not m['finished']]
            
            for match in finished_matches:
                emoji = "✅" if match['report_sent'] else "🆕"
                btn_text = f"{emoji} {match['home_team']} vs {match['away_team']} ({match['score']})"
                keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"check_match_{match['match_id']}")])
            
            if finished_matches and pending_matches:
                keyboard.append([InlineKeyboardButton("─" * 15, callback_data="separator")])
            
            for match in pending_matches:
                status_emoji = "⏳" if match['status'] == 'NS' else "🔴" if match['status'] in ['1H', '2H', 'HT'] else "❓"
                btn_text = f"{status_emoji} {match['home_team']} vs {match['away_team']} ({match['status']})"
                keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"check_match_{match['match_id']}")])
            
            # Add navigation buttons
            keyboard.append([InlineKeyboardButton("🔄 Обновить", callback_data="check_results")])
            keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="date_0")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Count stats
            finished_count = len(finished_matches)
            pending_count = len(pending_matches)
            sent_count = sum(1 for m in matches_info if m['report_sent'])
            
            summary = f"📊 **ОТСЛЕЖИВАЕМЫЕ МАТЧИ**\n\n"
            summary += f"📁 Всего: {len(matches_info)}\n"
            summary += f"✅ Завершено: {finished_count}\n"
            summary += f"⏳ В ожидании: {pending_count}\n"
            summary += f"📨 Отчетов отправлено: {sent_count}\n\n"
            summary += "Выберите матч для просмотра отчета:"
            
            await target.reply_text(summary, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error showing tracked matches: {e}", exc_info=True)
            await target.reply_text(
                "❌ Произошла ошибка при проверке результатов.\n"
                "Попробуйте позже."
            )

    async def cmd_check_results_inline(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle inline Check Results button."""
        query = update.callback_query
        await query.answer("🔍 Загружаю матчи...")
        
        # Call the main check results method
        await self.cmd_check_results(update, context)

    async def cmd_ignore_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Ignore separator/callbacks without action."""
        query = update.callback_query
        await query.answer()

    async def cmd_check_match_report(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle individual match selection from tracked matches list."""
        query = update.callback_query
        match_id = query.data.replace("check_match_", "")
        
        await query.answer("🔍 Проверяю матч...")
        
        try:
            # Get tracked match
            tracked = self.tracker.get_tracked_match(match_id)
            
            if not tracked:
                await query.message.reply_text(
                    "❌ Матч не найден в отслеживаемых."
                )
                return
            
            # Get current match status from API
            params = {"id": match_id}
            data = self.parser._make_request("/fixtures", params)
            
            if not data or not data.get("response"):
                await query.message.reply_text(
                    "❌ Не удалось получить данные о матче."
                )
                return
            
            fixture = data["response"][0]
            status = fixture.get("fixture", {}).get("status", {}).get("short", "")
            goals = fixture.get("goals", {})
            home_score = goals.get("home", "-")
            away_score = goals.get("away", "-")
            
            # Check if match is finished
            if status not in ['FT', 'AET', 'PEN', 'ET']:
                # Match not finished yet
                status_text = {
                    'NS': 'Не начался',
                    '1H': 'Первый тайм',
                    '2H': 'Второй тайм',
                    'HT': 'Перерыв',
                    'LIVE': 'Идет матч'
                }.get(status, status)
                
                await query.message.reply_text(
                    f"⏳ **МАТЧ ЕЩЁ НЕ ЗАВЕРШЕН**\n\n"
                    f"{tracked.home_team} vs {tracked.away_team}\n"
                    f"🏆 {tracked.tournament}\n\n"
                    f"Статус: {status_text}\n"
                    f"Счет: {home_score}:{away_score}\n\n"
                    f"Отчет будет отправлен после завершения матча."
                )
                return
            
            # Match is finished - check if report already sent
            if tracked.report_sent:
                await query.message.reply_text(
                    f"✅ **ОТЧЕТ УЖЕ ОТПРАВЛЕН**\n\n"
                    f"{tracked.home_team} {home_score}:{away_score} {tracked.away_team}\n\n"
                    f"Отчет был отправлен ранее."
                )
                return
            
            # Generate and send report
            actual_result = {
                'home_score': home_score,
                'away_score': away_score
            }
            
            report = self.reporter.generate_report(match_id, actual_result)
            
            if not report:
                await query.message.reply_text(
                    "❌ Не удалось сгенерировать отчет."
                )
                return
            
            # Send report
            await query.message.reply_text(report, parse_mode='Markdown')
            
            # Mark as sent
            self.tracker.mark_report_sent(match_id)
            
            logger.info(f"Sent post-match report to user {tracked.user_id} for match {match_id}")
            
        except Exception as e:
            logger.error(f"Error checking match report: {e}", exc_info=True)
            await query.message.reply_text(
                "❌ Произошла ошибка при проверке матча.\n"
                "Попробуйте позже."
            )

    async def _analyze_match(
        self, query, match_id: str
    ) -> None:
        """Analyze selected match using ONLY Claude AI."""
        logger.info(f"User {query.from_user.id} selected match {match_id}")

        analyzing_message = await query.message.reply_text(
            "🔍 Анализирую матч (AI Claude), подождите..."
        )

        try:
            match_details = self.parser.get_match_details(match_id)

            if not match_details or not match_details.match:
                logger.error(f"Failed to get match details for {match_id}")
                await analyzing_message.edit_text(
                    "❌ Не удалось получить данные о матче.\n"
                    "Возможно, матч ещё не начался или данные временно недоступны."
                )
                return

            match = match_details.match
            header = f"⚽ {match.home_team} vs {match.away_team}\n"
            header += f"🏆 {match.tournament}\n\n"

            # Check if Anthropic is available
            if not self.analyzer:
                await analyzing_message.edit_text(
                    header +
                    "❌ **AI анализ недоступен**\n\n"
                    "Требуется ANTHROPIC_API_KEY для анализа.\n"
                    "Пожалуйста, настройте API ключ в .env файле."
                )
                return

            # === ONLY CLAUDE AI ANALYSIS ===
            # Claude получает ВСЕ данные из API и сам делает анализ
            # Никаких предварительных расчетов вероятностей
            analysis = await self.analyzer.generate_analysis(match_details)

            # === TRACK MATCH FOR POST-MATCH REPORT ===
            # Extract predictions from AI analysis for post-match tracking
            predictions = self._extract_predictions_from_analysis(analysis)

            # Convert match timestamp to ISO date for tracking
            match_date_str = str(match.date) if match.date else ""

            # Track the match for post-match report
            self.tracker.track_match(
                match_id=match_id,
                user_id=query.from_user.id,
                home_team=match.home_team,
                away_team=match.away_team,
                tournament=match.tournament,
                match_date=match_date_str,
                predictions=predictions
            )
            logger.info(f"Match {match_id} tracked for post-match report for user {query.from_user.id}")

            # Add inline keyboard with "Check Results" button
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Проверить результаты", callback_data="check_results")],
                [InlineKeyboardButton("📅 Другой матч", callback_data="date_0")]
            ])

            await analyzing_message.edit_text(header + analysis, reply_markup=keyboard)
            logger.info(f"AI analysis sent for match {match_id}")

        except Exception as e:
            logger.error(f"Error analyzing match {match_id}: {e}", exc_info=True)
            await analyzing_message.edit_text(
                "❌ Произошла ошибка при анализе матча.\n"
                "Попробуйте позже или выберите другой матч."
            )

    def _extract_predictions_from_analysis(self, analysis: str) -> Dict:
        """
        Extract prediction probabilities from AI analysis text.
        Parses the analysis to get 1X2, over/under, BTTS probabilities.
        """
        predictions = {}
        
        # Extract 1X2 probabilities (e.g., "П1: 45% | X: 28% | П2: 27%")
        x2_match = re.search(r"П1:\s*(\d+)%\s*\|\s*X:\s*(\d+)%\s*\|\s*П2:\s*(\d+)%", analysis)
        if x2_match:
            predictions['home_win_pct'] = int(x2_match.group(1))
            predictions['draw_pct'] = int(x2_match.group(2))
            predictions['away_win_pct'] = int(x2_match.group(3))
        
        # Extract over/under 2.5 (e.g., "ТБ 2.5: 55%" or "Тотал > 2.5: 55%" or "ТБ 2.5 — 55%")
        over_match = re.search(r"(?:ТБ|Тотал\s*>\s*)\s*2\.5[:\s—-]\s*(\d+)%", analysis)
        under_match = re.search(r"(?:ТМ|Тотал\s*<\s*)\s*2\.5[:\s—-]\s*(\d+)%", analysis)
        if over_match:
            predictions['over_2_5_pct'] = int(over_match.group(1))
        if under_match:
            predictions['under_2_5_pct'] = int(under_match.group(1))
        
        # Extract BTTS (e.g., "Обе забьют: 60%" or "Обе забьют — 60%" or "ОЗ: 60%")
        # Also try to find from recommendations section
        btts_match = re.search(r"(?:Обе\s*забьют|ОЗ)[:\s—-]\s*(\d+)%", analysis)
        if btts_match:
            predictions['btts_yes_pct'] = int(btts_match.group(1))
            predictions['btts_no_pct'] = 100 - predictions['btts_yes_pct']
        
        # Extract likely scores (e.g., "• 1:1: 12%" or "1:1 — 12%")
        score_matches = re.findall(r"•\s*(\d+:\d+):\s*(\d+)%", analysis)
        if score_matches:
            predictions['likely_scores'] = [
                {"score": score, "prob": int(prob)} 
                for score, prob in score_matches[:5]
            ]
        
        # Fallback: Try to extract from stats section if available
        if 'btts_yes_pct' not in predictions:
            # Look for "ТБ 2.5 — XX%" pattern in recommendations
            tb_rec = re.search(r"ТБ\s*2\.5\s*—\s*(\d+)%", analysis)
            if tb_rec:
                predictions['over_2_5_pct'] = int(tb_rec.group(1))
                predictions['under_2_5_pct'] = 100 - predictions['over_2_5_pct']
        
        # Fallback defaults if parsing failed
        if not predictions:
            predictions = {
                'home_win_pct': 33,
                'draw_pct': 34,
                'away_win_pct': 33,
                'over_2_5_pct': 50,
                'under_2_5_pct': 50,
                'btts_yes_pct': 50,
                'btts_no_pct': 50,
                'likely_scores': []
            }
        
        logger.info(f"Extracted predictions from analysis: {predictions}")
        return predictions

    def _format_stats_analysis(self, stats: dict, match_details: MatchDetails) -> str:
        """Format Poisson statistics analysis."""
        match = match_details.match

        # Get team form summary
        home_form = match_details.home_team_form
        away_form = match_details.away_team_form

        home_form_str = "".join([m.get("result", "?") for m in home_form[:5]])
        away_form_str = "".join([m.get("result", "?") for m in away_form[:5]])

        # Check if market odds were blended
        blended = stats.get("blended", False)
        is_national = stats.get("is_national_teams", False)
        
        # Build header
        stats_text = f"📈 **СТАТИСТИЧЕСКИЙ ПРОГНОЗ{' + Рынок' if blended else ''} ({'Сборные' if is_national else 'Poisson-модель'})**\n\n"
        
        # Show market odds if available
        if stats.get("market_home_odd"):
            stats_text += (
                f"💰 **Коэффициенты букмекеров:**\n"
                f"П1: {stats['market_home_odd']:.2f} | X: {stats['market_draw_odd']:.2f} | П2: {stats['market_away_odd']:.2f}\n\n"
            )
        
        stats_text += (
            f"📊 **Форма команд (последние 5 матчей):**\n"
            f"🏠 {match.home_team}: {home_form_str}\n"
            f"✈️ {match.away_team}: {away_form_str}\n\n"
            f"🎯 **ОСНОВНЫЕ ВЕРОЯТНОСТИ**\n"
            f"П1: {stats['home_win_pct']}% | X: {stats['draw_pct']}% | П2: {stats['away_win_pct']}%\n\n"
        )
        
        # Add note about blending for national teams
        if blended and is_national:
            stats_text += (
                f"ℹ️ _Вероятности скорректированы по рыночным коэффициентам (40% модель + 60% рынок)_\n\n"
            )
        
        stats_text += (
            f"⚽ **ГОЛЫ**\n"
            f"Ожидаемый тотал: {stats['expected_total_goals']}\n"
            f"Тотал > 2.5: {stats['over_2_5_pct']}%\n"
            f"Тотал < 2.5: {stats['under_2_5_pct']}%\n"
            f"Обе забьют (Да): {stats['btts_yes_pct']}%\n\n"
            f"🟨 **КАРТОЧКИ**\n"
            f"ТЖК > 4.5: {stats['cards_over_4_5_pct']}%\n\n"
            f"📐 **УГЛОВЫЕ**\n"
            f"Угловые > 9.5: {stats['corners_over_9_5_pct']}%\n\n"
            f"🎲 **НАИБОЛЕЕ ВЕРОЯТНЫЕ СЧЕТА**\n"
            + "\n".join([f"• {s['score']}: {s['prob']}%" for s in stats['likely_scores']]) + "\n\n"
            f"ℹ️ _Данные предоставлены API-Football. Для анализа с рекомендациями добавьте Anthropic API ключ._"
        )

        return stats_text

    async def run(self) -> None:
        """Start the bot."""
        logger.info("Starting bot...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        logger.info("Bot is running (manual results check enabled)")

        # Note: Automatic periodic check disabled to save API requests
        # Users can manually check results with the "✅ Проверить результаты" button
        # asyncio.create_task(self._periodic_results_check())

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping bot...")
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()


async def main() -> None:
    """Main entry point."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        return

    bot = FootballBot(token)
    await bot.run()


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    asyncio.run(main())
