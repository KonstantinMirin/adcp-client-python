# The 15 published names that resolve nowhere

The independent verification came back NOT CONFIRMED on types: 15 names upstream 9.6.1
publishes resolve nowhere in ours AND appear nowhere in `docs/migration-from-upstream.md`.
A published name disappeared without a row, so a consumer gets an `AttributeError` with
nothing to grep for.

This file is the decision for each of the 15 and the evidence it was decided on. Reading 10
is the rule it is decided by: **a name with no schema subject gets a migration note and
never a class.** Nothing here mints a class to satisfy an import.

## How these were read

Upstream 9.6.1 was installed to a scratch target and read **statically**, with `ast`, and
never imported — the two trees interleave `adcp/` at file granularity and cannot share an
interpreter (`survey/alias_surface.py`'s three-phase note). All 15 were located, and what
each one IS upstream is a definition and not an inference:

| upstream name | what upstream declares it as | where |
| --- | --- | --- |
| `AssetInstance` | an 11-arm union of the asset classes | `types/aliases.py` |
| `AssetInstanceType` | `Literal['image', 'video', 'audio', …]` | `types/aliases.py` |
| `FormatAssetUnion` | tagged union over `Assets`, `Assets9`, `Assets10`, … | `domains/core/format.py` |
| `GroupFormatAssetUnion` | tagged union over `Assets31`, `Assets32`, … | `domains/core/format.py` |
| `GetProductsResponseUnion` | `GetProductsResponse \| …Submitted \| …Working \| …InputRequired` | `types/_eager.py` |
| `GetSignalsResponseUnion` | `GetSignals{Success,Submitted,Working}` | `types/aliases.py` |
| `LegacyProductFormatDeclaration` | `= LegacyGeneratedProductFormatDeclaration` | `types/legacy.py` |
| `PrincipalReadResult` | 4-arm union | `types/aliases.py` |
| `PrincipalSyncResult` | 3-arm union | `types/aliases.py` |
| `CreateMediaBuySubmittedResponse` | `= _canonical_creative.CreateMediaBuyResponse3` | `types/_eager.py` |
| `GetProductsSuccessResponse` | `= GetProductsResponse` | `types/_eager.py` |
| `UpdateMediaBuyErrorResponse` | `= _canonical_creative.UpdateMediaBuyResponse2` | `types/_eager.py` |
| `UpdateMediaBuySubmittedResponse` | `= _canonical_creative.UpdateMediaBuyResponse3` | `types/_eager.py` |
| `Refine` | `Annotated[Refine1 \| Refine2 \| Refine3, discriminator='scope']` | `domains/media_buy/get_products_request.py` |
| `RefinementApplied` | `Annotated[RefinementApplied1 \| …2 \| …3, discriminator='scope']` | `domains/media_buy/get_products_response.py` |

**Every one of the 15 is an ALIAS upstream — a union, a `Literal`, or a second spelling of
one class. None is a class with a schema subject of its own.** That is what makes the
question answerable: an alias has a subject exactly when the thing it names does, so the
test is whether the members resolve in ours.

Measured over `adcp.types`:

| upstream name | members resolving in ours | verdict |
| --- | --- | --- |
| `AssetInstance` | 11 / 11 | **(a) restore** |
| `GetSignalsResponseUnion` | 3 / 3 | **(a) restore** |
| `PrincipalReadResult` | 4 / 4 | **(a) restore** |
| `PrincipalSyncResult` | 3 / 3 | **(a) restore** |
| `Refine` | 3 / 3 | **(a) restore** |
| `RefinementApplied` | 3 / 3 | **(a) restore** |
| `GetProductsSuccessResponse` | 1 / 1 | **(a) restore** |
| `CreateMediaBuySubmittedResponse` | 1 / 1 | **(a) restore** |
| `UpdateMediaBuySubmittedResponse` | 1 / 1 | **(a) restore** |
| `UpdateMediaBuyErrorResponse` | 1 / 1 | **(a) restore** |
| `AssetInstanceType` | — | **(b) row** |
| `FormatAssetUnion` | — | **(b) row** |
| `GroupFormatAssetUnion` | — | **(b) row** |
| `GetProductsResponseUnion` | 1 / 4 | **(b) row** |
| `LegacyProductFormatDeclaration` | 0 / 1 | **(b) row** |

## (a) — ten names that should resolve, and do not. A regression.

These are the alias layer's own business: every member of each one resolves in ours today,
so the subject is there and only the spelling is missing. Restoring them mints no class and
widens nothing — an alias is a NAME and never a second type, so `isinstance` holds across
every spelling of one subject (`survey/alias_destinations.py`'s own statement of the rule).

Four of them are the response aliases of the deleted `canonical_creative` layer, and the
reviewer's reading that these were "deliberate" is **half right and half wrong**: deleting
that layer was deliberate, and dropping these spellings was not a decision anybody recorded.
Each names one ARM of a response union, and the arm is still emitted — upstream's numbered
arm maps onto our named branch, confirmed against the branch list the base declares:

| upstream | upstream's target | ours |
| --- | --- | --- |
| `CreateMediaBuySubmittedResponse` | `CreateMediaBuyResponse3` (`#/oneOf/2`) | `CreateMediaBuyResponseSubmitted` |
| `UpdateMediaBuyErrorResponse` | `UpdateMediaBuyResponse2` (`#/oneOf/1`) | `UpdateMediaBuyError` |
| `UpdateMediaBuySubmittedResponse` | `UpdateMediaBuyResponse3` (`#/oneOf/2`) | `UpdateMediaBuyResponseSubmitted` |
| `GetProductsSuccessResponse` | `GetProductsResponse` | `GetProductsResponse` |

`CreateMediaBuyResponse._branch_models` is `(CreateMediaBuySuccess, CreateMediaBuyError,
CreateMediaBuyResponseSubmitted)` and `UpdateMediaBuyResponse._branch_models` is
`(UpdateMediaBuySuccess, UpdateMediaBuyError, UpdateMediaBuyResponseSubmitted)` — so the
index upstream's name carries and the branch ours declares agree, and the mapping is read
off the document's own `oneOf` order rather than guessed from the words.

## (b) — five names that are deliberately gone, and why

**`AssetInstanceType`** — upstream declares `Literal['image', 'video', 'audio', …]`, a
vocabulary it minted from the asset union's own discriminator tags. **No document states
that list as a type.** Our asset union dispatches on the tag without naming the word set,
and reading 10's rule is explicit: a name with no schema subject gets a note and never a
class. Minting the `Literal` here would be naming a concept the bundle does not name —
which is the same refusal `codegen/constraints.py` already carries for a constraint with no
document word. A caller who wants the word set reads it off the union's own tags.

**`FormatAssetUnion` and `GroupFormatAssetUnion`** — tagged unions over upstream's NUMBERED
codegen classes (`Assets`, `Assets9`, `Assets10`, … `Assets31`…). Those numbers are
`datamodel-code-generator`'s traversal order and nothing else; `CLAUDE.md` records that
adding one sibling schema renumbers the whole window. **The union has no subject because its
members have no stable identity** — a name built over `Assets31` names whatever the
generator put at position 31 on the day it ran. Ours emits the same format-asset structure
under the document's own names.

**`GetProductsResponseUnion`** — 3 of its 4 members do not resolve:
`GetProductsSubmittedResponse`, `GetProductsWorkingResponse` and
`GetProductsInputRequiredResponse`. Those are upstream's async-response spellings, and the
union cannot be restored over members that are themselves absent. The row names the
replacement for the one member that does resolve and states plainly that the other three are
a separate question — restoring the union before its members would be a name that resolves
and then fails on use, which is worse than an `AttributeError`.

**`LegacyProductFormatDeclaration`** — `= LegacyGeneratedProductFormatDeclaration`, which
does not resolve either. The legacy declaration layer is not emitted; `CLAUDE.md`'s own
record of `core/format.json` is that it is `deprecated: true` as a whole and retained for
older 3.x peers. The row says what a caller writes instead.

## What this file does not yet carry

The decisions above are complete and evidenced. **Not yet landed**: the ten restorations in
the alias layer, the five migration rows in `docs/migration-from-upstream.md`, and the
derived gate. The gate's shape is settled and recorded here so it is not re-derived:

**It ranges over upstream's published surface, read statically, and never over a list.**
`survey/alias-surface-9.6.1.tsv` is NOT that surface — its header states a population of
7,118 names and the file carries 3,300 rows, the `--deliberate-only` subset, and **11 of
these 15 are not in it**. A gate written over the committed TSV would pass today while
saying nothing about 11 of the names it exists for. The surface is upstream's own
`__init__.py` and `types/__init__.py` re-export lists, parsed with `ast` from an installed
`adcp==9.6.1` — which is how these 15 were located, and which catches the sixteenth when a
bundle moves because it reads what upstream publishes rather than what anyone wrote down.
A run with upstream absent must RAISE and not skip (`docs/plan/final-state.md`: a gate that
disappears with its own instrument reports green).
