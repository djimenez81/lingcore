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

    The returned object is a ``MappingProxyType`` over a ``dict``.
    It is read-only, but it is *not* hashable: ``MappingProxyType``
    delegates hashing to the wrapped ``dict``, and ``dict`` is
    unhashable. Callers that need a stable hash should derive one
    from the mapping's items.

    Parameters
    ----------
    items : Mapping
        The mapping to freeze.

    Returns
    -------
    Mapping
        A read-only view of a shallow copy of ``items``.
    """
    return MappingProxyType(dict(items))


def freeze_tuple(items: Iterable[_T]) -> tuple[_T, ...]:
    """Return a tuple built from ``items``.

    Strings and bytes are wrapped as single-element tuples, since
    iterating them would otherwise produce a tuple of characters or
    integers. This matches the common intent of writing
    ``aliases="voi"`` as shorthand for ``aliases=("voi",)``.

    Parameters
    ----------
    items : Iterable
        The iterable to freeze.

    Returns
    -------
    tuple
        A tuple whose elements are those of ``items``, or a
        single-element tuple if ``items`` is a string or bytes.
    """
    if isinstance(items, (str, bytes)):
        return (items,)  # type: ignore[return-value]
    return tuple(items)
