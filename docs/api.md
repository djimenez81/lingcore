# API reference

Every public class and function in lingcore.

## `Value`

**Purpose.** A named, notation-agnostic label.

**Signature.**

```python
Value(
    name: str,
    description: str = "",
    aliases: tuple[str, ...] = (),
)
```

**Fields.**

| Field         | Type            | Description                                  |
|---------------|-----------------|----------------------------------------------|
| `name`        | `str`           | Canonical name, e.g. `"close"` or `"+"`.     |
| `description` | `str`           | Human-readable. Defaults to empty.           |
| `aliases`     | `tuple[str,...]`| Alternative names accepted when resolving.   |

**Methods.**

- `matches(candidate: str) -> bool` — `True` if `candidate` equals
  the canonical name or any alias.

**Notes.** Immutable and hashable. Equality by all fields. Lingcore
never interprets `name`.

---

## `ValueSet`

**Purpose.** A named, ordered collection of `Value`s. Used to declare
the admissible values for a classifier.

**Signature.**

```python
ValueSet(
    name: str,
    values: tuple[Value, ...],
    description: str = "",
)
```

**Methods.**

- `__contains__(item)` — accepts a `Value` (membership by equality)
  or a `str` (membership by name or alias).
- `resolve(name: str) -> Value` — returns the unique matching
  `Value`. Raises `KeyError` if zero or multiple values match.

---

## `Feature`

**Purpose.** A named dimension of description.

**Signature.**

```python
Feature(
    name: str,
    kind: FeatureKind = FeatureKind.BINARY,
    description: str = "",
    aliases: tuple[str, ...] = (),
)
```

**Fields.**

| Field         | Type            | Description                                        |
|---------------|-----------------|----------------------------------------------------|
| `name`        | `str`           | Canonical, e.g. `"voice"`.                         |
| `kind`        | `FeatureKind`   | `BINARY`, `MULTI`, or `SCALAR`. Only binary now.   |
| `description` | `str`           | Human-readable.                                    |
| `aliases`     | `tuple[str,...]`| Alternative names, e.g. `("voi", "voiced")`.       |

**Notes.** Immutable and hashable.

---

## `FeatureSystem`

**Purpose.** An ordered, versioned collection of features.

**Signature.**

```python
FeatureSystem(
    name: str,
    version: str,
    features: tuple[Feature, ...],
    encoder: ValueEncoder | None = None,
    metadata: Mapping[str, object] = {},
)
```

**Fields.**

| Field      | Type                | Description                                    |
|------------|---------------------|------------------------------------------------|
| `name`     | `str`               | Identifier, e.g. `"panphon"`.                  |
| `version`  | `str`               | Version string, e.g. `"0.1.0"`.                |
| `features` | `tuple[Feature,...]`| In canonical order.                            |
| `encoder`  | `ValueEncoder`      | Filled from `ValueEncoder.default()` if `None`.|
| `metadata` | `Mapping`           | Free-form. See the design notes.               |

**Methods.**

- `names() -> tuple[str, ...]` — canonical names in order.
- `index(name: str) -> int` — position of a feature by name or
  alias. Raises `KeyError` if zero or multiple match.
- `resolve(name: str) -> Feature` — the unique matching feature.
- `__contains__(name)` — `True` if a feature matches.
- `__getitem__(name)` — alias for `resolve`.
- `__iter__()` — iterates over `Feature`s in order.

**Notes.** Immutable. Equality by all fields, with NaN-tolerant
encoder comparison. Hashing is over `(name, version, features)` and
ignores `encoder` and `metadata`.

---

## `Segment`

**Purpose.** An atomic unit of linguistic structure.

**Signature.**

```python
Segment(
    symbol: str,
    type: str,
    classification: Mapping[str, Value] = {},
    values: Mapping[str, Value] = {},
    metadata: Mapping[str, object] = {},
)
```

**Fields.**

| Field            | Type                     | Description                              |
|------------------|--------------------------|------------------------------------------|
| `symbol`         | `str`                    | Notation-specific form. Opaque.          |
| `type`           | `str`                    | Drawn from the inventory's vocabulary.   |
| `classification` | `Mapping[str, Value]`     | Categorical labels by classifier.        |
| `values`         | `Mapping[str, Value]`     | Feature values by feature name.          |
| `metadata`       | `Mapping[str, object]`    | Application-specific annotations.        |

