#!/bin/bash
# Запуск бота с проверкой квалификации ЧМ

echo "============================================================"
echo "🚀 Sports Analytics Bot v1.1.0"
echo "   World Cup 2026 Qualification Support"
echo "============================================================"
echo ""

# Activate virtual environment
echo "📦 Активация виртуального окружения..."
source venv/bin/activate

# Clear cache
echo "🗑️  Очистка кэша..."
python -c "from api_football_parser import APIFootballParser; p = APIFootballParser('08c6e6aeaf97abc445440c686ac50fab'); p._season_cache.clear(); print('   Кэш очищен')"

# Check WC qualification matches
echo ""
echo "🔍 Проверка квалификации ЧМ..."
python verify_wc_qualification.py

# Start bot
echo ""
echo "🤙 Запуск бота..."
echo "   Нажмите Ctrl+C для остановки"
echo "============================================================"
python main.py
