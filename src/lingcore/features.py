"""Features and feature systems.

A :class:`Feature` is a named dimension along which segments may be
compared. A :class:`FeatureSystem` is an ordered, versioned collection
of features.

Neither type knows anything about segments or inventories. The binding
of a system to an inventory happens in :mod:`lingcore.matrix`.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from enum import Enum

from ._immutable import freeze_mapping, freeze_tuple
from .encoding import ValueEncoder

__all__ = ["Feature", "FeatureKind", "FeatureSystem"]


class FeatureKind(str, Enum):
    """The kind of a feature.

    Only :attr:`BINARY` is implemented in v0.1. The other members are
    placeholders so that consumers can branch on ``feature.kind``
    without breaking when new kinds are added.
    """

    BINARY = "binary"
    MULTI = "multi"
    SCALAR = "scalar"


@dataclass(frozen=True, slots=True, eq=False)
class Feature:
    """A named dimension of description.

    Parameters
    ----------
    name : str
        Canonical name within its system, e.g. ``"voice"``.
    kind : FeatureKind, optional
        Defaults to :attr:`FeatureKind.BINARY`.
    description : str, optional
        Human-readable explanation. Defaults to ``""``.
    aliases : tuple of str, optional
        Alternative names, e.g. ``("voi", "voiced")``.

    Notes
    -----
    Instances are immutable. Two ``Feature`` instances are equal iff
    their ``name`` and ``kind`` are the same; ``description`` and
    ``aliases`` are annotations and do not participate in identity.
    A string passed as ``aliases`` is wrapped as a single-element
    tuple.
    """

    name: str
    kind: FeatureKind = FeatureKind.BINARY
    description: str = ""
    aliases: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "aliases", freeze_tuple(self.aliases)
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Feature):
            return NotImplemented
        return (self.name, self.kind) == (other.name, other.kind)

    def __hash__(self) -> int:
        return hash((self.name, self.kind))

    def matches(self, candidate: str) -> bool:
        """Return True if ``candidate`` names this feature."""
        return candidate == self.name or candidate in self.aliases

    def all_identifiers(self) -> tuple[str, ...]:
        """Return the canonical name followed by all aliases."""
        return (self.name, *self.aliases)


@dataclass(frozen=True, slots=True, eq=False)
class FeatureSystem:
    """An ordered, versioned collection of features.

    Parameters
    ----------
    name : str
        Identifier, e.g. ``"panphon"``.
    version : str
        Version string, e.g. ``"0.1.0"``.
    features : tuple of Feature
        The features, in canonical order.
    encoder : ValueEncoder or None, optional
        The encoding used when materializing this system as a
        :class:`~lingcore.matrix.FeatureMatrix`. When ``None``
        (the default), :meth:`ValueEncoder.default` is used.
    metadata : Mapping, optional
        Free-form metadata. lingcore never interprets it.

    Notes
    -----
    Instances are immutable. Two systems are equal iff their
    ``name``, ``version``, and ``features`` are equal; ``encoder``
    and ``metadata`` are attachments and do not participate in
    identity. Hashing follows the same rule, so two systems that
    differ only in encoder or metadata are equal and hash equal.
    """

    name: str
    version: str
    features: tuple[Feature, ...]
    encoder: ValueEncoder | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "features", freeze_tuple(self.features)
        )
        object.__setattr__(
            self, "metadata", freeze_mapping(self.metadata)
        )
        if self.encoder is None:
            object.__setattr__(
                self, "encoder", ValueEncoder.default()
            )
        self._check_unique_identifiers()

    def _check_unique_identifiers(self) -> None:
        seen: dict[str, str] = {}
        for feature in self.features:
            for identifier in feature.all_identifiers():
                if identifier in seen:
                    raise ValueError(
                        f"Identifier {identifier!r} is used by "
                        f"both {seen[identifier]!r} and "
                        f"{feature.name!r} in system {self.name!r}"
                    )
                seen[identifier] = feature.name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FeatureSystem):
            return NotImplemented
        return (
            self.name,
            self.version,
            self.features,
        ) == (
            other.name,
            other.version,
            other.features,
        )

    def __hash__(self) -> int:
        return hash((self.name, self.version, self.features))

    def __len__(self) -> int:
        return len(self.features)

    def __iter__(self) -> Iterator[Feature]:
        return iter(self.features)

    def __contains__(self, name: object) -> bool:
        if not isinstance(name, str):
            return False
        return any(f.matches(name) for f in self.features)

    def __getitem__(self, name: str) -> Feature:
        return self.resolve(name)

    def index(self, name: str) -> int:
        """Return the position of the named feature in this system.

        Because :meth:`__post_init__` rejects identifier collisions,
        at most one feature can match any given string. This method
        therefore returns a unique index or raises ``KeyError``.

        Parameters
        ----------
        name : str
            Canonical name or alias of the feature.

        Returns
        -------
        int
            Zero-based index into ``self.features``.

        Raises
        ------
        KeyError
            If no feature matches.
        """
        for i, f in enumerate(self.features):
            if f.matches(name):
                return i
        raise KeyError(
            f"No feature matching {name!r} in system {self.name!r}"
        )

    def resolve(self, name: str) -> Feature:
        """Return the unique feature matching ``name``.

        Raises
        ------
        KeyError
            If no feature matches.
        """
        return self.features[self.index(name)]

    def names(self) -> tuple[str, ...]:
        """Return canonical feature names in order."""
        return tuple(f.name for f in self.features)
