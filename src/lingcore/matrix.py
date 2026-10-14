"""Feature matrices: segments x features, materialized.

A :class:`FeatureMatrix` binds a :class:`SegmentInventory` to a
:class:`FeatureSystem` and exposes the resulting table. Undefined
values are represented by ``numpy.nan``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from .features import FeatureKind, FeatureSystem
from .inventories import SegmentInventory

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd

__all__ = ["FeatureMatrix", "feature_matrix"]


@dataclass(frozen=True, eq=False)
class FeatureMatrix:
    """A read-only segments-by-features table.

    Parameters
    ----------
    segment_ids : tuple of str
        Symbols of the segments, in row order.
    feature_names : tuple of str
        Feature names, in column order.
    data : numpy.ndarray
        Two-dimensional float array of shape
        ``(len(segment_ids), len(feature_names))``. NaN means
        undefined.

    Notes
    -----
    Constructed via :func:`feature_matrix`, not directly. Instances
    are immutable; the underlying array is copied at construction and
    marked read-only. Equality compares segment IDs, feature names,
    and cell values, treating two NaNs as equal. Hashing follows the
    same rule and is over the flattened cell values.
    """

    segment_ids: tuple[str, ...]
    feature_names: tuple[str, ...]
    data: np.ndarray

    def __post_init__(self) -> None:
        expected = (len(self.segment_ids), len(self.feature_names))
        if self.data.shape != expected:
            raise ValueError(
                f"data shape {self.data.shape} does not match "
                f"{expected}"
            )
        if not np.issubdtype(self.data.dtype, np.floating):
            raise ValueError(
                f"data must be a float array; got {self.data.dtype}"
            )
        arr = np.array(self.data, dtype=float, copy=True)
        arr.flags.writeable = False
        object.__setattr__(self, "data", arr)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FeatureMatrix):
            return NotImplemented
        return (
            self.segment_ids == other.segment_ids
            and self.feature_names == other.feature_names
            and np.array_equal(
                self.data, other.data, equal_nan=True
            )
        )

    def __hash__(self) -> int:
        flat = tuple(self.data.flatten().tolist())
        return hash(
            (self.segment_ids, self.feature_names, flat)
        )

    def distinguishing_features(
        self, i: int, j: int
    ) -> list[str]:
        """Features that distinguish rows ``i`` and ``j``.

        A feature distinguishes two rows when both values are defined
        and they differ.

        Parameters
        ----------
        i, j : int
            Row indices.

        Returns
        -------
        list of str
            Feature names, in column order.
        """
        row_i = self.data[i]
        row_j = self.data[j]
        both_defined = ~np.isnan(row_i) & ~np.isnan(row_j)
        differ = row_i != row_j
        mask = both_defined & differ
        return [
            self.feature_names[k]
            for k in range(len(self.feature_names))
            if mask[k]
        ]

    def pair_covers(self) -> dict[str, set[tuple[int, int]]]:
        """Map each feature to the set of row-index pairs it covers.

        A pair ``(i, j)`` with ``i < j`` is covered by feature ``f``
        when both rows have defined values for ``f`` and those values
        differ.

        Returns
        -------
        dict of str to set of tuple of int
            One entry per feature name, in column order.
        """
        n = len(self.segment_ids)
        covers: dict[str, set[tuple[int, int]]] = {
            name: set() for name in self.feature_names
        }
        for k, name in enumerate(self.feature_names):
            column = self.data[:, k]
            defined = ~np.isnan(column)
            for i in range(n):
                if not defined[i]:
                    continue
                for j in range(i + 1, n):
                    if not defined[j]:
                        continue
                    if column[i] != column[j]:
                        covers[name].add((i, j))
        return covers

    def to_records(self) -> list[dict[str, object]]:
        """Return one dict per segment, keyed by feature name.

        Cells are returned as floats, or ``None`` when undefined.
        The raw encoded values are preserved, so custom encoders
        (for example, one that maps ``"+"`` to ``100.0``) round-trip
        correctly.

        Returns
        -------
        list of dict
            One dict per segment, with a ``"symbol"`` key and one key
            per feature name.
        """
        records: list[dict[str, object]] = []
        for i, symbol in enumerate(self.segment_ids):
            record: dict[str, object] = {"symbol": symbol}
            for k, name in enumerate(self.feature_names):
                value = self.data[i, k]
                record[name] = (
                    None if np.isnan(value) else float(value)
                )
            records.append(record)
        return records

    def to_dataframe(self) -> "pd.DataFrame":
        """Return a pandas DataFrame with one row per segment.

        Requires the optional ``pandas`` dependency.

        Returns
        -------
        pandas.DataFrame
            Index is segment symbols; columns are feature names.
        """
        try:
            import pandas as pd
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "to_dataframe requires pandas; install lingcore "
                "with the 'pandas' extra"
            ) from exc
        return pd.DataFrame(
            self.data,
            index=list(self.segment_ids),
            columns=list(self.feature_names),
        )


def feature_matrix(
    inventory: SegmentInventory,
    system: FeatureSystem,
) -> FeatureMatrix:
    """Materialize the feature matrix of ``inventory`` under ``system``.

    Segments that lack a ``values`` entry for a given feature are
    encoded using the system's encoder, which is expected to map
    ``None`` to a suitable "undefined" marker (by default, NaN).

    Parameters
    ----------
    inventory : SegmentInventory
        The inventory whose segments form the rows.
    system : FeatureSystem
        The feature system whose features form the columns, and whose
        encoder determines the numeric encoding of each cell.

    Returns
    -------
    FeatureMatrix
        A read-only segments-by-features table.

    Raises
    ------
    NotImplementedError
        If ``system`` contains a feature whose kind is not
        ``FeatureKind.BINARY``.

    Notes
    -----
    The encoding is determined by ``system.encoder``. The default
    encoder maps ``Value("+")`` to 1.0, ``Value("-")`` to 0.0,
    ``Value("0")`` to NaN, and missing values to NaN. Any value not
    present in the encoder's mapping raises :class:`ValueError`.
    """
    for feature in system.features:
        if feature.kind is not FeatureKind.BINARY:
            raise NotImplementedError(
                f"Feature {feature.name!r} has kind "
                f"{feature.kind.value!r}; only BINARY features "
                f"are supported by feature_matrix"
            )
    encoder = system.encoder
    if encoder is None:  # pragma: no cover
        raise RuntimeError(
            f"FeatureSystem {system.name!r} has no encoder"
        )
    rows = len(inventory.segments)
    cols = len(system.features)
    data = np.full((rows, cols), np.nan, dtype=float)
    for i, segment in enumerate(inventory.segments):
        for k, feature in enumerate(system.features):
            value = segment.values.get(feature.name)
            data[i, k] = encoder.encode(value)
    return FeatureMatrix(
        segment_ids=inventory.symbols(),
        feature_names=system.names(),
        data=data,
    )
