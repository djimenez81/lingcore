# Project summary

## What lingcore is

`lingcore` is a small library of abstract linguistic data structures
for Python. It provides the *containers* that linguistic tooling
needs — segments, inventories, features, feature systems, matrices —
without committing to any particular notation, language, or feature
framework.

The name reflects the goal: *ling-* for linguistics, *-core* because
it is meant to be the shared foundation beneath more specific
packages.

## What lingcore is not

`lingcore` deliberately excludes:

- **Notation.** No IPA, no X-SAMPA, no Unicode knowledge. A segment's
  `symbol` is an opaque string as far as lingcore is concerned.
- **Feature tables.** No PanPhon, no Hayes, no PHOIBLE. Consumers
  provide their own feature systems.
- **I/O.** No YAML, no JSON, no CSV. Loading and saving are consumer
  concerns.
- **Linguistic theory beyond structure.** No phonemes, no allophony,
  no phonotaxis, no syllables, no prosody beyond what a consumer
  chooses to express as features.

These exclusions are deliberate, not oversights. They keep the
library small and reusable.

## Design principles

1. **Notation-agnostic.** lingcore knows nothing about any specific
   writing system or transcription convention.
2. **Optional description.** A `Segment` may carry classification,
   feature values, both, or neither. Consumers that only need a list
   of strings get a list of strings.
3. **Immutability where it matters.** Segments, features, values,
   feature systems, and matrices are immutable. Inventories are
   mutable during construction, then treated as fixed.
4. **No hidden state.** No global registries, no metaclasses, no
   magic. What you construct is what you get.
5. **No hard dependencies beyond NumPy.** NumPy is required for
   `FeatureMatrix`. Pandas is optional.

## Status

### Implemented in v0.1

- `Value` — a named, notation-agnostic label.
- `ValueSet` — a named collection of values.
- `Feature` — a named dimension of description.
- `FeatureKind` — binary, multi-valued, or scalar. Only binary is
  implemented.
- `FeatureSystem` — an ordered, versioned collection of features.
- `Segment` — an atomic unit of linguistic structure, with optional
  classification and values.
- `SegmentInventory` — an ordered, unique collection of segments,
  with a declared vocabulary of types and classifiers.
- `FeatureMatrix` — a read-only, NumPy-backed segments-by-features
  table, with helpers for finding distinguishing features.
- `ValueEncoder` — a configurable mapping from values to floats,
  used when materializing a feature matrix.

### Planned

The following are under consideration. They are not commitments.

- **`Phoneme` and `PhonemicInventory`.** An inventory of phonemes,
  each of which may map to one or more allophones. Requires deciding
  how to model allophony, which is the hard part.
- **Phonotactic constraints.** Predicates over sequences of
  segments. Likely a separate module or a sibling package.
- **Syllable structure.** Templates, onsets, codas. Likely a small
  addition once phonotaxis has a shape.
- **Multi-valued and scalar features.** `FeatureKind.MULTI` and
  `FeatureKind.SCALAR` are declared but not implemented. Needed for
  tone contours, sign-language handshapes, and other non-binary
  systems.
- **Serialization helpers.** `to_dict` / `from_dict` for the core
  types, so consumers don't each reinvent them.
- **Cross-system bridges.** A way to declare that feature `voice` in
  system A and feature `voiced` in system B refer to the same
  dimension.

### Not planned

- **Notation-specific tokenization.** That belongs in consumer
  packages.
- **A built-in feature table.** Consumers provide their own.
- **Network or database access.** Out of scope by design.

## Versioning

`lingcore` follows [semantic versioning](https://semver.org/) from
`0.1.0` onward. While the major version is `0`, breaking changes may
occur between minor versions; we will document them in the changelog.

## License

GPL-3.0-or-later.
