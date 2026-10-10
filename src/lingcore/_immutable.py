"""Internal helpers for enforcing immutability of container fields.

This module is private to lingcore. It exists so that dataclasses can
declare ``Mapping`` fields and get genuinely read-only mappings without
sprinkling ``MappingProxyType`` calls through every class.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from types import MappingProxyType
from typing import TypeVar

__all__ = ["freeze_mapping", "freeze_tuple"]

_K = TypeVar("_K")
_V = TypeVar("_V")
_T = TypeVar("_T")


def freeze_mapping(items: Mapping[_K, _V]) -> Mapping[_K, _V]:
    """Return a read-only view of ``items``.

    A shallow copy is made so that later mutation of the caller's
    original mapping does not leak through. Nested mappings are *not*
    recursively frozen; callers that need nested immutability should
    freeze inner mappings themselves before calling this function.

    Parameters
    ----------
    items : Mapping
        The mapping to freeze.

    Returns
    -------
    Mapping
        A read-only, hashable-if-contents-are-hashable view.
    """
    return MappingProxyType(dict(items))


def freeze_tuple(items: Iterable[_T]) -> tuple[_T, ...]:
    """Return a tuple of ``items``.

    Trivial when ``items`` is already a tuple; provided for symmetry
    with :func:`freeze_mapping` so dataclasses read uniformly.

    Parameters
    ----------
    items : Iterable
        The iterable to freeze.

    Returns
    -------
    tuple
        A tuple with the same elements.
    """
    return tuple(items)
