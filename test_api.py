#!/usr/bin/env python3
"""Test script for Football-Data.org API"""
import os
import sys
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('FOOTBALL_DATA_API_KEY')
print(f'API Key: {api_key}')
print(f'Today: {datetime.now().date()}')
print()

headers = {'X-Auth-Token': api_key}

# Test each league
leagues = {
    'PL': 'Premier League',
    'PD': 'La Liga',
    'BL1': 'Bundesliga',
    'SA': 'Serie A',
    'FL1': 'Ligue 1',
    'CL': 'Champions League',
}

for comp_id, comp_name in leagues.items():
    print(f'\n=== {comp_name} ({comp_id}) ===')
    
    # Get current season
    resp = requests.get(f'https://api.football-data.org/v4/competitions/{comp_id}', headers=headers)
    print(f'Season API status: {resp.status_code}')
    
    if resp.status_code == 429:
        print('RATE LIMIT EXCEEDED!')
        continue
    
    if resp.status_code != 200:
        print(f'Error: {resp.text[:200]}')
        continue
    
    data = resp.json()
    season = data.get('currentSeason', {})
    print(f'Current season: {season.get("startDate")} to {season.get("endDate")}')
    
    year = season.get('startDate', '2025')[:4]
    
    # Get matches for next 7 days
    today = datetime.now().date()
    end_date = today + timedelta(days=7)
    
    resp2 = requests.get(
        f'https://api.football-data.org/v4/competitions/{comp_id}/matches?season={year}',
        headers=headers
    )
    print(f'Matches API status: {resp2.status_code}')
    
    if resp2.status_code == 200:
        matches_data = resp2.json()
        all_matches = matches_data.get('matches', [])
        print(f'Total matches in season: {len(all_matches)}')
        
        # Filter by date range
        upcoming = []
        for m in all_matches:
            match_date_str = m.get('utcDate', '')
            if match_date_str:
                try:
                    match_date = datetime.fromisoformat(match_date_str.replace('Z', '+00:00')).date()
                    if today <= match_date <= end_date:
                        upcoming.append((match_date_str[:10], m))
                except:
                    pass
        
        print(f'Upcoming matches (7 days): {len(upcoming)}')
        for date_str, m in upcoming[:5]:
            home = m.get('homeTeam', {}).get('name', '?')
            away = m.get('awayTeam', {}).get('name', '?')
            print(f'  {date_str}: {home} vs {away}')
