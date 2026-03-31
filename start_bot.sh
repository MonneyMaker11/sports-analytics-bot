#!/bin/bash
# Start bot in background

cd /Users/ilyailyx/Desktop/sports-analytics-bot
source venv/bin/activate

# Clear cache first
python -c "from api_football_parser import APIFootballParser; p = APIFootballParser('08c6e6aeaf97abc445440c686ac50fab'); p._season_cache.clear()"

# Start bot
echo "Starting bot..."
python main.py &
echo "Bot started with PID $!"
