"""Segments: the atoms of a lingcore model.

A :class:`Segment` has an opaque ``symbol``, a ``type`` drawn from its
inventory's vocabulary, and two optional description channels:
``classification`` (categorical labels keyed by classifier name) and
``values`` (any other label-value pairs). Neither channel is
interpreted by lingcore.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ._immutable import freeze_mapping
from .values import Value

__all__ = ["Segment"]


@dataclass(frozen=True, slots=True, eq=False)
class Segment:
    """An atomic unit of linguistic structure.

    Parameters
    ----------
    symbol : str
        The notation-specific form of the segment, e.g. an IPA string.
        lingcore treats it as opaque.
    type : str
        The kind of segment, e.g. ``"vowel"``. Must be declared in the
        owning inventory's ``types``.
    classification : Mapping of str to Value, optional
        Categorical labels keyed by classifier name. Defaults to empty.
    values : Mapping of str to Value, optional
        Feature-like values keyed by feature name. Defaults to empty.
    metadata : Mapping, optional
        Free-form metadata. lingcore never interprets it. Excluded
        from equality and hashing.

    Notes
    -----
    Instances are immutable. Two segments are equal iff their
    ``symbol``, ``type``, ``classification``, and ``values`` are
    equal; ``metadata`` is an attachment and does not participate in
    identity. Hashing follows the same rule.

    The ``metadata`` mapping is exposed as a read-only view, but its
    *values* are not frozen: a metadata value that is itself mutable
    (a list, a dict) can be mutated through the view. This is a
    documented limitation, and it is why metadata is excluded from
    hashing.
    """

    symbol: str
    type: str
    classification: Mapping[str, Value] = field(default_factory=dict)
    values: Mapping[str, Value] = field(default_factory=dict)
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "classification", freeze_mapping(self.classification)
        )
        object.__setattr__(
            self, "values", freeze_mapping(self.values)
        )
        object.__setattr__(
            self, "metadata", freeze_mapping(self.metadata)
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Segment):
            return NotImplemented
        return (
            self.symbol,
            self.type,
            self.classification,
            self.values,
        ) == (
            other.symbol,
            other.type,
            other.classification,
            other.values,
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.symbol,
                self.type,
                tuple(sorted(self.classification.items())),
                tuple(sorted(self.values.items())),
            )
        )

    def has_classifier(self, name: str) -> bool:
        """Return True if ``name`` is present in ``classification``."""
        return name in self.classification

    def value_for(self, name: str) -> Value | None:
        """Return the ``values`` entry for ``name``, or ``None``."""
        return self.values.get(name)
