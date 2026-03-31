# 🏆 Sports Analytics Bot v1.1.0

Telegram bot for football match analysis with AI-powered predictions.

## ✨ What's New in v1.1.0

### World Cup 2026 Qualification Support

Added **7 new qualification leagues** for FIFA World Cup 2026:

| League | ID | Season | Matches Today (31.03.2026) |
|--------|----|--------|---------------------------|
| 🌍 Europe | 32 | 2024 | 4 matches |
| 🌍 CONCACAF | 31 | 2026 | 0 matches |
| 🌍 South America | 34 | 2026 | 0 matches |
| 🌍 Asia | 30 | 2026 | 0 matches |
| 🌍 Africa | 29 | 2023 | 0 matches |
| 🌍 Oceania | 33 | 2026 | 0 matches |
| 🌍 Playoffs | 37 | 2026 | 0 matches |

### Today's Featured Matches (31.03.2026)

**WC Qualification Europe:**
- 🇸🇪 Sweden vs Poland 🇵🇱 (18:45)
- 🇨🇿 Czech Republic vs Denmark 🇩🇰 (18:45)
- 🇽🇰 Kosovo vs Türkiye 🇹🇷 (18:45)
- 🇧🇦 Bosnia & Herzegovina vs Italy 🇮🇹 (18:45)

## 🚀 Quick Start

### Run with script
```bash
./run_bot.sh
```

### Manual start
```bash
cd /Users/ilyailyx/Desktop/sports-analytics-bot
source venv/bin/activate
python main.py
```

## 📱 How to Use in Telegram

1. Open bot in Telegram
2. Click "📅 Анализ матча"
3. Select "⚽ Футбол"
4. Select "Сегодня (4)" ← WC Qualification matches!
5. Select "🌍 Квалификация ЧМ (Европа) (4)"
6. Choose a match
7. Get AI-powered analysis!

## 📊 Features

- **Poisson Model**: Statistical predictions based on team form, xG, H2H
- **AI Analysis**: Optional Claude AI analysis for detailed insights
- **20+ Leagues**: Premier League, La Liga, Champions League, WC Qualification, etc.
- **Live Data**: Real-time data from API-Football
- **Smart Cache**: 24h cache for optimal API usage

## 🛠 Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run bot
python main.py
```

## 📁 Project Structure

```
sports-analytics-bot/
├── main.py                 # Telegram bot core
├── api_football_parser.py  # API-Football data parser
├── flashscore_parser.py    # Flashscore fallback parser
├── ai_analyzer.py          # AI analysis engine
├── requirements.txt        # Python dependencies
├── run_bot.sh             # Quick start script
└── README.md              # This file
```

## 📈 Version History

### v1.1.0 (2026-03-31)
- ✅ Added 7 WC Qualification 2026 leagues
- ✅ Fixed season handling for qualifications
- ✅ Updated team form for national teams
- ✅ Added qualifications to date/league selection

### v1.0.0 (Previous)
- Core bot functionality
- Premier League, La Liga, Bundesliga, Serie A, Ligue 1
- Champions League, Europa League
- AI-powered analysis with Claude

## 📝 Documentation

- [WC Qualification Instruction](WC_QUALIFICATION_INSTRUCTION.md)
- [Release Notes](RELEASE_NOTES.md)
- [Comparison of formats](COMPARISON.md)
- [Enhanced Prompt](ENHANCED_PROMPT.md)

## 🤝 Support

For issues or questions:
1. Check logs
2. Run `python verify_wc_qualification.py`
3. Ensure API keys are valid

## 📄 License

MIT License

---

**Bot Version:** v1.1.0  
**Last Updated:** 2026-03-31  
**Status:** ✅ Production Ready
