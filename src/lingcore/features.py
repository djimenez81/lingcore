"""Features and feature systems.

A :class:`Feature` is a named dimension along which segments may be
compared. A :class:`FeatureSystem` is an ordered, versioned collection
of features.

Neither type knows anything about segments or inventories. The binding
of a system to an inventory happens in :mod:`lingcore.matrix`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum

from ._immutable import freeze_mapping, freeze_tuple

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


@dataclass(frozen=True, slots=True)
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
    """

    name: str
    kind: FeatureKind = FeatureKind.BINARY
    description: str = ""
    aliases: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "aliases", freeze_tuple(self.aliases)
        )

    def matches(self, candidate: str) -> bool:
        """Return True if ``candidate`` names this feature."""
        return candidate == self.name or candidate in self.aliases


@dataclass(frozen=True, slots=True)
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
    metadata : Mapping, optional
        Free-form metadata. lingcore never interprets it.
    """

    name: str
    version: str
    features: tuple[Feature, ...]
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "features", freeze_tuple(self.features)
        )
        object.__setattr__(
            self, "metadata", freeze_mapping(self.metadata)
        )
        names = [f.name for f in self.features]
        if len(names) != len(set(names)):
            raise ValueError(
                f"Duplicate feature names in system {self.name!r}: "
                f"{sorted({n for n in names if names.count(n) > 1})}"
            )

    def __len__(self) -> int:
        return len(self.features)

    def __iter__(self):
        return iter(self.features)

    def __contains__(self, name: object) -> bool:
        if not isinstance(name, str):
            return False
        return any(f.matches(name) for f in self.features)

    def __getitem__(self, name: str) -> Feature:
        return self.resolve(name)

    def index(self, name: str) -> int:
        """Return the position of the named feature in this system.

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
            If no feature matches, or if more than one matches.
        """
        matches = [
            (i, f)
            for i, f in enumerate(self.features)
            if f.matches(name)
        ]
        if len(matches) != 1:
            raise KeyError(
                f"{name!r} matches {len(matches)} features in "
                f"system {self.name!r}; expected exactly one"
            )
        return matches[0][0]

    def resolve(self, name: str) -> Feature:
        """Return the unique feature matching ``name``."""
        return self.features[self.index(name)]

    def names(self) -> tuple[str, ...]:
        """Return canonical feature names in order."""
        return tuple(f.name for f in self.features)
