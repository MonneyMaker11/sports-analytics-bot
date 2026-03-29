#!/usr/bin/env python3
"""Test paid API-Football key"""
import requests

API_KEY = "3c3dbadbdd333a1ca1ecd2ef59779054"
BASE_URL = "https://v3.football.api-sports.io"

headers = {"x-apisports-key": API_KEY}

print("=== Test 1: Check leagues endpoint ===")
resp = requests.get(f"{BASE_URL}/leagues?id=39", headers=headers)
print(f"Status: {resp.status_code}")
data = resp.json()
print(f"Response: {data.get('response', [])[:1] if data.get('response') else 'None'}\n")

print("=== Test 2: Get current season fixtures (no date filter) ===")
params = {"league": 39, "season": 2025, "round": "Regular Season - 30"}
resp = requests.get(f"{BASE_URL}/fixtures", headers=headers, params=params)
print(f"Status: {resp.status_code}")
print(f"Errors: {resp.json().get('errors', 'None')}")
print(f"Results: {resp.json().get('results', 0)}")
if resp.json().get('response'):
    print(f"First match: {resp.json()['response'][0]['teams']}")

print("\n=== Test 3: Get fixtures by date range ===")
params = {"league": 39, "season": 2025, "from": "2026-03-29", "to": "2026-04-12"}
resp = requests.get(f"{BASE_URL}/fixtures", headers=headers, params=params)
print(f"Status: {resp.status_code}")
print(f"Errors: {resp.json().get('errors', 'None')}")
print(f"Results: {resp.json().get('results', 0)}")
if resp.json().get('response'):
    print(f"First match: {resp.json()['response'][0]}")

print("\n=== Test 4: Check what seasons are available ===")
resp = requests.get(f"{BASE_URL}/leagues?id=39", headers=headers)
data = resp.json()
if data.get('response'):
    seasons = data['response'][0].get('seasons', [])
    print(f"Available seasons: {[s['year'] for s in seasons[-5:]]}")
    for s in seasons:
        if s.get('current'):
            print(f"Current season: {s['year']} ({s['start']} to {s['end']})")
