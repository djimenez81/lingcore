"""Tests for lingcore.segments."""

import pytest

from lingcore import Segment, Value


class TestConstruction:
    def test_minimal(self) -> None:
        s = Segment("p", "consonant")
        assert s.symbol == "p"
        assert s.type == "consonant"
        assert s.classification == {}
        assert s.values == {}
        assert s.metadata == {}

    def test_full(self) -> None:
        s = Segment(
            symbol="p",
            type="consonant",
            classification={"manner": Value("stop")},
            values={"voice": Value("-")},
            metadata={"source": "test"},
        )
        assert s.classification["manner"] == Value("stop")
        assert s.values["voice"] == Value("-")
        assert s.metadata["source"] == "test"

    def test_frozen(self) -> None:
        s = Segment("p", "consonant")
        with pytest.raises(AttributeError):
            s.symbol = "b"  # type: ignore[misc]

    def test_inner_mappings_frozen(self) -> None:
        s = Segment(
            "p", "consonant", classification={"m": Value("stop")}
        )
        with pytest.raises(TypeError):
            s.classification["x"] = Value("y")  # type: ignore[index]


class TestEquality:
    def test_equality_all_fields(self) -> None:
        a = Segment(
            "p",
            "consonant",
            classification={"manner": Value("stop")},
        )
        b = Segment(
            "p",
            "consonant",
            classification={"manner": Value("stop")},
        )
        assert a == b

    def test_inequality_different_symbol(self) -> None:
        assert Segment("p", "consonant") != Segment("b", "consonant")

    def test_inequality_different_type(self) -> None:
        assert Segment("p", "consonant") != Segment("p", "vowel")

    def test_inequality_different_classification(self) -> None:
        a = Segment(
            "p",
            "consonant",
            classification={"manner": Value("stop")},
        )
        b = Segment(
            "p",
            "consonant",
            classification={"manner": Value("fricative")},
        )
        assert a != b

    def test_inequality_different_values(self) -> None:
        a = Segment("p", "consonant", values={"voice": Value("-")})
        b = Segment("p", "consonant", values={"voice": Value("+")})
        assert a != b

    def test_equality_ignores_metadata(self) -> None:
        a = Segment("p", "consonant")
        b = Segment("p", "consonant", metadata={"source": "test"})
        assert a == b
        assert hash(a) == hash(b)


class TestHashing:
    def test_hashable(self) -> None:
        s = Segment("p", "consonant")
        assert {s, s} == {s}

    def test_hashable_with_metadata(self) -> None:
        s = Segment(
            "p", "consonant", metadata={"source": "test"}
        )
        assert hash(s) is not None

    def test_hashable_with_unhashable_metadata_values(self) -> None:
        # Metadata values are not required to be hashable, because
        # metadata is excluded from the hash.
        s = Segment(
            "p",
            "consonant",
            metadata={"sources": ["a", "b"]},
        )
        assert hash(s) is not None


class TestAccessors:
    def test_has_classifier(self) -> None:
        s = Segment(
            "p",
            "consonant",
            classification={"manner": Value("stop")},
        )
        assert s.has_classifier("manner")
        assert not s.has_classifier("place")

    def test_value_for(self) -> None:
        s = Segment("p", "consonant", values={"voice": Value("-")})
        assert s.value_for("voice") == Value("-")
        assert s.value_for("nasal") is None
