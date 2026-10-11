"""Value encoders: mapping lingcore Values to numeric matrix cells.

A :class:`ValueEncoder` is a frozen mapping from a ``Value`` (or
``None``, meaning "no value present") to a float. It exists so that
the convention for encoding ``"+"``, ``"-"``, ``"0"`` and missing
values lives in *data*, not in lingcore's logic.

This module is intentionally not exported at the top level. Consumers
that need it import it as ``lingcore.encoding.ValueEncoder``.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field

from ._immutable import freeze_mapping
from .values import Value

__all__ = ["ValueEncoder"]


@dataclass(frozen=True, slots=True)
class ValueEncoder:
    """A mapping from Values (or None) to floats.

    Parameters
    ----------
    mapping : Mapping of Value or None to float
        The encoding table. Keys are ``Value`` instances, or ``None``
        to represent "no value present". Values are floats; ``NaN``
        is a legal encoding and is conventionally used to mean
        "undefined".

    Notes
    -----
    Instances are immutable. Two encoders are equal when they have
    the same keys and, for each key, values that are equal or both
    NaN. This makes two identically-constructed encoders compare
    equal even though ``nan != nan`` under IEEE 754.

    Encoders are deliberately unhashable: they contain floats,
    including NaN, and NaN hashes inconsistently across Python
    versions. Equality by content is provided; hashing is not.
    """

    mapping: Mapping[Value | None, float] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "mapping", freeze_mapping(self.mapping)
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ValueEncoder):
            return NotImplemented
        if self.mapping.keys() != other.mapping.keys():
            return False
        for key in self.mapping:
            v1 = self.mapping[key]
            v2 = other.mapping[key]
            if isinstance(v1, float) and isinstance(v2, float):
                if math.isnan(v1) and math.isnan(v2):
                    continue
            if v1 != v2:
                return False
        return True

    # Defining __eq__ sets __hash__ to None automatically; stated
    # here explicitly for readability.
    __hash__ = None  # type: ignore[assignment]

    def encode(self, value: Value | None) -> float:
        """Return the float encoding of ``value``.

        Parameters
        ----------
        value : Value or None
            The value to encode. ``None`` means "no value present".

        Returns
        -------
        float
            The encoded float.

        Raises
        ------
        ValueError
            If ``value`` has no entry in the encoding table.
        """
        try:
            return self.mapping[value]
        except KeyError as exc:
            raise ValueError(
                f"No encoding for value {value!r}"
            ) from exc

    @classmethod
    def default(cls) -> "ValueEncoder":
        """Return the default encoder.

        The default maps ``Value("+")`` to 1.0, ``Value("-")`` to 0.0,
        ``Value("0")`` to NaN, and ``None`` to NaN. This is the
        convention used by PanPhon-style and Hayes-style binary
        feature tables.

        Returns
        -------
        ValueEncoder
            A freshly constructed default encoder.
        """
        return cls(
            {
                Value("+"): 1.0,
                Value("-"): 0.0,
                Value("0"): float("nan"),
                None: float("nan"),
            }
        )
