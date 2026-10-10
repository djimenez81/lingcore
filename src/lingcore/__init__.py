"""lingcore: abstract linguistic structures.

lingcore provides notation-agnostic building blocks for linguistic
data: values, features, feature systems, segments, segment
inventories, and feature matrices. It has no hardcoded knowledge of
any particular notation, language, or feature framework.

Public API
----------
Values:
    :class:`Value`, :class:`ValueSet`

Features:
    :class:`Feature`, :class:`FeatureKind`, :class:`FeatureSystem`

Segments:
    :class:`Segment`

Inventories:
    :class:`SegmentInventory`

Matrices:
    :class:`FeatureMatrix`, :func:`feature_matrix`
"""

from .features import Feature, FeatureKind, FeatureSystem
from .inventories import SegmentInventory
from .matrix import FeatureMatrix, feature_matrix
from .segments import Segment
from .values import Value, ValueSet

__version__ = "0.1.0"

__all__ = [
    "Feature",
    "FeatureKind",
    "FeatureMatrix",
    "FeatureSystem",
    "Segment",
    "SegmentInventory",
    "Value",
    "ValueSet",
    "feature_matrix",
    "__version__",
]
