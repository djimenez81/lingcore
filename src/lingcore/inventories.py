"""Inventories: ordered, unique collections of segments.

An :class:`SegmentInventory` declares a controlled vocabulary of types
and classifiers, and holds segments conforming to that vocabulary.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field

from ._immutable import freeze_mapping, freeze_tuple
from .segments import Segment

__all__ = ["SegmentInventory"]


@dataclass
class SegmentInventory:
    """An ordered, unique collection of segments.

    Parameters
    ----------
    id : str
        Identifier for this inventory.
    types : tuple of str
        The admissible segment types.
    classifiers : Mapping of str to tuple of str
        For each type, the classifier names that segments of that type
        may use. Types not present are treated as having no
        classifiers.
    segments : list of Segment, optional
        Initial segments. Defaults to empty.
    metadata : Mapping, optional
        Free-form metadata. lingcore never interprets it.

    Notes
    -----
    The inventory is mutable: :meth:`add` appends segments. Its schema
    fields (``types``, ``classifiers``) are immutable after
    construction.
    """

    id: str
    types: tuple[str, ...]
    classifiers: Mapping[str, tuple[str, ...]]
    segments: list[Segment] = field(default_factory=list)
    metadata: Mapping[str, object] = field(default_factory=dict)

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
            self, "metadata", freeze_mapping(self.metadata)
        )
        # Re-validate any pre-supplied segments.
        initial = list(self.segments)
        self.segments = []
        for seg in initial:
            self.add(seg)

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
            classifier not declared for its type, or if a segment with
            the same symbol already exists.
        """
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
        if any(s.symbol == segment.symbol for s in self.segments):
            raise ValueError(
                f"Segment with symbol {segment.symbol!r} already "
                f"present in inventory {self.id!r}"
            )
        self.segments.append(segment)

    def __len__(self) -> int:
        return len(self.segments)

    def __iter__(self) -> Iterator[Segment]:
        return iter(self.segments)

    def __contains__(self, item: object) -> bool:
        if isinstance(item, Segment):
            return item in self.segments
        if isinstance(item, str):
            return any(s.symbol == item for s in self.segments)
        return False

    def __getitem__(self, symbol: str) -> Segment:
        for seg in self.segments:
            if seg.symbol == symbol:
                return seg
        raise KeyError(symbol)

    def by_type(self, type_: str) -> list[Segment]:
        """Return segments of the given type."""
        return [s for s in self.segments if s.type == type_]

    def uses_classification(self) -> bool:
        """Return True if any segment carries classification."""
        return any(s.classification for s in self.segments)

    def uses_values(self) -> bool:
        """Return True if any segment carries values."""
        return any(s.values for s in self.segments)

    def symbols(self) -> tuple[str, ...]:
        """Return segment symbols in insertion order."""
        return tuple(s.symbol for s in self.segments)
