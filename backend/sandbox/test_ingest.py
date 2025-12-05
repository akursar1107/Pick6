"""
Sample experimental script for sandbox usage.
Demonstrates basic usage of nflreadpy to fetch NFL game data.
"""

try:
    from nflreadpy import games
except ImportError:
    print("nflreadpy not installed. Run: pip install nflreadpy")
    exit(1)

# Fetch NFL games for 2023 season
try:
    df = games(season=2023)
    print(df.head())
except Exception as e:
    print(f"Error fetching games: {e}")
