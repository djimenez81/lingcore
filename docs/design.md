# Design notes

Why lingcore looks the way it does. Read this if you are considering
building on lingcore, contributing to it, or just wondering why a
particular decision went the way it did.

## Why an abstract core at all?

The alternative to a separate `lingcore` package is to build the
containers inside each notation-specific package. That works fine for
one package. It fails as soon as there are two: either they share a
copy of the containers (and diverge), or they duplicate them (and
diverge). Lingcore factors out the shared structure so that
`phonfeat`, a hypothetical sign-language package, and anything else
you build all sit on the same foundation.

The design rule is: **if two packages would each have a class called
`Segment`, that class belongs in lingcore.** If they would not, it
does not.

## Why no tokenization?

Tokenization is inherently notation-specific. Splitting an IPA string
into phones requires knowing about diacritics, tie bars, and
combining codepoints. Splitting an X-SAMPA string requires knowing
about multi-character sequences and underscore-prefixed diacritics.
Splitting a sign-language notation requires something else entirely.

Lingcore has no opinion about any of this. It provides the *result*
of tokenization (a `Segment`) but not the process.

## Why no built-in feature tables?

Feature tables are large, contentious, and versioned separately from
code. PanPhon, Hayes, PHOIBLE, and any table you invent all have
different coverage, different naming conventions, and different
values. Baking any one of them into lingcore would (a) bloat the
package, (b) commit it to an external project's update cycle, and (c)
implicitly privilege one framework over others.

Instead, lingcore provides `FeatureSystem`, which is the *shape* of a
feature table, and consumers provide the table itself.

## Why are segments immutable?

Because segments are values. They have no identity beyond their
content. Two segments with the same symbol, type, classification, and
values *are the same segment*, and treating them as distinct objects
with distinct identities is a source of subtle bugs. Immutability
also makes segments hashable, which means they can be used as dict
keys and set members, which is exactly what you want when building
inventories and feature matrices.

## Why is the inventory mutable?

Because inventories are built incrementally. You start with an empty
inventory, add segments as you process a corpus, and end up with a
full one. Trying to make this functional (build a new inventory for
every addition) is awkward and slow. The compromise is: the
inventory's *schema* (`types`, `classifiers`) is frozen after
construction, but its *contents* (`segments`) grow via `add`.

Once an inventory is fully built, treat it as read-only. Lingcore
does not enforce this, but it is the intended discipline.

## Why is there both classification and values?

Because they answer different questions.

- Classification answers: *what kind of thing is this?* `height:
  close`, `manner: stop`. The vocabulary is per-inventory and free.
- Values answer: *where does this segment sit on a set of binary
  dimensions?* `voice: +`, `nasal: -`. The vocabulary is a
  `FeatureSystem`.

Some consumers only need classification (a descriptive inventory of
a language). Some only need values (an algorithm that operates on
feature matrices). Some need both (a scholarly description plus a
computational analysis). Lingcore supports all three cases.

## Why is the encoder a data field, not a hardcoded function?

Because the mapping from `Value` to float is a convention, not a
fact. PanPhon uses `+`/`-`/`0`. Someone else might use `yes`/`no`/`NA`.
Someone else might want `+` → `True`, `-` → `False`. By making the
encoder a `ValueEncoder` instance attached to a `FeatureSystem`,
lingcore does not have to take sides, and consumers can override the
convention without touching library code.

## Why is `FeatureSystem` not bound to a `SegmentInventory`?

Because a feature system is a schema, and inventories are data. The
same PanPhon feature system might apply to a dozen different
inventories. Binding them together would mean either duplicating the
system or sharing it in ways that make mutation hazardous.

Instead, lingcore provides `feature_matrix(inventory, system)` as a
free function. The binding happens at call time, not construction
time.

The cost is that a user has to pass two objects around where one
might have sufficed. The benefit is that both objects remain
independently reusable.

## Why is `metadata` so vaguely defined?

Because it is a hedge. It exists so consumers can attach
application-specific annotations without subclassing or wrapping
lingcore types. Lingcore never interprets it.

