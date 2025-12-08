"""
Test CSV parsing to see what data we have

Run this first to understand the CSV structure before importing
"""

import csv
from collections import defaultdict

CSV_FILE = "tests/TestImportData/First TD - 2025 (4).csv"


def analyze_csv():
    """Analyze the CSV file structure"""
    print("Analyzing CSV file...")
    print("=" * 80)

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"\nTotal rows: {len(rows)}")
    print(f"\nColumn headers: {list(rows[0].keys())}")

    # Analyze data
    users = set()
    teams = set()
    players = set()
    weeks = set()
    results = defaultdict(int)

    valid_rows = 0

    for row in rows:
        if not row.get("Week") or not row.get("Picker"):
            continue

        valid_rows += 1

        if row.get("Picker"):
            users.add(row["Picker"])
        if row.get("Home"):
            teams.add(row["Home"])
        if row.get("Vistor"):  # Note: typo in CSV
            teams.add(row["Vistor"])
        if row.get("Player"):
            players.add(row["Player"])
        if row.get("Week"):
            try:
                weeks.add(int(row["Week"]))
            except:
                pass
        if row.get("Result"):
            results[row["Result"]] += 1

    print(f"\nValid data rows: {valid_rows}")
    print(f"\nUnique users ({len(users)}):")
    for user in sorted(users):
        print(f"  - {user}")

    print(f"\nUnique teams ({len(teams)}):")
    for team in sorted(teams):
        print(f"  - {team}")

    print(f"\nWeeks covered: {sorted(weeks)}")

    print(f"\nResults distribution:")
    for result, count in sorted(results.items()):
        print(f"  {result}: {count}")

    print(f"\nUnique players: {len(players)}")

    # Show first few valid rows
    print("\n" + "=" * 80)
    print("Sample rows:")
    print("=" * 80)

    count = 0
    for row in rows:
        if not row.get("Week") or not row.get("Picker"):
            continue

        print(f"\nWeek {row['Week']} - {row['Gameday']}")
        print(f"  Picker: {row['Picker']}")
        print(f"  Game: {row['Vistor']} @ {row['Home']}")
        print(f"  Pick: {row['Player']} ({row.get('Position', 'N/A')})")
        print(f"  Result: {row.get('Result', 'Pending')}")
        if row.get("Actual Result"):
            print(f"  Actual FTD: {row['Actual Result']}")

        count += 1
        if count >= 5:
            break

    print("\n" + "=" * 80)


if __name__ == "__main__":
    analyze_csv()
