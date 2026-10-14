"""Values: named, notation-agnostic labels.

A :class:`Value` is the smallest unit of description in lingcore. It
carries a name, an optional human-readable description, and optional
aliases. lingcore never interprets the name; consumers do. This makes
``Value`` suitable for IPA feature values, sign-language handshape
labels, or anything a consumer invents.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._immutable import freeze_tuple

__all__ = ["Value", "ValueSet"]


@dataclass(frozen=True, slots=True, eq=False)
class Value:
    """A named label attached to a segment.

    Parameters
    ----------
    name : str
        The canonical name, e.g. ``"close"`` or ``"+voice"``.
    description : str, optional
        Human-readable explanation. Defaults to ``""``.
    aliases : tuple of str, optional
        Alternative names accepted when resolving this value.
        Defaults to an empty tuple.

    Notes
    -----
    Instances are immutable. Two ``Value`` instances are equal iff
    their ``name`` is the same; ``description`` and ``aliases`` are
    annotations and do not participate in identity. Hashing is over
    ``name`` alone. A string passed as ``aliases`` is wrapped as a
    single-element tuple.
    """

    name: str
    description: str = ""
    aliases: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "aliases", freeze_tuple(self.aliases)
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Value):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def matches(self, candidate: str) -> bool:
        """Return True if ``candidate`` names this value.

        A candidate matches if it equals the canonical ``name`` or any
        element of ``aliases``.

        Parameters
        ----------
        candidate : str
            The string to check.

        Returns
        -------
        bool
            Whether the candidate is a recognized name for this value.
        """
        return candidate == self.name or candidate in self.aliases


@dataclass(frozen=True, slots=True)
class ValueSet:
    """A named, ordered collection of :class:`Value` objects.

    Used to declare the admissible values for a classifier (for
    example, the set of heights for vowels) so inventories can
    validate their contents.

    Parameters
    ----------
    name : str
        Identifier for the value set, e.g. ``"height"``.
    values : tuple of Value
        Members of the set, in a canonical order.
    description : str, optional
        Human-readable explanation. Defaults to ``""``.

    Notes
    -----
    Instances are immutable and hashable. Duplicate values (by name)
    are rejected at construction.
    """

    name: str
    values: tuple[Value, ...]
    description: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "values", freeze_tuple(self.values)
        )
        names = [v.name for v in self.values]
        if len(names) != len(set(names)):
            raise ValueError(
                f"Duplicate value names in ValueSet {self.name!r}: "
                f"{sorted({n for n in names if names.count(n) > 1})}"
            )

    def __contains__(self, value: object) -> bool:
        if isinstance(value, Value):
            return value in self.values
        if isinstance(value, str):
            return any(v.matches(value) for v in self.values)
        return False

    def __len__(self) -> int:
        return len(self.values)

    def __iter__(self):
        return iter(self.values)

    def resolve(self, name: str) -> Value:
        """Return the unique value matching ``name``.

        Parameters
        ----------
        name : str
            Canonical name or alias of the desired value.

        Returns
        -------
        Value
            The matching value.

        Raises
        ------
        KeyError
            If no value matches, or if more than one matches.
        """
        matches = [v for v in self.values if v.matches(name)]
        if len(matches) != 1:
            raise KeyError(
                f"{name!r} matches {len(matches)} values in "
                f"ValueSet {self.name!r}; expected exactly one"
            )
        return matches[0]
