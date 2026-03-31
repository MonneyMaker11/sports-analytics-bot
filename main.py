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
from typing import Optional

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
from ai_analyzer import AIAnalyzer, PoissonCalculator

logger = logging.getLogger(__name__)

load_dotenv()

# Conversation states
SELECT_SPORT, SELECT_DATE, SELECT_LEAGUE, SELECT_MATCH = range(4)

# Persistent keyboard for easy access
MAIN_KEYBOARD = ReplyKeyboardMarkup([
    [KeyboardButton("📅 Анализ матча")],
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
        self.default_league = default_league

        self.application = Application.builder().token(token).build()
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up command and callback handlers."""
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        
        # Handle keyboard button text as messages
        self.application.add_handler(MessageHandler(
            filters.Regex("^📅 Анализ матча$"),
            self.cmd_start_analysis
        ))
        self.application.add_handler(MessageHandler(
            filters.Regex("^ℹ️ Помощь$"),
            self.cmd_help
        ))
        
        # Conversation handlers
        self.application.add_handler(CallbackQueryHandler(self.on_sport_select, pattern=r"^sport_"))
        self.application.add_handler(CallbackQueryHandler(self.on_date_select, pattern=r"^date_"))
        self.application.add_handler(CallbackQueryHandler(self.on_league_select, pattern=r"^league_"))
        self.application.add_handler(CallbackQueryHandler(self.on_match_select, pattern=r"^match_"))

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
            "🔹 Бот использует API-Football для данных и Poisson-модель для расчётов.",
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
            "5. Получите статистический прогноз\n\n"
            "🔹 **Источники данных:**\n"
            "• API-Football — расписание, форма команд, статистика\n"
            "• Poisson-модель — математический расчёт вероятностей\n"
            "• GPT-4o-mini (опционально) — анализ и рекомендации\n\n"
            "🎯 **Точность:** ~60-65%\n\n"
            "⚠️ Для полного анализа с рекомендациями нужен OpenAI API ключ"
        )

    async def _analyze_match(
        self, query, match_id: str
    ) -> None:
        """Analyze selected match using API-Football data + Poisson + optional GPT."""
        logger.info(f"User {query.from_user.id} selected match {match_id}")

        analyzing_message = await query.message.reply_text(
            "🔍 Анализирую матч (статистика + Poisson), подождите..."
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

            # Generate Poisson-based analysis
            calc = PoissonCalculator()
            stats = calc.calculate_probabilities(match_details)
            
            match = match_details.match
            header = f"⚽ {match.home_team} vs {match.away_team}\n"
            header += f"🏆 {match.tournament}\n\n"
            
            # Check if Anthropic is available
            anthropic_available = (
                os.getenv("ANTHROPIC_API_KEY") and 
                os.getenv("ANTHROPIC_API_KEY") != "your_anthropic_api_key_here"
            ) and self.analyzer is not None
            
            if not anthropic_available:
                # Free analysis with full team form from API-Football
                stats_text = self._format_stats_analysis(stats, match_details)
                await analyzing_message.edit_text(header + stats_text)
                return

            # GPT analysis with full API-Football data
            analysis = await self.analyzer.generate_analysis(match_details)
            await analyzing_message.edit_text(header + analysis)
            logger.info(f"Analysis sent for match {match_id}")

        except Exception as e:
            logger.error(f"Error analyzing match {match_id}: {e}", exc_info=True)
            await analyzing_message.edit_text(
                "❌ Произошла ошибка при анализе матча.\n"
                "Попробуйте позже или выберите другой матч."
            )

    def _format_stats_analysis(self, stats: dict, match_details: MatchDetails) -> str:
        """Format Poisson statistics analysis."""
        match = match_details.match
        
        # Get team form summary
        home_form = match_details.home_team_form
        away_form = match_details.away_team_form
        
        home_form_str = "".join([m.get("result", "?") for m in home_form[:5]])
        away_form_str = "".join([m.get("result", "?") for m in away_form[:5]])
        
        stats_text = (
            f"📈 **СТАТИСТИЧЕСКИЙ ПРОГНОЗ (Poisson-модель)**\n\n"
            f"📊 **Форма команд (последние 5 матчей):**\n"
            f"🏠 {match.home_team}: {home_form_str}\n"
            f"✈️ {match.away_team}: {away_form_str}\n\n"
            f"🎯 **ОСНОВНЫЕ ВЕРОЯТНОСТИ**\n"
            f"П1: {stats['home_win_pct']}% | X: {stats['draw_pct']}% | П2: {stats['away_win_pct']}%\n\n"
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
            f"ℹ️ _Данные предоставлены API-Football. Для анализа с рекомендациями добавьте OpenAI API ключ._"
        )
        
        return stats_text

    async def run(self) -> None:
        """Start the bot."""
        logger.info("Starting bot...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        logger.info("Bot is running")

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
