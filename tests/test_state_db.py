import pytest

from git_miner.state_db import StateDB


@pytest.fixture
def state_db():
    """Create a StateDB instance with in-memory database for testing."""
    return StateDB(db_path=":memory:")


def test_init_db(state_db):
    """Test that database is initialized correctly."""
    assert state_db.db_path == ":memory:"
    assert state_db._is_memory is True


def test_save_and_get_search(state_db):
    """Test saving and retrieving a search."""
    query = "python web framework"
    options = {
        "language": "python",
        "min_stars": 100,
        "max_stars": 1000,
    }

    state_db.save_search("test_search", query, options)
    retrieved = state_db.get_search("test_search")

    assert retrieved is not None
    assert retrieved["name"] == "test_search"
    assert retrieved["query"] == query
    assert retrieved["options"] == options
    assert "created_at" in retrieved
    assert "updated_at" in retrieved


def test_save_search_without_force(state_db):
    """Test that saving without force raises error for existing search."""
    query = "test query"
    options = {"language": "python"}

    state_db.save_search("test_search", query, options)

    with pytest.raises(ValueError, match="already exists"):
        state_db.save_search("test_search", "new query", {})


def test_save_search_with_force(state_db):
    """Test that saving with force overwrites existing search."""
    query1 = "first query"
    query2 = "second query"
    options1 = {"language": "python"}
    options2 = {"language": "javascript"}

    state_db.save_search("test_search", query1, options1)
    state_db.save_search("test_search", query2, options2, force=True)

    retrieved = state_db.get_search("test_search")
    assert retrieved["query"] == query2
    assert retrieved["options"] == options2


def test_get_nonexistent_search(state_db):
    """Test getting a search that doesn't exist."""
    retrieved = state_db.get_search("nonexistent")
    assert retrieved is None


def test_list_searches(state_db):
    """Test listing all saved searches."""
    searches = [
        ("search1", "query1", {"language": "python"}),
        ("search2", "query2", {"language": "javascript"}),
        ("search3", "query3", {"language": "go"}),
    ]

    for name, query, options in searches:
        state_db.save_search(name, query, options)

    result = state_db.list_searches()
    assert len(result) == 3

    names = [s["name"] for s in result]
    assert "search1" in names
    assert "search2" in names
    assert "search3" in names


def test_delete_search(state_db):
    """Test deleting a saved search."""
    state_db.save_search("test_search", "query", {"language": "python"})

    state_db.delete_search("test_search")

    retrieved = state_db.get_search("test_search")
    assert retrieved is None


def test_delete_nonexistent_search(state_db):
    """Test deleting a search that doesn't exist."""
    with pytest.raises(ValueError, match="not found"):
        state_db.delete_search("nonexistent")


def test_search_with_complex_options(state_db):
    """Test saving a search with complex options."""
    query = "machine learning"
    options = {
        "language": "python",
        "min_stars": 1000,
        "max_stars": 10000,
        "min_forks": 50,
        "max_forks": 500,
        "license": "mit",
        "topics": "ai,ml,data-science",
        "is_fork": False,
        "is_archived": False,
        "sort": "stars",
        "max_results": 50,
    }

    state_db.save_search("complex_search", query, options)
    retrieved = state_db.get_search("complex_search")

    assert retrieved is not None
    assert retrieved["query"] == query
    assert retrieved["options"] == options


def test_list_empty_searches(state_db):
    """Test listing searches when none exist."""
    result = state_db.list_searches()
    assert result == []
