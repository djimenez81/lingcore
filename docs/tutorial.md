# Tutorial

A worked example. By the end you will have built a small inventory,
attached features to its segments, and computed a feature matrix.

## 1. Install

```
pip install lingcore
```

## 2. Define a feature system

A `FeatureSystem` is an ordered collection of features. Let us model
a small consonant system with three features.

```python
from lingcore import Feature, FeatureSystem

system = FeatureSystem(
    name="toy",
    version="0.1.0",
    features=(
        Feature("voice", description="Vocal folds vibrate."),
        Feature("nasal", description="Air flows through the nose."),
        Feature("continuant", description="Airflow not blocked."),
    ),
)
```

The order of features matters. It defines the column order of the
feature matrix we will build later.

## 3. Define an inventory

A `SegmentInventory` declares a vocabulary of types and classifiers,
then holds segments conforming to that vocabulary.

```python
from lingcore import SegmentInventory, Value

inv = SegmentInventory(
    id="toy consonants",
    types=("consonant",),
    classifiers={
        "consonant": ("manner", "place"),
    },
)
```

The inventory is currently empty. `types` says a segment may be of
type `"consonant"`. `classifiers` says a consonant may be classified
by `manner` and `place`.

## 4. Add segments

A `Segment` has a `symbol` (opaque to lingcore), a `type` (from the
vocabulary), an optional `classification`, and optional `values`.

```python
def stop(symbol, place):
    return Segment(
        symbol=symbol,
        type="consonant",
        classification={
            "manner": Value("stop"),
            "place": Value(place),
        },
        values={
            "voice": Value("-"),
            "nasal": Value("-"),
            "continuant": Value("-"),
        },
    )

inv.add(stop("p", "bilabial"))
inv.add(stop("t", "alveolar"))
inv.add(stop("k", "velar"))
```

We have added three voiceless oral stops. Note that `classification`
and `values` are independent: a consumer could use just one, or
neither.

Attempting to add a segment with an undeclared type or classifier
raises an error:

```python
inv.add(Segment(symbol="x", type="vowel"))
# ValueError: Segment 'x' has type 'vowel', not in ('consonant',)
```

## 5. Materialize a feature matrix

```python
from lingcore import feature_matrix

m = feature_matrix(inv, system)
print(m.data)
```

The result is a NumPy array with one row per segment and one column
per feature:

```
[[0. 0. 0.]
 [0. 0. 0.]
 [0. 0. 0.]]
```

All three stops are identical in this feature system, so all cells
are 0. To make them distinguishable, we would need a `place` feature
in the system.

## 6. Find distinguishing features

```python
inv.add(Segment(
    symbol="m",
    type="consonant",
    classification={
        "manner": Value("nasal"),
        "place": Value("bilabial"),
    },
    values={
        "voice": Value("+"),
        "nasal": Value("+"),
        "continuant": Value("-"),
    },
))

m = feature_matrix(inv, system)
print(m.distinguishing_features(0, 3))
# ['voice', 'nasal']
```

`distinguishing_features(i, j)` returns the names of features whose
values differ between rows `i` and `j`, and where both values are
defined.

## 7. Export

```python
for record in m.to_records():
    print(record)
```

Each record is a dict with a `symbol` key and one key per feature.
Install `lingcore[pandas]` if you want `m.to_dataframe()`.

## 8. What next

- Read the [concepts](concepts.md) for the mental model.
- Read the [API reference](api.md) for a full description of every
  class and method.
- If you want to add notation-specific behavior — tokenizing IPA,
  converting to X-SAMPA — build it on top of lingcore. See the
  design notes for why lingcore deliberately excludes this.
