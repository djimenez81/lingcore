"""Inventories: ordered, unique collections of segments.

A :class:`SegmentInventory` declares a controlled vocabulary of types
and classifiers, and holds segments conforming to that vocabulary.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field

from ._immutable import freeze_mapping, freeze_tuple
from .segments import Segment
from .values import ValueSet

__all__ = ["SegmentInventory"]


@dataclass
class SegmentInventory:
    """An ordered, unique collection of segments.

    Parameters
    ----------
    id : str
        Identifier for this inventory.
    types : tuple of str
        The admissible segment types. Duplicates are rejected.
    classifiers : Mapping of str to tuple of str
        For each type, the classifier names that segments of that type
        may use. Types not present are treated as having no
        classifiers.
    value_sets : Mapping of str to ValueSet, optional
        For each classifier, the admissible values. Classifiers not
        present are unconstrained. Defaults to empty.
    metadata : Mapping, optional
        Free-form metadata. lingcore never interprets it. Excluded
        from equality (the inventory is not hashable).

    Notes
    -----
    The inventory is mutable: :meth:`add` appends segments. Its schema
    fields (``types``, ``classifiers``, ``value_sets``) are frozen
    after construction. Segments are stored internally keyed by
    symbol, and exposed as a read-only tuple via :attr:`segments`.
    """

    id: str
    types: tuple[str, ...]
    classifiers: Mapping[str, tuple[str, ...]]
    value_sets: Mapping[str, ValueSet] = field(default_factory=dict)
    metadata: Mapping[str, object] = field(default_factory=dict)
    _by_symbol: dict[str, Segment] = field(
        default_factory=dict, init=False, repr=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "types", freeze_tuple(self.types))
        frozen_classifiers = {
            k: freeze_tuple(v) for k, v in self.classifiers.items()
        }
        object.__setattr__(
            self,
            "classifiers",
            freeze_mapping(frozen_classifiers),
        )
        object.__setattr__(
            self, "value_sets", freeze_mapping(self.value_sets)
        )
        object.__setattr__(
            self, "metadata", freeze_mapping(self.metadata)
        )
        self._check_schema()

    def _check_schema(self) -> None:
        if len(self.types) != len(set(self.types)):
            duplicates = sorted(
                {t for t in self.types if self.types.count(t) > 1}
            )
            raise ValueError(
                f"Duplicate types in inventory {self.id!r}: "
                f"{duplicates}"
            )
        unknown_types = sorted(
            set(self.classifiers) - set(self.types)
        )
        if unknown_types:
            raise ValueError(
                f"Classifiers declared for unknown types in "
                f"inventory {self.id!r}: {unknown_types}"
            )
        declared_classifiers = {
            c for cs in self.classifiers.values() for c in cs
        }
        unknown_sets = sorted(
            set(self.value_sets) - declared_classifiers
        )
        if unknown_sets:
            raise ValueError(
                f"ValueSets declared for unknown classifiers in "
                f"inventory {self.id!r}: {unknown_sets}"
            )

    @classmethod
    def from_segments(
        cls,
        id: str,
        types: tuple[str, ...],
        classifiers: Mapping[str, tuple[str, ...]],
        segments: Sequence[Segment],
        *,
        value_sets: Mapping[str, ValueSet] | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> "SegmentInventory":
        """Construct an inventory pre-populated with ``segments``.

        Equivalent to constructing an empty inventory and calling
        :meth:`add` for each segment.

        Raises
        ------
        ValueError
            If any segment fails validation.
        """
        inv = cls(
            id=id,
            types=types,
            classifiers=classifiers,
            value_sets=value_sets or {},
            metadata=metadata or {},
        )
        for segment in segments:
            inv.add(segment)
        return inv

    @property
    def segments(self) -> tuple[Segment, ...]:
        """The segments, in insertion order, as a read-only tuple."""
        return tuple(self._by_symbol.values())

    def add(self, segment: Segment) -> None:
        """Append ``segment`` after validating conformance.

        Parameters
        ----------
        segment : Segment
            The segment to add.

        Raises
        ------
        ValueError
            If the segment's type is not in ``types``, if it uses a
            classifier not declared for its type, if it uses a
            classification value not in the corresponding
            ``ValueSet``, or if a segment with the same symbol
            already exists.
        """
        self._validate(segment)
        self._by_symbol[segment.symbol] = segment

    def _validate(self, segment: Segment) -> None:
        if segment.type not in self.types:
            raise ValueError(
                f"Segment {segment.symbol!r} has type "
                f"{segment.type!r}, not in {self.types!r}"
            )
        allowed = self.classifiers.get(segment.type, ())
        for classifier in segment.classification:
            if classifier not in allowed:
                raise ValueError(
                    f"Segment {segment.symbol!r} uses classifier "
                    f"{classifier!r}, not declared for type "
                    f"{segment.type!r}"
                )
        for classifier, value in segment.classification.items():
            value_set = self.value_sets.get(classifier)
            if value_set is not None and value not in value_set:
                raise ValueError(
                    f"Segment {segment.symbol!r} uses value "
                    f"{value.name!r} for classifier "
                    f"{classifier!r}, not in "
                    f"ValueSet {value_set.name!r}"
                )
        if segment.symbol in self._by_symbol:
            raise ValueError(
                f"Segment with symbol {segment.symbol!r} already "
                f"present in inventory {self.id!r}"
            )

    def __len__(self) -> int:
        return len(self._by_symbol)

    def __iter__(self) -> Iterator[Segment]:
        return iter(self._by_symbol.values())

    def __contains__(self, item: object) -> bool:
        if isinstance(item, Segment):
            return self._by_symbol.get(item.symbol) == item
        if isinstance(item, str):
            return item in self._by_symbol
        return False

    def __getitem__(self, symbol: str) -> Segment:
        try:
            return self._by_symbol[symbol]
        except KeyError:
            raise KeyError(symbol) from None

    def by_type(self, type_: str) -> list[Segment]:
        """Return segments of the given type."""
        return [
            s for s in self._by_symbol.values() if s.type == type_
        ]

    def uses_classification(self) -> bool:
        """Return True if any segment carries classification."""
        return any(s.classification for s in self._by_symbol.values())

    def uses_values(self) -> bool:
        """Return True if any segment carries values."""
        return any(s.values for s in self._by_symbol.values())

    def symbols(self) -> tuple[str, ...]:
        """Return segment symbols in insertion order."""
        return tuple(self._by_symbol.keys())
