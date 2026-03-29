#!/usr/bin/env python3
"""Test API-Football connection"""
import requests

API_KEY = "08c6e6aeaf97abc445440c686ac50fab"
BASE_URL = "https://v3.football.api-sports.io"

headers = {"x-apisports-key": API_KEY}

# Test 1: Check leagues endpoint
print("=== Test 1: Leagues endpoint ===")
resp = requests.get(f"{BASE_URL}/leagues?id=39", headers=headers)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.json()}\n")

# Test 2: Get fixtures for Premier League
print("=== Test 2: Fixtures for Premier League ===")
import datetime
today = datetime.datetime.now().strftime("%Y-%m-%d")
future = (datetime.datetime.now() + datetime.timedelta(days=14)).strftime("%Y-%m-%d")

params = {
    "league": 39,
    "season": 2025,
    "from": today,
    "to": future
}
resp = requests.get(f"{BASE_URL}/fixtures", headers=headers, params=params)
print(f"Status: {resp.status_code}")
data = resp.json()
print(f"Results: {data.get('results', 0)}")
print(f"Response: {data}\n")

# Test 3: Get current season fixtures
print("=== Test 3: Current season (no date filter) ===")
params = {"league": 39, "season": 2025, "round": "Regular Season - 30"}
resp = requests.get(f"{BASE_URL}/fixtures", headers=headers, params=params)
print(f"Status: {resp.status_code}")
data = resp.json()
print(f"Results: {data.get('results', 0)}")
if data.get('response'):
    print(f"First match: {data['response'][0]}")
