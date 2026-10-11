# Concepts

This document explains the mental model behind lingcore's API. Read
it before the tutorial if you are new; read it after the tutorial if
you prefer to learn by example.

## The four axes

Lingcore models linguistic structure along four orthogonal axes:

1. **Identity** — what is this thing?
2. **Type** — what kind of thing is it?
3. **Classification** — how is it described categorically?
4. **Values** — how is it described by feature values?

Any of the last three may be absent. A minimal lingcore object is
just an identity.

## Values

A `Value` is a named label. It has a `name`, an optional
`description`, and optional `aliases`. Lingcore never interprets the
name. `Value("close")`, `Value("+")`, and `Value("handshape-A")` are
all valid and mean whatever the consumer says they mean.

Values are immutable and hashable. Two values are equal iff all their
fields are equal.

A `ValueSet` is a named, ordered collection of values. It is used to
declare the admissible values for a classifier — for example, the
set of heights a vowel may have — so inventories can validate their
contents.

## Features

A `Feature` is a named dimension of description. It has a `name`, a
`kind` (binary, multi-valued, or scalar), an optional `description`,
and optional `aliases`.

In v0.1, only binary features are implemented. A binary feature's
values are conventionally `Value("+")`, `Value("-")`, and
`Value("0")`, where `"0"` means "not applicable" rather than "false".
This three-valued convention is inherited from PanPhon.

A `FeatureSystem` is an ordered, versioned collection of features.
Order matters: it defines the column order of a `FeatureMatrix`, and
it is the tie-breaker for algorithms that iterate over features.

## Segments

A `Segment` is the atom of the model. It has:

- A `symbol`, which is an opaque string. Whatever notation the
  consumer uses, this is the notation-specific form of the segment.
- A `type`, drawn from the vocabulary declared by the owning
  inventory.
- An optional `classification`, a mapping from classifier names to
  `Value`s.
- An optional `values`, a mapping from feature names to `Value`s.
- Optional `metadata`, for application-specific annotations that are
  not structural to the linguistic model.

Segments are immutable and hashable. Equality is by all fields.

A segment's `classification` and `values` are independent. You can
have classification without values, values without classification,
both, or neither.

## Inventories

A `SegmentInventory` is an ordered, unique collection of segments. It
declares a controlled vocabulary:

- `types` — the admissible segment types.
- `classifiers` — for each type, the classifier names that segments
  of that type may use.

When you add a segment, the inventory validates that its `type` is
declared, that its `classification` uses only classifiers allowed
for that type, and that no segment with the same `symbol` is already
present.

Inventories are mutable during construction, then treated as fixed.
Duplicate classification is allowed: two segments may have the same
classification. Duplicate symbols are not allowed.

## Feature matrices

A `FeatureMatrix` binds a `SegmentInventory` to a `FeatureSystem`.
It has one row per segment and one column per feature. Cells are
floats; `NaN` means "undefined" — either the segment has no value for
that feature, or its value is `"0"`.

`FeatureMatrix` is constructed via the `feature_matrix(inventory,
system)` function. The encoding from `Value` to float is determined
by `system.encoder`, a `ValueEncoder`.

A `ValueEncoder` is a mapping from `Value` (or `None`) to float. The
default maps `Value("+")` to 1.0, `Value("-")` to 0.0, `Value("0")`
to NaN, and `None` to NaN. Consumers can supply their own encoder if
they want a different convention.

## Values vs features, classification vs values

The distinction between *classification* and *values* is the one
most likely to confuse new users.

- **Classification** is categorical: `height: close`, `manner:
  stop`. It describes what the segment *is*, in a vocabulary the
  consumer chose.
- **Values** are feature-like: `voice: +`, `nasal: -`. They describe
  the segment along a set of dimensions defined by a
  `FeatureSystem`.

A consumer can use only classification (a descriptive inventory), or
only values (a feature-annotated inventory), or both. Lingcore does
not require either.

## Why no phonemes?

Because allophony is genuinely hard, and modeling it badly is worse
than not modeling it at all. A future `Phoneme` type will need to
answer questions like: does a phoneme have features, or do its
allophones? What happens when two allophones differ in a feature
that the phoneme must have a value for? Can a phoneme have features
that are not present in any allophone? These questions have multiple
defensible answers, and we would rather defer the decision than
guess.

For now, lingcore models phonetics, not phonology. Consumers who
want phonemes can define their own convention on top of
`SegmentInventory`.
