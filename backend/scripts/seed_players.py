"""Seed sample NFL players for each team"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from app.db.models.team import Team
from app.db.models.player import Player

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@db:5432/first6"

# Sample players for each team (QB, RB, WR, TE per team)
# Using realistic player names and positions
SAMPLE_PLAYERS = {
    "BUF": [
        {
            "external_id": "allen_josh",
            "name": "Josh Allen",
            "position": "QB",
            "jersey_number": 17,
        },
        {
            "external_id": "cook_james_buf",
            "name": "James Cook",
            "position": "RB",
            "jersey_number": 4,
        },
        {
            "external_id": "diggs_stefon",
            "name": "Stefon Diggs",
            "position": "WR",
            "jersey_number": 14,
        },
        {
            "external_id": "kincaid_dalton",
            "name": "Dalton Kincaid",
            "position": "TE",
            "jersey_number": 86,
        },
    ],
    "MIA": [
        {
            "external_id": "tagovailoa_tua",
            "name": "Tua Tagovailoa",
            "position": "QB",
            "jersey_number": 1,
        },
        {
            "external_id": "mostert_raheem",
            "name": "Raheem Mostert",
            "position": "RB",
            "jersey_number": 31,
        },
        {
            "external_id": "hill_tyreek",
            "name": "Tyreek Hill",
            "position": "WR",
            "jersey_number": 10,
        },
        {
            "external_id": "waddle_jaylen",
            "name": "Jaylen Waddle",
            "position": "WR",
            "jersey_number": 17,
        },
    ],
    "NE": [
        {
            "external_id": "jones_mac",
            "name": "Mac Jones",
            "position": "QB",
            "jersey_number": 10,
        },
        {
            "external_id": "stevenson_rhamondre",
            "name": "Rhamondre Stevenson",
            "position": "RB",
            "jersey_number": 38,
        },
        {
            "external_id": "bourne_kendrick",
            "name": "Kendrick Bourne",
            "position": "WR",
            "jersey_number": 84,
        },
        {
            "external_id": "henry_hunter",
            "name": "Hunter Henry",
            "position": "TE",
            "jersey_number": 85,
        },
    ],
    "NYJ": [
        {
            "external_id": "rodgers_aaron",
            "name": "Aaron Rodgers",
            "position": "QB",
            "jersey_number": 8,
        },
        {
            "external_id": "hall_breece",
            "name": "Breece Hall",
            "position": "RB",
            "jersey_number": 20,
        },
        {
            "external_id": "wilson_garrett",
            "name": "Garrett Wilson",
            "position": "WR",
            "jersey_number": 5,
        },
        {
            "external_id": "conklin_tyler",
            "name": "Tyler Conklin",
            "position": "TE",
            "jersey_number": 83,
        },
    ],
    "BAL": [
        {
            "external_id": "jackson_lamar",
            "name": "Lamar Jackson",
            "position": "QB",
            "jersey_number": 8,
        },
        {
            "external_id": "henry_derrick",
            "name": "Derrick Henry",
            "position": "RB",
            "jersey_number": 22,
        },
        {
            "external_id": "flowers_zay",
            "name": "Zay Flowers",
            "position": "WR",
            "jersey_number": 4,
        },
        {
            "external_id": "andrews_mark",
            "name": "Mark Andrews",
            "position": "TE",
            "jersey_number": 89,
        },
    ],
    "CIN": [
        {
            "external_id": "burrow_joe",
            "name": "Joe Burrow",
            "position": "QB",
            "jersey_number": 9,
        },
        {
            "external_id": "mixon_joe",
            "name": "Joe Mixon",
            "position": "RB",
            "jersey_number": 28,
        },
        {
            "external_id": "chase_jamarr",
            "name": "Ja'Marr Chase",
            "position": "WR",
            "jersey_number": 1,
        },
        {
            "external_id": "higgins_tee",
            "name": "Tee Higgins",
            "position": "WR",
            "jersey_number": 85,
        },
    ],
    "CLE": [
        {
            "external_id": "watson_deshaun",
            "name": "Deshaun Watson",
            "position": "QB",
            "jersey_number": 4,
        },
        {
            "external_id": "chubb_nick",
            "name": "Nick Chubb",
            "position": "RB",
            "jersey_number": 24,
        },
        {
            "external_id": "cooper_amari",
            "name": "Amari Cooper",
            "position": "WR",
            "jersey_number": 2,
        },
        {
            "external_id": "njoku_david",
            "name": "David Njoku",
            "position": "TE",
            "jersey_number": 85,
        },
    ],
    "PIT": [
        {
            "external_id": "pickett_kenny",
            "name": "Kenny Pickett",
            "position": "QB",
            "jersey_number": 8,
        },
        {
            "external_id": "harris_najee",
            "name": "Najee Harris",
            "position": "RB",
            "jersey_number": 22,
        },
        {
            "external_id": "pickens_george",
            "name": "George Pickens",
            "position": "WR",
            "jersey_number": 14,
        },
        {
            "external_id": "freiermuth_pat",
            "name": "Pat Freiermuth",
            "position": "TE",
            "jersey_number": 88,
        },
    ],
    "HOU": [
        {
            "external_id": "stroud_cj",
            "name": "C.J. Stroud",
            "position": "QB",
            "jersey_number": 7,
        },
        {
            "external_id": "mixon_joe_hou",
            "name": "Joe Mixon",
            "position": "RB",
            "jersey_number": 28,
        },
        {
            "external_id": "collins_nico",
            "name": "Nico Collins",
            "position": "WR",
            "jersey_number": 12,
        },
        {
            "external_id": "schultz_dalton",
            "name": "Dalton Schultz",
            "position": "TE",
            "jersey_number": 86,
        },
    ],
    "IND": [
        {
            "external_id": "richardson_anthony",
            "name": "Anthony Richardson",
            "position": "QB",
            "jersey_number": 5,
        },
        {
            "external_id": "taylor_jonathan",
            "name": "Jonathan Taylor",
            "position": "RB",
            "jersey_number": 28,
        },
        {
            "external_id": "pittman_michael",
            "name": "Michael Pittman Jr.",
            "position": "WR",
            "jersey_number": 11,
        },
        {
            "external_id": "granson_kylen",
            "name": "Kylen Granson",
            "position": "TE",
            "jersey_number": 83,
        },
    ],
    "JAX": [
        {
            "external_id": "lawrence_trevor",
            "name": "Trevor Lawrence",
            "position": "QB",
            "jersey_number": 16,
        },
        {
            "external_id": "etienne_travis",
            "name": "Travis Etienne",
            "position": "RB",
            "jersey_number": 1,
        },
        {
            "external_id": "kirk_christian",
            "name": "Christian Kirk",
            "position": "WR",
            "jersey_number": 13,
        },
        {
            "external_id": "engram_evan",
            "name": "Evan Engram",
            "position": "TE",
            "jersey_number": 17,
        },
    ],
    "TEN": [
        {
            "external_id": "levis_will",
            "name": "Will Levis",
            "position": "QB",
            "jersey_number": 8,
        },
        {
            "external_id": "henry_derrick_ten",
            "name": "Derrick Henry",
            "position": "RB",
            "jersey_number": 22,
        },
        {
            "external_id": "hopkins_deandre",
            "name": "DeAndre Hopkins",
            "position": "WR",
            "jersey_number": 10,
        },
        {
            "external_id": "okonkwo_chig",
            "name": "Chig Okonkwo",
            "position": "TE",
            "jersey_number": 85,
        },
    ],
    "DEN": [
        {
            "external_id": "wilson_russell",
            "name": "Russell Wilson",
            "position": "QB",
            "jersey_number": 3,
        },
        {
            "external_id": "williams_javonte",
            "name": "Javonte Williams",
            "position": "RB",
            "jersey_number": 33,
        },
        {
            "external_id": "jeudy_jerry",
            "name": "Jerry Jeudy",
            "position": "WR",
            "jersey_number": 10,
        },
        {
            "external_id": "trautman_adam",
            "name": "Adam Trautman",
            "position": "TE",
            "jersey_number": 82,
        },
    ],
    "KC": [
        {
            "external_id": "mahomes_patrick",
            "name": "Patrick Mahomes",
            "position": "QB",
            "jersey_number": 15,
        },
        {
            "external_id": "pacheco_isiah",
            "name": "Isiah Pacheco",
            "position": "RB",
            "jersey_number": 10,
        },
        {
            "external_id": "rice_rashee",
            "name": "Rashee Rice",
            "position": "WR",
            "jersey_number": 4,
        },
        {
            "external_id": "kelce_travis",
            "name": "Travis Kelce",
            "position": "TE",
            "jersey_number": 87,
        },
    ],
    "LV": [
        {
            "external_id": "oconnell_aidan",
            "name": "Aidan O'Connell",
            "position": "QB",
            "jersey_number": 12,
        },
        {
            "external_id": "jacobs_josh",
            "name": "Josh Jacobs",
            "position": "RB",
            "jersey_number": 8,
        },
        {
            "external_id": "adams_davante",
            "name": "Davante Adams",
            "position": "WR",
            "jersey_number": 17,
        },
        {
            "external_id": "mayer_michael",
            "name": "Michael Mayer",
            "position": "TE",
            "jersey_number": 87,
        },
    ],
    "LAC": [
        {
            "external_id": "herbert_justin",
            "name": "Justin Herbert",
            "position": "QB",
            "jersey_number": 10,
        },
        {
            "external_id": "ekeler_austin",
            "name": "Austin Ekeler",
            "position": "RB",
            "jersey_number": 30,
        },
        {
            "external_id": "allen_keenan",
            "name": "Keenan Allen",
            "position": "WR",
            "jersey_number": 13,
        },
        {
            "external_id": "parham_donald",
            "name": "Donald Parham",
            "position": "TE",
            "jersey_number": 89,
        },
    ],
    "DAL": [
        {
            "external_id": "prescott_dak",
            "name": "Dak Prescott",
            "position": "QB",
            "jersey_number": 4,
        },
        {
            "external_id": "pollard_tony",
            "name": "Tony Pollard",
            "position": "RB",
            "jersey_number": 20,
        },
        {
            "external_id": "lamb_ceedee",
            "name": "CeeDee Lamb",
            "position": "WR",
            "jersey_number": 88,
        },
        {
            "external_id": "ferguson_jake",
            "name": "Jake Ferguson",
            "position": "TE",
            "jersey_number": 87,
        },
    ],
    "NYG": [
        {
            "external_id": "jones_daniel",
            "name": "Daniel Jones",
            "position": "QB",
            "jersey_number": 8,
        },
        {
            "external_id": "barkley_saquon",
            "name": "Saquon Barkley",
            "position": "RB",
            "jersey_number": 26,
        },
        {
            "external_id": "nabers_malik",
            "name": "Malik Nabers",
            "position": "WR",
            "jersey_number": 1,
        },
        {
            "external_id": "waller_darren",
            "name": "Darren Waller",
            "position": "TE",
            "jersey_number": 12,
        },
    ],
    "PHI": [
        {
            "external_id": "hurts_jalen",
            "name": "Jalen Hurts",
            "position": "QB",
            "jersey_number": 1,
        },
        {
            "external_id": "swift_dangelo",
            "name": "D'Angelo Swift",
            "position": "RB",
            "jersey_number": 0,
        },
        {
            "external_id": "brown_aj",
            "name": "A.J. Brown",
            "position": "WR",
            "jersey_number": 11,
        },
        {
            "external_id": "goedert_dallas",
            "name": "Dallas Goedert",
            "position": "TE",
            "jersey_number": 88,
        },
    ],
    "WAS": [
        {
            "external_id": "howell_sam",
            "name": "Sam Howell",
            "position": "QB",
            "jersey_number": 14,
        },
        {
            "external_id": "robinson_brian",
            "name": "Brian Robinson",
            "position": "RB",
            "jersey_number": 8,
        },
        {
            "external_id": "mclaurin_terry",
            "name": "Terry McLaurin",
            "position": "WR",
            "jersey_number": 17,
        },
        {
            "external_id": "thomas_logan",
            "name": "Logan Thomas",
            "position": "TE",
            "jersey_number": 82,
        },
    ],
    "CHI": [
        {
            "external_id": "fields_justin",
            "name": "Justin Fields",
            "position": "QB",
            "jersey_number": 1,
        },
        {
            "external_id": "herbert_khalil",
            "name": "Khalil Herbert",
            "position": "RB",
            "jersey_number": 24,
        },
        {
            "external_id": "moore_dj",
            "name": "DJ Moore",
            "position": "WR",
            "jersey_number": 2,
        },
        {
            "external_id": "kmet_cole",
            "name": "Cole Kmet",
            "position": "TE",
            "jersey_number": 85,
        },
    ],
    "DET": [
        {
            "external_id": "goff_jared",
            "name": "Jared Goff",
            "position": "QB",
            "jersey_number": 16,
        },
        {
            "external_id": "montgomery_david",
            "name": "David Montgomery",
            "position": "RB",
            "jersey_number": 5,
        },
        {
            "external_id": "stbrown_amon",
            "name": "Amon-Ra St. Brown",
            "position": "WR",
            "jersey_number": 14,
        },
        {
            "external_id": "laporta_sam",
            "name": "Sam LaPorta",
            "position": "TE",
            "jersey_number": 87,
        },
    ],
    "GB": [
        {
            "external_id": "love_jordan",
            "name": "Jordan Love",
            "position": "QB",
            "jersey_number": 10,
        },
        {
            "external_id": "jones_aaron",
            "name": "Aaron Jones",
            "position": "RB",
            "jersey_number": 33,
        },
        {
            "external_id": "watson_christian",
            "name": "Christian Watson",
            "position": "WR",
            "jersey_number": 9,
        },
        {
            "external_id": "musgrave_luke",
            "name": "Luke Musgrave",
            "position": "TE",
            "jersey_number": 88,
        },
    ],
    "MIN": [
        {
            "external_id": "cousins_kirk",
            "name": "Kirk Cousins",
            "position": "QB",
            "jersey_number": 8,
        },
        {
            "external_id": "mattison_alexander",
            "name": "Alexander Mattison",
            "position": "RB",
            "jersey_number": 2,
        },
        {
            "external_id": "jefferson_justin",
            "name": "Justin Jefferson",
            "position": "WR",
            "jersey_number": 18,
        },
        {
            "external_id": "hockenson_tj",
            "name": "T.J. Hockenson",
            "position": "TE",
            "jersey_number": 87,
        },
    ],
    "ATL": [
        {
            "external_id": "ridder_desmond",
            "name": "Desmond Ridder",
            "position": "QB",
            "jersey_number": 4,
        },
        {
            "external_id": "robinson_bijan",
            "name": "Bijan Robinson",
            "position": "RB",
            "jersey_number": 7,
        },
        {
            "external_id": "london_drake",
            "name": "Drake London",
            "position": "WR",
            "jersey_number": 5,
        },
        {
            "external_id": "pitts_kyle",
            "name": "Kyle Pitts",
            "position": "TE",
            "jersey_number": 8,
        },
    ],
    "CAR": [
        {
            "external_id": "young_bryce",
            "name": "Bryce Young",
            "position": "QB",
            "jersey_number": 9,
        },
        {
            "external_id": "hubbard_chuba",
            "name": "Chuba Hubbard",
            "position": "RB",
            "jersey_number": 30,
        },
        {
            "external_id": "thielen_adam",
            "name": "Adam Thielen",
            "position": "WR",
            "jersey_number": 19,
        },
        {
            "external_id": "tremble_tommy",
            "name": "Tommy Tremble",
            "position": "TE",
            "jersey_number": 82,
        },
    ],
    "NO": [
        {
            "external_id": "carr_derek",
            "name": "Derek Carr",
            "position": "QB",
            "jersey_number": 4,
        },
        {
            "external_id": "kamara_alvin",
            "name": "Alvin Kamara",
            "position": "RB",
            "jersey_number": 41,
        },
        {
            "external_id": "olave_chris",
            "name": "Chris Olave",
            "position": "WR",
            "jersey_number": 12,
        },
        {
            "external_id": "hill_taysom",
            "name": "Taysom Hill",
            "position": "TE",
            "jersey_number": 7,
        },
    ],
    "TB": [
        {
            "external_id": "mayfield_baker",
            "name": "Baker Mayfield",
            "position": "QB",
            "jersey_number": 6,
        },
        {
            "external_id": "white_rachaad",
            "name": "Rachaad White",
            "position": "RB",
            "jersey_number": 29,
        },
        {
            "external_id": "evans_mike",
            "name": "Mike Evans",
            "position": "WR",
            "jersey_number": 13,
        },
        {
            "external_id": "otton_cade",
            "name": "Cade Otton",
            "position": "TE",
            "jersey_number": 88,
        },
    ],
    "ARI": [
        {
            "external_id": "murray_kyler",
            "name": "Kyler Murray",
            "position": "QB",
            "jersey_number": 1,
        },
        {
            "external_id": "conner_james",
            "name": "James Conner",
            "position": "RB",
            "jersey_number": 6,
        },
        {
            "external_id": "harrisonjr_marvin",
            "name": "Marvin Harrison Jr.",
            "position": "WR",
            "jersey_number": 18,
        },
        {
            "external_id": "ertz_zach",
            "name": "Zach Ertz",
            "position": "TE",
            "jersey_number": 86,
        },
    ],
    "LAR": [
        {
            "external_id": "stafford_matthew",
            "name": "Matthew Stafford",
            "position": "QB",
            "jersey_number": 9,
        },
        {
            "external_id": "akers_cam",
            "name": "Cam Akers",
            "position": "RB",
            "jersey_number": 3,
        },
        {
            "external_id": "kupp_cooper",
            "name": "Cooper Kupp",
            "position": "WR",
            "jersey_number": 10,
        },
        {
            "external_id": "higbee_tyler",
            "name": "Tyler Higbee",
            "position": "TE",
            "jersey_number": 89,
        },
    ],
    "SF": [
        {
            "external_id": "purdy_brock",
            "name": "Brock Purdy",
            "position": "QB",
            "jersey_number": 13,
        },
        {
            "external_id": "mccaffrey_christian",
            "name": "Christian McCaffrey",
            "position": "RB",
            "jersey_number": 23,
        },
        {
            "external_id": "aiyuk_brandon",
            "name": "Brandon Aiyuk",
            "position": "WR",
            "jersey_number": 11,
        },
        {
            "external_id": "kittle_george",
            "name": "George Kittle",
            "position": "TE",
            "jersey_number": 85,
        },
    ],
    "SEA": [
        {
            "external_id": "smith_geno",
            "name": "Geno Smith",
            "position": "QB",
            "jersey_number": 7,
        },
        {
            "external_id": "walker_kenneth",
            "name": "Kenneth Walker III",
            "position": "RB",
            "jersey_number": 9,
        },
        {
            "external_id": "metcalf_dk",
            "name": "DK Metcalf",
            "position": "WR",
            "jersey_number": 14,
        },
        {
            "external_id": "fant_noah",
            "name": "Noah Fant",
            "position": "TE",
            "jersey_number": 87,
        },
    ],
}


async def seed_players():
    """Seed sample players for all NFL teams"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        print("🏈 Seeding NFL players...")

        # Get all teams
        result = await session.execute(select(Team))
        teams = {team.abbreviation: team for team in result.scalars().all()}

        if not teams:
            print("❌ No teams found! Please run seed_teams.py first.")
            return

        # Check existing players
        result = await session.execute(select(Player))
        existing_players = result.scalars().all()
        existing_external_ids = {player.external_id for player in existing_players}

        players_created = 0
        players_skipped = 0

        for team_abbr, players_data in SAMPLE_PLAYERS.items():
            if team_abbr not in teams:
                print(f"⚠️  Team {team_abbr} not found, skipping players")
                continue

            team = teams[team_abbr]
            print(f"\n📋 {team.name}:")

            for player_data in players_data:
                if player_data["external_id"] in existing_external_ids:
                    print(f"   ⏭️  Skipping {player_data['name']} (already exists)")
                    players_skipped += 1
                    continue

                player = Player(
                    external_id=player_data["external_id"],
                    name=player_data["name"],
                    team_id=team.id,
                    position=player_data["position"],
                    jersey_number=player_data.get("jersey_number"),
                    is_active=True,
                )
                session.add(player)
                players_created += 1
                print(
                    f"   ✅ Created {player_data['name']} ({player_data['position']} #{player_data.get('jersey_number', 'N/A')})"
                )

        if players_created > 0:
            await session.commit()

        print(f"\n📊 Summary:")
        print(f"   Created: {players_created} players")
        print(f"   Skipped: {players_skipped} players (already exist)")
        print(f"   Total: {sum(len(p) for p in SAMPLE_PLAYERS.values())} players")

    await engine.dispose()
    print("\n✅ Player seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_players())
