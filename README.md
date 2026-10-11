# lingcore

Abstract linguistic structures for Python.

`lingcore` provides notation-agnostic building blocks for working with
linguistic data: **values**, **features**, **feature systems**,
**segments**, **segment inventories**, and **feature matrices**. It has
no hardcoded knowledge of IPA, X-SAMPA, or any particular linguistic
framework. Consumers bring their own notation and their own feature
tables; `lingcore` provides the structure.

## Why

Most phonological or phonetic tooling in Python is either tightly bound
to a specific notation (IPA, X-SAMPA) or a specific feature framework
(PanPhon, Hayes, PHOIBLE), or it reimplements the same three or four
data classes in every project. `lingcore` factors out the structure so
that notation-specific packages can be built on top of a shared,
stable foundation.

If you are building a package for IPA, a package for sign-language
phonology, or a package for a constructed language you invented last
weekend, `lingcore` gives you the containers without imposing
assumptions.

## Install

```
pip install lingcore
```

Optional extras:

- `lingcore[pandas]` — for `FeatureMatrix.to_dataframe()`.
- `lingcore[dev]` — for running the test suite.

## Quick example

```python
from lingcore import (
    Feature, FeatureSystem, Segment, SegmentInventory, Value,
    feature_matrix,
)

# Define a feature system.
system = FeatureSystem(
    name="toy",
    version="0.1.0",
    features=(Feature("voice"), Feature("nasal")),
)

# Define an inventory that uses it.
inv = SegmentInventory(
    id="toy",
    types=("consonant",),
    classifiers={"consonant": ("manner", "place")},
)

# Add segments.
inv.add(Segment(
    symbol="p",
    type="consonant",
    classification={"manner": Value("stop"), "place": Value("bilabial")},
    values={"voice": Value("-"), "nasal": Value("-")},
))
inv.add(Segment(
    symbol="m",
    type="consonant",
    classification={"manner": Value("nasal"), "place": Value("bilabial")},
    values={"voice": Value("+"), "nasal": Value("+")},
))

# Materialize a feature matrix.
m = feature_matrix(inv, system)
print(m.distinguishing_features(0, 1))
# ['voice', 'nasal']
```

## What `lingcore` is not

- Not a tokenizer. It does not know how to split an IPA string into
  phones. That is the job of a notation-specific package built on top.
- Not a feature table. It does not ship PanPhon or Hayes features.
  Consumers provide feature tables; `lingcore` only provides the
  containers.
- Not an I/O library. It does not read or write YAML, JSON, or CSV.
  Serialization is a consumer concern.
- Not a full linguistic framework. It has no notion of phonemes,
  allophony, phonotaxis, syllables, or prosody beyond what is
  expressed as features. Those are future work, potentially in a
  sibling package.

## Status

Alpha. The API is small and, we hope, stable, but it may change before
1.0. See [`docs/summary.md`](docs/summary.md) for a detailed
implementation status.

## Documentation

- [`docs/summary.md`](docs/summary.md) — what this project is and
  where it is going.
- [`docs/concepts.md`](docs/concepts.md) — the mental model.
- [`docs/tutorial.md`](docs/tutorial.md) — a worked example.
- [`docs/api.md`](docs/api.md) — reference.
- [`docs/design.md`](docs/design.md) — design decisions and their
  rationale.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
