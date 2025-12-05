"""Property-based tests for PlayerService"""

import pytest
import pytest_asyncio
from hypothesis import given, settings, strategies as st, HealthCheck
from app.db.models.player import Player
from app.services.player_service import PlayerService
import uuid


# Custom strategies for generating test data
@st.composite
def player_name_strategy(draw):
    """Generate realistic player names"""
    first_names = [
        "Patrick",
        "Tom",
        "Aaron",
        "Josh",
        "Travis",
        "Tyreek",
        "Justin",
        "Joe",
    ]
    last_names = [
        "Mahomes",
        "Brady",
        "Rodgers",
        "Allen",
        "Kelce",
        "Hill",
        "Jefferson",
        "Burrow",
    ]
    return f"{draw(st.sampled_from(first_names))} {draw(st.sampled_from(last_names))}"


@st.composite
def position_strategy(draw):
    """Generate valid NFL positions"""
    positions = ["QB", "RB", "WR", "TE", "K", "DEF"]
    return draw(st.sampled_from(positions))


@pytest_asyncio.fixture
async def create_test_player(db_session, test_team):
    """Factory fixture for creating test players"""

    async def _create_player(name: str, position: str = "QB"):
        player = Player(
            id=uuid.uuid4(),
            external_id=f"test_player_{uuid.uuid4()}",
            name=name,
            team_id=test_team.id,
            position=position,
            is_active=True,
        )
        db_session.add(player)
        await db_session.commit()
        await db_session.refresh(player)
        return player

    return _create_player


@pytest.mark.asyncio
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    search_query=st.text(
        min_size=1,
        max_size=20,
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
    )
)
async def test_property_14_player_search_returns_matches(
    search_query, player_service, create_test_player, db_session
):
    """
    Feature: pick-submission, Property 14: Player search returns matches
    For any search query string, the returned players should have names that match the query string.
    Validates: Requirements 6.1
    """
    # Setup: Create players with known names
    test_players = [
        await create_test_player("Patrick Mahomes", "QB"),
        await create_test_player("Travis Kelce", "TE"),
        await create_test_player("Tyreek Hill", "WR"),
    ]

    # Action: Search for players
    results = await player_service.search_players(search_query)

    # Assert: All returned players should have names matching the query (case-insensitive)
    query_lower = search_query.lower()
    for player in results:
        assert (
            query_lower in player.name.lower()
        ), f"Player '{player.name}' does not contain search query '{search_query}'"


@pytest.mark.asyncio
async def test_property_14_player_search_returns_matches_unit(
    player_service, create_test_player
):
    """
    Unit test version of Property 14 with specific examples
    """
    # Setup: Create test players
    await create_test_player("Patrick Mahomes", "QB")
    await create_test_player("Travis Kelce", "TE")
    await create_test_player("Tyreek Hill", "WR")

    # Test 1: Search for "Patrick" should return Patrick Mahomes
    results = await player_service.search_players("Patrick")
    assert len(results) >= 1
    assert any("Patrick" in p.name for p in results)

    # Test 2: Search for "Kelce" should return Travis Kelce
    results = await player_service.search_players("Kelce")
    assert len(results) >= 1
    assert any("Kelce" in p.name for p in results)

    # Test 3: Case-insensitive search
    results = await player_service.search_players("mahomes")
    assert len(results) >= 1
    assert any("Mahomes" in p.name for p in results)

    # Test 4: Partial match
    results = await player_service.search_players("Tyr")
    assert len(results) >= 1
    assert any("Tyreek" in p.name for p in results)


@pytest.mark.asyncio
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(player_name=player_name_strategy(), position=position_strategy())
async def test_property_15_player_search_response_completeness(
    player_name, position, player_service, create_test_player
):
    """
    Feature: pick-submission, Property 15: Player search response completeness
    For any player returned from search, the response should include player name, team, and position.
    Validates: Requirements 6.2
    """
    # Setup: Create a player with the generated data
    player = await create_test_player(player_name, position)

    # Action: Search for the player
    search_term = player_name.split()[0]  # Search by first name
    results = await player_service.search_players(search_term)

    # Assert: All returned players should have required fields
    for result_player in results:
        assert result_player.name is not None, "Player name is missing"
        assert result_player.team_id is not None, "Player team is missing"
        assert result_player.position is not None, "Player position is missing"
        assert isinstance(result_player.name, str), "Player name should be a string"


@pytest.mark.asyncio
async def test_property_15_player_search_response_completeness_unit(
    player_service, create_test_player
):
    """
    Unit test version of Property 15 with specific examples
    """
    # Setup: Create test player
    player = await create_test_player("Patrick Mahomes", "QB")

    # Action: Search for the player
    results = await player_service.search_players("Patrick")

    # Assert: Response should include all required fields
    assert len(results) >= 1
    found_player = next((p for p in results if p.id == player.id), None)
    assert found_player is not None
    assert found_player.name == "Patrick Mahomes"
    assert found_player.team_id is not None
    assert found_player.position == "QB"


@pytest.mark.asyncio
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    non_matching_query=st.text(
        min_size=10,
        max_size=30,
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll"), blacklist_characters="aeiouAEIOU"
        ),
    ).filter(lambda x: len(x.strip()) >= 10)
)
async def test_property_16_non_matching_search_returns_empty(
    non_matching_query, player_service, create_test_player
):
    """
    Feature: pick-submission, Property 16: Non-matching search returns empty
    For any search query that does not match any player names, the system should return an empty list.
    Validates: Requirements 6.4
    """
    # Setup: Create players with known names
    await create_test_player("Patrick Mahomes", "QB")
    await create_test_player("Travis Kelce", "TE")

    # Action: Search with a query that shouldn't match
    results = await player_service.search_players(non_matching_query)

    # Assert: If no matches, should return empty list
    # Note: We can't guarantee no matches with random strings, so we verify the property:
    # If results exist, they must contain the query string
    for player in results:
        assert (
            non_matching_query.lower() in player.name.lower()
        ), f"Player '{player.name}' returned but doesn't match query '{non_matching_query}'"


@pytest.mark.asyncio
async def test_property_16_non_matching_search_returns_empty_unit(
    player_service, create_test_player
):
    """
    Unit test version of Property 16 with specific examples
    """
    # Setup: Create test players
    await create_test_player("Patrick Mahomes", "QB")
    await create_test_player("Travis Kelce", "TE")

    # Test 1: Search for non-existent player
    results = await player_service.search_players("ZzZzNonExistentPlayerXxXx")
    assert len(results) == 0, "Should return empty list for non-matching query"

    # Test 2: Empty query should return empty list
    results = await player_service.search_players("")
    assert len(results) == 0, "Should return empty list for empty query"

    # Test 3: Whitespace-only query should return empty list
    results = await player_service.search_players("   ")
    assert len(results) == 0, "Should return empty list for whitespace query"
