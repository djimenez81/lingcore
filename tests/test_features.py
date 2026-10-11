"""Tests for lingcore.features."""

import pytest

from lingcore import Feature, FeatureKind, FeatureSystem
from lingcore.encoding import ValueEncoder


class TestFeature:
    def test_minimal(self) -> None:
        f = Feature("voice")
        assert f.name == "voice"
        assert f.kind is FeatureKind.BINARY
        assert f.description == ""
        assert f.aliases == ()

    def test_kind(self) -> None:
        f = Feature("height", kind=FeatureKind.MULTI)
        assert f.kind is FeatureKind.MULTI

    def test_aliases_are_tuple(self) -> None:
        f = Feature("voice", aliases=["voi", "voiced"])
        assert f.aliases == ("voi", "voiced")
        assert isinstance(f.aliases, tuple)

    def test_frozen(self) -> None:
        f = Feature("voice")
        with pytest.raises(AttributeError):
            f.name = "nasal"  # type: ignore[misc]

    def test_hashable(self) -> None:
        f = Feature("voice")
        assert {f, f} == {f}

    def test_equality(self) -> None:
        assert Feature("voice") == Feature("voice")
        assert Feature("voice") != Feature("nasal")
        assert Feature("voice") != Feature("voice", aliases=("voi",))

    def test_matches(self) -> None:
        f = Feature("voice", aliases=("voi", "voiced"))
        assert f.matches("voice")
        assert f.matches("voi")
        assert f.matches("voiced")
        assert not f.matches("nasal")


class TestFeatureSystem:
    def _system(self) -> FeatureSystem:
        return FeatureSystem(
            name="toy",
            version="0.1.0",
            features=(Feature("voice"), Feature("nasal")),
        )

    def test_minimal(self) -> None:
        s = self._system()
        assert s.name == "toy"
        assert s.version == "0.1.0"
        assert len(s) == 2
        assert s.names() == ("voice", "nasal")

    def test_features_are_tuple(self) -> None:
        s = self._system()
        assert isinstance(s.features, tuple)

    def test_duplicate_feature_names_raise(self) -> None:
        with pytest.raises(ValueError, match="Duplicate feature"):
            FeatureSystem(
                name="toy",
                version="0.1.0",
                features=(Feature("voice"), Feature("voice")),
            )

    def test_encoder_defaults_when_omitted(self) -> None:
        s = self._system()
        assert s.encoder is not None
        assert s.encoder.encode(__import__("lingcore").Value("+")) == 1.0

    def test_encoder_can_be_supplied(self) -> None:
        enc = ValueEncoder({__import__("lingcore").Value("+"): 42.0})
        s = FeatureSystem(
            name="toy",
            version="0.1.0",
            features=(Feature("voice"),),
            encoder=enc,
        )
        assert s.encoder is enc

    def test_metadata_frozen(self) -> None:
        s = FeatureSystem(
            name="toy",
            version="0.1.0",
            features=(Feature("voice"),),
            metadata={"source": "test"},
        )
        with pytest.raises(TypeError):
            s.metadata["source"] = "other"  # type: ignore[index]

    def test_iter(self) -> None:
        s = self._system()
        assert [f.name for f in s] == ["voice", "nasal"]

    def test_contains_by_canonical_name(self) -> None:
        s = self._system()
        assert "voice" in s
        assert "nasal" in s
        assert "height" not in s

    def test_contains_by_alias(self) -> None:
        s = FeatureSystem(
            name="toy",
            version="0.1.0",
            features=(Feature("voice", aliases=("voi",)),),
        )
        assert "voi" in s

    def test_contains_rejects_non_string(self) -> None:
        s = self._system()
        assert 5 not in s

    def test_getitem(self) -> None:
        s = self._system()
        assert s["voice"].name == "voice"

    def test_index(self) -> None:
        s = self._system()
        assert s.index("voice") == 0
        assert s.index("nasal") == 1

    def test_index_by_alias(self) -> None:
        s = FeatureSystem(
            name="toy",
            version="0.1.0",
            features=(
                Feature("voice", aliases=("voi",)),
                Feature("nasal"),
            ),
        )
        assert s.index("voi") == 0

    def test_resolve_missing(self) -> None:
        s = self._system()
        with pytest.raises(KeyError, match="matches 0"):
            s.resolve("height")

    def test_resolve_ambiguous(self) -> None:
        s = FeatureSystem(
            name="toy",
            version="0.1.0",
            features=(
                Feature("voice"),
                Feature("nasal", aliases=("voice",)),
            ),
        )
        with pytest.raises(KeyError, match="matches 2"):
            s.resolve("voice")

    def test_hashable(self) -> None:
        s1 = self._system()
        s2 = self._system()
        assert s1 == s2
        assert {s1, s2} == {s1}

    def test_hash_ignores_encoder_and_metadata(self) -> None:
        s1 = FeatureSystem(
            name="toy",
            version="0.1.0",
            features=(Feature("voice"),),
        )
        s2 = FeatureSystem(
            name="toy",
            version="0.1.0",
            features=(Feature("voice"),),
            metadata={"source": "test"},
        )
        # Two systems that differ only in metadata are unequal but
        # may hash the same; both facts are consistent with the
        # Python hash contract.
        assert hash(s1) == hash(s2)
