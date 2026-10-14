"""Tests for lingcore.inventories."""

import pytest

from lingcore import Segment, SegmentInventory, Value, ValueSet


def _vowel_inventory() -> SegmentInventory:
    return SegmentInventory(
        id="toy",
        types=("vowel",),
        classifiers={"vowel": ("height", "backness", "roundness")},
    )


class TestConstruction:
    def test_empty(self) -> None:
        inv = _vowel_inventory()
        assert len(inv) == 0
        assert inv.symbols() == ()
        assert inv.segments == ()

    def test_types_are_tuple(self) -> None:
        inv = _vowel_inventory()
        assert isinstance(inv.types, tuple)

    def test_classifiers_are_frozen(self) -> None:
        inv = _vowel_inventory()
        with pytest.raises(TypeError):
            inv.classifiers["vowel"] = ("x",)  # type: ignore[index]

    def test_classifier_tuples_are_tuples(self) -> None:
        inv = _vowel_inventory()
        assert isinstance(inv.classifiers["vowel"], tuple)

    def test_segments_property_is_tuple(self) -> None:
        inv = _vowel_inventory()
        assert isinstance(inv.segments, tuple)

    def test_duplicate_types_rejected(self) -> None:
        with pytest.raises(ValueError, match="Duplicate types"):
            SegmentInventory(
                id="toy",
                types=("vowel", "vowel"),
                classifiers={"vowel": ()},
            )

    def test_classifiers_for_unknown_type_rejected(self) -> None:
        with pytest.raises(ValueError, match="unknown types"):
            SegmentInventory(
                id="toy",
                types=("vowel",),
                classifiers={"consonant": ()},
            )

    def test_value_set_for_unknown_classifier_rejected(self) -> None:
        with pytest.raises(ValueError, match="unknown classifiers"):
            SegmentInventory(
                id="toy",
                types=("vowel",),
                classifiers={"vowel": ("height",)},
                value_sets={
                    "backness": ValueSet(
                        "backness", values=(Value("front"),)
                    )
                },
            )


class TestFromSegments:
    def test_basic(self) -> None:
        inv = SegmentInventory.from_segments(
            id="toy",
            types=("vowel",),
            classifiers={"vowel": ()},
            segments=[
                Segment("u", "vowel"),
                Segment("i", "vowel"),
            ],
        )
        assert inv.symbols() == ("u", "i")

    def test_validation_applies(self) -> None:
        with pytest.raises(ValueError, match="not in"):
            SegmentInventory.from_segments(
                id="toy",
                types=("vowel",),
                classifiers={"vowel": ()},
                segments=[Segment("p", "consonant")],
            )


class TestAdd:
    def test_add_valid(self) -> None:
        inv = _vowel_inventory()
        inv.add(
            Segment(
                symbol="u",
                type="vowel",
                classification={
                    "height": Value("close"),
                    "backness": Value("back"),
                    "roundness": Value("rounded"),
                },
            )
        )
        assert len(inv) == 1
        assert "u" in inv
        assert inv.segments == (Segment(
            symbol="u",
            type="vowel",
            classification={
                "height": Value("close"),
                "backness": Value("back"),
                "roundness": Value("rounded"),
            },
        ),)

    def test_add_unknown_type(self) -> None:
        inv = _vowel_inventory()
        with pytest.raises(ValueError, match="not in"):
            inv.add(Segment(symbol="p", type="consonant"))

    def test_add_undeclared_classifier(self) -> None:
        inv = _vowel_inventory()
        with pytest.raises(ValueError, match="not declared"):
            inv.add(
                Segment(
                    symbol="u",
                    type="vowel",
                    classification={"nasality": Value("nasal")},
                )
            )

    def test_add_duplicate_symbol(self) -> None:
        inv = _vowel_inventory()
        inv.add(Segment(symbol="u", type="vowel"))
        with pytest.raises(ValueError, match="already present"):
            inv.add(Segment(symbol="u", type="vowel"))

    def test_value_set_validation(self) -> None:
        inv = SegmentInventory(
            id="toy",
            types=("vowel",),
            classifiers={"vowel": ("height",)},
            value_sets={
                "height": ValueSet(
                    "height",
                    values=(Value("close"), Value("open")),
                )
            },
        )
        inv.add(
            Segment(
                "u",
                "vowel",
                classification={"height": Value("close")},
            )
        )
        with pytest.raises(ValueError, match="not in ValueSet"):
            inv.add(
                Segment(
                    "a",
                    "vowel",
                    classification={"height": Value("mid")},
                )
            )


class TestAccess:
    def test_getitem(self) -> None:
        inv = _vowel_inventory()
        seg = Segment(symbol="u", type="vowel")
        inv.add(seg)
        assert inv["u"] == seg

    def test_getitem_missing(self) -> None:
        inv = _vowel_inventory()
        with pytest.raises(KeyError):
            inv["x"]

    def test_by_type(self) -> None:
        inv = SegmentInventory(
            id="toy",
            types=("vowel", "consonant"),
            classifiers={"vowel": (), "consonant": ()},
        )
        inv.add(Segment(symbol="u", type="vowel"))
        inv.add(Segment(symbol="p", type="consonant"))
        inv.add(Segment(symbol="i", type="vowel"))
        assert [s.symbol for s in inv.by_type("vowel")] == ["u", "i"]
        assert [s.symbol for s in inv.by_type("consonant")] == ["p"]


class TestDerivations:
    def test_uses_classification_false_when_empty(self) -> None:
        inv = _vowel_inventory()
        inv.add(Segment(symbol="u", type="vowel"))
        assert inv.uses_classification() is False

    def test_uses_classification_true(self) -> None:
        inv = _vowel_inventory()
        inv.add(
            Segment(
                symbol="u",
                type="vowel",
                classification={"height": Value("close")},
            )
        )
        assert inv.uses_classification() is True

    def test_uses_values_false_when_empty(self) -> None:
        inv = _vowel_inventory()
        inv.add(Segment(symbol="u", type="vowel"))
        assert inv.uses_values() is False

    def test_uses_values_true(self) -> None:
        inv = _vowel_inventory()
        inv.add(
            Segment(
                symbol="u",
                type="vowel",
                values={"voice": Value("+")},
            )
        )
        assert inv.uses_values() is True


class TestMembership:
    def test_contains_by_symbol(self) -> None:
        inv = _vowel_inventory()
        inv.add(Segment(symbol="u", type="vowel"))
        assert "u" in inv
        assert "x" not in inv

    def test_contains_by_segment(self) -> None:
        inv = _vowel_inventory()
        seg = Segment(symbol="u", type="vowel")
        inv.add(seg)
        assert seg in inv

    def test_contains_by_segment_not_present(self) -> None:
        inv = _vowel_inventory()
        seg = Segment(symbol="u", type="vowel")
        assert seg not in inv

    def test_contains_non_string_non_segment(self) -> None:
        inv = _vowel_inventory()
        assert 5 not in inv
