# 🚀 Quick Start - Ideal Probability System

## Test the System

```bash
cd /Users/ilyailyx/Desktop/sports-analytics-bot
source venv/bin/activate

# Test on Bosnia vs Italy
python test_ideal_calculator.py

# Test probability fix
python test_bosnia_italy_fix.py
```

## Run the Bot

```bash
# Option 1: Use script
./run_bot.sh

# Option 2: Manual
python main.py
```

## What Changed

### Before:
```
📊 СТАТИСТИЧЕСКИЙ ПРОГНОЗ (Poisson-модель)
🎯 ОСНОВНЫЕ ВЕРОЯТНОСТИ
П1: 52% | X: 22% | П2: 26%  ❌ WRONG!
```

### After:
```
📊 IDEAL ANALYSIS (Market + Form + Model)
💰 КОЭФФИЦИЕНТЫ БУКМЕКЕРОВ (3 БК):
   П1: 7.50 | X: 4.25 | П2: 1.52

🎯 ВЕРОЯТНОСТИ (Confidence: HIGH)
   П1: 17% | X: 22% | П2: 61%  ✅ CORRECT!
```

## System Architecture

```
┌──────────────────────────────────────┐
│     IDEAL PROBABILITY CALCULATOR     │
├──────────────────────────────────────┤
│ 1. Market Odds (75%) ← Most accurate │
│ 2. Team Form (20%) ← Recent results  │
│ 3. Statistical Model (5%) ← Poisson  │
└──────────────────────────────────────┘
```

## Key Files

| File | Purpose |
|------|---------|
| `ideal_probability_calculator.py` | Core calculator |
| `main.py` | Bot with integrated calculator |
| `test_ideal_calculator.py` | Test suite |
| `IDEAL_SYSTEM_DOCUMENTATION.md` | Full documentation |

## Validation

All probabilities are validated:
- ✅ Underdog: 8-25% (realistic)
- ✅ Favorite: 50-75% (realistic)
- ✅ Draw: 15-30% (realistic)
- ✅ Sum: Exactly 100%

## API Keys Required

In `.env`:
```
API_FOOTBALL_KEY=your_key_here
TELEGRAM_BOT_TOKEN=your_bot_token
ANTHROPIC_API_KEY=optional_for_ai_commentary
```

## Support

If probabilities look wrong:
1. Check if market odds are available
2. Verify team form data exists
3. Run `python test_ideal_calculator.py`
4. Check logs for warnings

---

**Status:** ✅ Production Ready
**Version:** 1.0.0 (Ideal System)
**Last Updated:** 2026-03-31