The risk is that users will put structural data in `metadata`
(frequencies, positions, features), and then the structure that
lingcore was supposed to provide has leaked back into untyped
dictionaries. To mitigate this:

- Use `metadata` only for annotations that are specific to your
  application and not structural to the linguistic model. Source
  citations, external annotation IDs, and free-form notes are
  appropriate.
- Do not use it as a substitute for a typed field. If a property is
  common enough that a second reader would expect to find it by name,
  propose adding it as a first-class field instead.

## Why NumPy and not pure Python?

Because feature matrices are the common case, and feature matrices
want NumPy. It is a heavy dependency, but it is already a transitive
dependency of most scientific Python, and the alternatives (lists of
lists, a custom matrix class) are worse in every measurable way.

`pandas` is not a hard dependency because it is a much heavier one.
It is only needed for `FeatureMatrix.to_dataframe()`, which is a
convenience.

## Why `NaN` for undefined?

Because a feature matrix has to represent three states per cell:
positive, negative, and undefined. A binary float array can represent
two. NaN is the conventional third state in numeric Python, and it
composes well with NumPy's handling of missing data (any arithmetic
involving NaN produces NaN, comparisons produce False, and so on).

The cost is that `NaN != NaN`, which breaks equality of any container
holding it. We address this by giving `ValueEncoder` a custom
`__eq__` that treats two NaNs as equal, and by hashing
`FeatureSystem` over fields that never contain NaN.

## Why does `FeatureSystem` hash only `(name, version, features)`?

Because `encoder` contains NaN, which hashes inconsistently across
Python versions, and `metadata` is opaque and may contain anything.
Hashing only the schema-defining fields is consistent with the Python
hash contract (equal objects hash equal) because two systems that are
`==` necessarily agree on name, version, and features.

Two systems that differ only in `encoder` or `metadata` are unequal
but hash equal. That is permitted: unequal objects may share a hash.
The contract only forbids equal objects from hashing differently.

## Why is `ValueEncoder` unhashable?

Because its values include `float('nan')`, and NaN has no stable hash.
Rather than paper over this with a sentinel (which is what
`float('nan') is float('nan')` tricks do), we declare the type
unhashable and rely on equality by content.

If a future use case needs hashing, the right fix is to store the
encoder's mapping as a tuple of `(key, encoded_value)` pairs where
the encoded value for "undefined" is a stable sentinel. That is a
larger change and not warranted at v0.1.

## Why is `Segment.__hash__` explicit?

Because the dataclass-generated `__hash__` would hash the
`classification` and `values` mappings, and `MappingProxyType`
delegates to `dict`, which is unhashable. We sort the mapping's items
into tuples and hash those. This assumes mapping keys are strings or
otherwise comparable; this is a documented assumption of the model,
not an enforced one.

If a consumer passes a `metadata` mapping with non-comparable keys,
hashing a `Segment` will raise. This is a deliberate trade-off:
enforcing "keys must be comparable" at construction time would cost
more than the rare failure mode.

## Why not use `attrs` or `pydantic`?

Because the model is small, the constraint set is stable, and neither
library provides enough benefit to justify a dependency. Dataclasses
plus explicit `__post_init__` hooks are enough. If the model grows
substantially — say, if we add validation of `ValueSet` membership at
segment construction, or a schema registry — we might reconsider.

## Why Python 3.12+?

Because that is what the author uses, and because the syntax we rely
on (PEP 604 `X | Y` unions, PEP 585 `tuple[...]` generics, PEP 634
`match` statements if we add them) is available without
`from __future__ import annotations` gymnastics. Relaxing to an
earlier version later is possible but not a priority.

## Why GPL-3.0-or-later?

Because the author wants the library and its derivatives to remain
free software. GPL-3.0-or-later is the modern strong-copyleft
default, and it is compatible with the licenses of the data sources
(PanPhon, Hayes, and similar) that downstream packages like `phonfeat`
will ingest.

Consumers who need a more permissive license can ask; the author is
the sole copyright holder and can relicense on a case-by-case basis.
