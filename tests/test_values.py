"""Tests for lingcore.values."""

import pytest

from lingcore import Value, ValueSet


class TestValue:
    def test_minimal(self) -> None:
        v = Value("close")
        assert v.name == "close"
        assert v.description == ""
        assert v.aliases == ()

    def test_aliases_are_tuple(self) -> None:
        v = Value("close", aliases=["high", "closed"])
        assert v.aliases == ("high", "closed")
        assert isinstance(v.aliases, tuple)

    def test_frozen(self) -> None:
        v = Value("close")
        with pytest.raises(AttributeError):
            v.name = "open"  # type: ignore[misc]

    def test_hashable(self) -> None:
        v = Value("close")
        assert {v, v} == {v}

    def test_equality(self) -> None:
        assert Value("close") == Value("close")
        assert Value("close") != Value("open")

    def test_matches(self) -> None:
        v = Value("close", aliases=("high",))
        assert v.matches("close")
        assert v.matches("high")
        assert not v.matches("low")


class TestValueSet:
    def test_contains_value(self) -> None:
        s = ValueSet(
            "height", values=(Value("close"), Value("open"))
        )
        assert Value("close") in s
        assert Value("mid") not in s

    def test_contains_string_by_name(self) -> None:
        s = ValueSet("height", values=(Value("close"),))
        assert "close" in s
        assert "mid" not in s

    def test_resolve(self) -> None:
        s = ValueSet(
            "height",
            values=(Value("close", aliases=("high",)), Value("open")),
        )
        assert s.resolve("high").name == "close"

    def test_resolve_ambiguous(self) -> None:
        s = ValueSet(
            "height",
            values=(Value("close"), Value("open", aliases=("close",))),
        )
        with pytest.raises(KeyError, match="matches 2"):
            s.resolve("close")

    def test_resolve_missing(self) -> None:
        s = ValueSet("height", values=(Value("close"),))
        with pytest.raises(KeyError, match="matches 0"):
            s.resolve("mid")
