"""Tests for lingcore.matrix."""

import numpy as np
import pytest

from lingcore import (
    Feature,
    FeatureMatrix,
    FeatureSystem,
    Segment,
    SegmentInventory,
    Value,
    feature_matrix,
)


def _binary_system() -> FeatureSystem:
    return FeatureSystem(
        name="toy",
        version="0.1.0",
        features=(Feature("voice"), Feature("nasal")),
    )


def _plus_minus(name: str) -> Value:
    return Value(name)


def _make_inventory() -> SegmentInventory:
    inv = SegmentInventory(
        id="toy",
        types=("consonant",),
        classifiers={"consonant": ()},
    )
    inv.add(
        Segment(
            symbol="p",
            type="consonant",
            values={
                "voice": _plus_minus("-"),
                "nasal": _plus_minus("-"),
            },
        )
    )
    inv.add(
        Segment(
            symbol="b",
            type="consonant",
            values={
                "voice": _plus_minus("+"),
                "nasal": _plus_minus("-"),
            },
        )
    )
    inv.add(
        Segment(
            symbol="m",
            type="consonant",
            values={
                "voice": _plus_minus("+"),
                "nasal": _plus_minus("+"),
            },
        )
    )
    return inv


class TestFeatureMatrix:
    def test_shape(self) -> None:
        m = feature_matrix(_make_inventory(), _binary_system())
        assert m.data.shape == (3, 2)
        assert m.segment_ids == ("p", "b", "m")
        assert m.feature_names == ("voice", "nasal")

    def test_undefined_is_nan(self) -> None:
        inv = SegmentInventory(
            id="toy",
            types=("consonant",),
            classifiers={"consonant": ()},
        )
        inv.add(Segment(symbol="p", type="consonant"))
        m = feature_matrix(inv, _binary_system())
        assert np.isnan(m.data).all()

    def test_read_only(self) -> None:
        m = feature_matrix(_make_inventory(), _binary_system())
        with pytest.raises(ValueError):
            m.data[0, 0] = 0.0

    def test_distinguishing_features(self) -> None:
        m = feature_matrix(_make_inventory(), _binary_system())
        assert m.distinguishing_features(0, 1) == ["voice"]
        assert m.distinguishing_features(0, 2) == ["voice", "nasal"]
        assert m.distinguishing_features(1, 2) == ["nasal"]

    def test_pair_covers(self) -> None:
        m = feature_matrix(_make_inventory(), _binary_system())
        covers = m.pair_covers()
        assert covers["voice"] == {(0, 1), (0, 2)}
        assert covers["nasal"] == {(0, 2), (1, 2)}

    def test_non_binary_value_raises(self) -> None:
        inv = SegmentInventory(
            id="toy",
            types=("consonant",),
            classifiers={"consonant": ()},
        )
        inv.add(
            Segment(
                symbol="p",
                type="consonant",
                values={"voice": Value("close")},
            )
        )
        with pytest.raises(ValueError, match="non-binary"):
            feature_matrix(inv, _binary_system())
