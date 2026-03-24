"""Tests for the data cleaning utilities in git_miner.datasets.cleaner."""

import pytest

from git_miner.datasets.cleaner import (
    _clamp_non_negative,
    _clean_text,
    _clean_topics,
    clean_repository_record,
    deduplicate_records,
)


class TestCleanText:
    def test_none_returns_none(self):
        assert _clean_text(None) is None

    def test_strips_leading_trailing_whitespace(self):
        assert _clean_text("  hello world  ") == "hello world"

    def test_collapses_internal_whitespace(self):
        assert _clean_text("hello   world") == "hello world"

    def test_removes_newlines(self):
        assert _clean_text("hello\nworld") == "hello world"

    def test_removes_control_characters(self):
        assert _clean_text("hello\x00world") == "hello world"

    def test_empty_string_returns_none(self):
        assert _clean_text("   ") is None

    def test_normal_string_unchanged(self):
        assert _clean_text("Python web framework") == "Python web framework"

    def test_unicode_normalization(self):
        # Combining characters should be normalized
        result = _clean_text("caf\u00e9")
        assert result is not None
        assert "caf" in result


class TestCleanTopics:
    def test_none_returns_none(self):
        assert _clean_topics(None) is None

    def test_empty_string_returns_none(self):
        assert _clean_topics("") is None

    def test_lowercases_topics(self):
        assert _clean_topics("Python,Django") == "python,django"

    def test_strips_whitespace_from_topics(self):
        assert _clean_topics("  python , django  ") == "python,django"

    def test_removes_empty_topics(self):
        assert _clean_topics("python,,django") == "python,django"

    def test_single_topic(self):
        assert _clean_topics("python") == "python"

    def test_all_empty_topics_returns_none(self):
        assert _clean_topics(",,,") is None


class TestClampNonNegative:
    def test_none_returns_none(self):
        assert _clamp_non_negative(None) is None

    def test_positive_value_unchanged(self):
        assert _clamp_non_negative(100) == 100

    def test_zero_unchanged(self):
        assert _clamp_non_negative(0) == 0

    def test_negative_clamped_to_zero(self):
        assert _clamp_non_negative(-5) == 0


class TestCleanRepositoryRecord:
    @pytest.fixture()
    def sample_record(self):
        return {
            "repository_id": 1,
            "name": "  Hello-World  ",
            "owner": "octocat",
            "full_name": "octocat/Hello-World",
            "description": "My first\nrepository  ",
            "primary_language": "Python",
            "stars": 100,
            "forks": 50,
            "open_issues": 10,
            "license": "MIT License",
            "license_key": "mit",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z",
            "pushed_at": "2024-01-01T12:00:00Z",
            "size_kb": 1024,
            "url": "https://github.com/octocat/Hello-World",
            "api_url": "https://api.github.com/repos/octocat/Hello-World",
            "is_fork": False,
            "is_archived": False,
            "topics": "GitHub , API , Example",
        }

    def test_strips_name_whitespace(self, sample_record):
        result = clean_repository_record(sample_record)
        assert result["name"] == "Hello-World"

    def test_cleans_description_newlines(self, sample_record):
        result = clean_repository_record(sample_record)
        assert result["description"] == "My first repository"

    def test_cleans_topics(self, sample_record):
        result = clean_repository_record(sample_record)
        assert result["topics"] == "github,api,example"

    def test_non_negative_stars(self, sample_record):
        sample_record["stars"] = -5
        result = clean_repository_record(sample_record)
        assert result["stars"] == 0

    def test_non_negative_forks(self, sample_record):
        sample_record["forks"] = -1
        result = clean_repository_record(sample_record)
        assert result["forks"] == 0

    def test_none_description_stays_none(self, sample_record):
        sample_record["description"] = None
        result = clean_repository_record(sample_record)
        assert result["description"] is None

    def test_none_topics_stays_none(self, sample_record):
        sample_record["topics"] = None
        result = clean_repository_record(sample_record)
        assert result["topics"] is None

    def test_does_not_mutate_original(self, sample_record):
        original_name = sample_record["name"]
        clean_repository_record(sample_record)
        assert sample_record["name"] == original_name

    def test_non_text_fields_preserved(self, sample_record):
        result = clean_repository_record(sample_record)
        assert result["repository_id"] == 1
        assert result["is_fork"] is False
        assert result["is_archived"] is False
        assert result["created_at"] == "2024-01-01T00:00:00Z"


class TestDeduplicateRecords:
    def test_no_duplicates_unchanged(self):
        records = [{"repository_id": 1}, {"repository_id": 2}]
        result = deduplicate_records(records)
        assert len(result) == 2

    def test_removes_duplicate_ids(self):
        records = [
            {"repository_id": 1, "name": "first"},
            {"repository_id": 1, "name": "duplicate"},
            {"repository_id": 2, "name": "other"},
        ]
        result = deduplicate_records(records)
        assert len(result) == 2
        assert result[0]["name"] == "first"

    def test_preserves_order(self):
        records = [
            {"repository_id": 3},
            {"repository_id": 1},
            {"repository_id": 2},
        ]
        result = deduplicate_records(records)
        assert [r["repository_id"] for r in result] == [3, 1, 2]

    def test_custom_key(self):
        records = [
            {"full_name": "a/b"},
            {"full_name": "a/b"},
            {"full_name": "c/d"},
        ]
        result = deduplicate_records(records, key="full_name")
        assert len(result) == 2

    def test_empty_list(self):
        assert deduplicate_records([]) == []