**Methods.**

- `has_classifier(name: str) -> bool`
- `value_for(name: str) -> Value | None`

**Notes.** Immutable and hashable. Equality by all fields. The
mappings are exposed as read-only views; attempting to mutate them
raises `TypeError`.

---

## `SegmentInventory`

**Purpose.** An ordered, unique collection of segments.

**Signature.**

```python
SegmentInventory(
    id: str,
    types: tuple[str, ...],
    classifiers: Mapping[str, tuple[str, ...]],
    segments: list[Segment] = [],
    metadata: Mapping[str, object] = {},
)
```

**Fields.**

| Field         | Type                            | Description                            |
|---------------|---------------------------------|----------------------------------------|
| `id`          | `str`                           | Identifier.                            |
| `types`       | `tuple[str, ...]`               | Admissible segment types.              |
| `classifiers` | `Mapping[str, tuple[str, ...]]` | Classifiers permitted per type.        |
| `segments`    | `list[Segment]`                 | The segments, in insertion order.      |
| `metadata`    | `Mapping[str, object]`          | Application-specific annotations.      |

**Methods.**

- `add(segment: Segment) -> None` — validates and appends. Raises
  `ValueError` on unknown type, undeclared classifier, or duplicate
  symbol.
- `by_type(type_: str) -> list[Segment]`
- `uses_classification() -> bool`
- `uses_values() -> bool`
- `symbols() -> tuple[str, ...]`
- `__contains__(item)` — accepts a `Segment` or a symbol string.
- `__getitem__(symbol)` — returns the segment with that symbol.
- `__iter__()`, `__len__()`

**Notes.** Mutable. `types` and `classifiers` are frozen after
construction; `segments` grows via `add`. Duplicate classification is
allowed.

---

## `FeatureMatrix`

**Purpose.** A read-only, NumPy-backed table with one row per segment
and one column per feature.

**Constructed by.** `feature_matrix(inventory, system)`.

**Fields.**

| Field           | Type                    | Description                            |
|-----------------|-------------------------|----------------------------------------|
| `segment_ids`   | `tuple[str, ...]`       | Symbols, in row order.                 |
| `feature_names` | `tuple[str, ...]`       | Feature names, in column order.        |
| `data`          | `numpy.ndarray`         | Float array of shape `(n, m)`. NaN = undefined. |

**Methods.**

- `distinguishing_features(i: int, j: int) -> list[str]` — names of
  features that differ between rows `i` and `j`, both defined.
- `pair_covers() -> dict[str, set[tuple[int, int]]]` — for each
  feature, the set of row-index pairs it distinguishes.
- `to_records() -> list[dict]` — one dict per segment.
- `to_dataframe() -> pandas.DataFrame` — requires the optional
  `pandas` dependency.

**Notes.** The underlying `data` array is marked read-only.

---

## `feature_matrix(inventory, system)`

**Purpose.** Materialize the feature matrix of an inventory under a
feature system.

**Signature.**

```python
feature_matrix(
    inventory: SegmentInventory,
    system: FeatureSystem,
) -> FeatureMatrix
```

**Notes.** The encoding from `Value` to float is determined by
`system.encoder`. See `ValueEncoder` below.

---

## `ValueEncoder`

**Import.** `from lingcore.encoding import ValueEncoder`. Not
exported at the top level.

**Purpose.** A mapping from `Value` (or `None`) to float, used when
materializing a feature matrix.

**Signature.**

```python
ValueEncoder(mapping: Mapping[Value | None, float])
```

**Methods.**

- `encode(value: Value | None) -> float` — raises `ValueError` if
  the value has no entry.
- `ValueEncoder.default() -> ValueEncoder` — the standard encoder:
  `"+"` → 1.0, `"-"` → 0.0, `"0"` → NaN, `None` → NaN.

**Notes.** Immutable. Two encoders are equal iff they have the same
keys and values, treating two NaNs as equal. Unhashable.
