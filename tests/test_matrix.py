"""Tests for lingcore.matrix."""

import numpy as np
import pytest

from lingcore import (
    Feature,
    FeatureKind,
    FeatureSystem,
    Segment,
    SegmentInventory,
    Value,
    feature_matrix,
)
from lingcore.encoding import ValueEncoder


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

    def test_copy_on_construction(self) -> None:
        original = np.zeros((1, 1), dtype=float)
        matrix = feature_matrix(_make_inventory(), _binary_system())
        # Constructing a matrix from `original` should not mutate it.
        from lingcore import FeatureMatrix
        FeatureMatrix(
            segment_ids=("x",),
            feature_names=("f",),
            data=original,
        )
        # `original` is still writable.
        original[0, 0] = 5.0
        assert original[0, 0] == 5.0

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

    def test_equality(self) -> None:
        m1 = feature_matrix(_make_inventory(), _binary_system())
        m2 = feature_matrix(_make_inventory(), _binary_system())
        assert m1 == m2

    def test_equality_all_nan(self) -> None:
        inv = SegmentInventory(
            id="toy",
            types=("consonant",),
            classifiers={"consonant": ()},
        )
        inv.add(Segment(symbol="p", type="consonant"))
        m1 = feature_matrix(inv, _binary_system())
        m2 = feature_matrix(inv, _binary_system())
        assert m1 == m2
        assert hash(m1) == hash(m2)

    def test_inequality(self) -> None:
        m1 = feature_matrix(_make_inventory(), _binary_system())
        inv = _make_inventory()
        inv.add(Segment(symbol="x", type="consonant"))
        m2 = feature_matrix(inv, _binary_system())
        assert m1 != m2

    def test_hashable(self) -> None:
        m1 = feature_matrix(_make_inventory(), _binary_system())
        m2 = feature_matrix(_make_inventory(), _binary_system())
        assert {m1, m2} == {m1}

    def test_to_records_preserves_floats(self) -> None:
        m = feature_matrix(_make_inventory(), _binary_system())
        records = m.to_records()
        assert records[0] == {
            "symbol": "p",
            "voice": 0.0,
            "nasal": 0.0,
        }
        assert records[2] == {
            "symbol": "m",
            "voice": 1.0,
            "nasal": 1.0,
        }

    def test_to_records_nonbinary_encoder(self) -> None:
        system = FeatureSystem(
            name="toy",
            version="0.1.0",
            features=(Feature("voice"),),
            encoder=ValueEncoder(
                {
                    Value("+"): 100.0,
                    Value("-"): -100.0,
                    None: float("nan"),
                }
            ),
        )
        inv = _make_inventory()
        m = feature_matrix(inv, system)
        records = m.to_records()
        assert records[0]["voice"] == -100.0
        assert records[1]["voice"] == 100.0

    def test_to_records_nan_is_none(self) -> None:
        inv = SegmentInventory(
            id="toy",
            types=("consonant",),
            classifiers={"consonant": ()},
        )
        inv.add(Segment(symbol="p", type="consonant"))
        m = feature_matrix(inv, _binary_system())
        for record in m.to_records():
            assert record["voice"] is None
            assert record["nasal"] is None

    def test_non_binary_feature_kind_rejected(self) -> None:
        system = FeatureSystem(
            name="toy",
            version="0.1.0",
            features=(Feature("height", kind=FeatureKind.MULTI),),
        )
        inv = SegmentInventory(
            id="toy",
            types=("vowel",),
            classifiers={"vowel": ()},
        )
        with pytest.raises(NotImplementedError, match="MULTI"):
            feature_matrix(inv, system)

    def test_encoder_unknown_value_raises(self) -> None:
        system = _binary_system()
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
        with pytest.raises(ValueError, match="No encoding"):
            feature_matrix(inv, system)

    def test_wrong_shape_rejected(self) -> None:
        from lingcore import FeatureMatrix
        with pytest.raises(ValueError, match="shape"):
            FeatureMatrix(
                segment_ids=("x",),
                feature_names=("f",),
                data=np.zeros((2, 1), dtype=float),
            )
