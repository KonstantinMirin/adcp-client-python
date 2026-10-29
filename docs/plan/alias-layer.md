# The alias layer: letting a downstream application keep its import spellings

Downstream applications import types from the upstream distribution today. For the classes
underneath to become ours without every one of those applications editing every import,
something has to bind the spelling they already use to the class we emit.

This document decides **nothing**. `docs/plan/rebuild-plan.md` decides the semantics and
`docs/plan/architecture.md` decides the structure; §6 here states the one sentence §1 would
need, as a numbered request, in the idiom `docs/plan/builder-layer.md` uses. **No code is
written for this document yet, by design**: §1's "one import path per class" is a rule the
compiler is built around, and a compatibility surface that contradicts it has to be
reconciled in §1 before it is emitted, not bolted beside it.

Every figure names the population it is over. The reference distribution is
`v9.2.0` at `/srv/ws/wt-v92`, read read-only, whose `src/adcp/ADCP_VERSION` is `3.2.4` and
whose `schemas/cache/3.2` is **byte-identical to ours** (`diff -rq`, 1,625 files, no
differences). So both sides generate from the same documents and a spelling question has an
answer.

---

## 1. What a consumer actually imports today

Measured by importing `v9.2.0`'s own tree in a child process (`tools/parity/extract.py`,
which exists because both distributions are packages named `adcp` and one interpreter
resolves only one of them):

| | count |
| --- | --- |
| `adcp.__all__` | 746 |
| `adcp.types.__all__` | 939 |
| union of the two | **1,195** |
| of those, names that resolve to a pydantic model or an enum | 849 |
| of those 849, declared in `types/domains/**` — the bundle-3.2 layer | 777 |
| of those 849, declared in a hand-written layer | 71 |
| public names that are **not** the declaring class's own name | **317** |

The last row is the finding that shapes the whole design. **Their public surface is already
an alias layer**, and it already does the thing §1 forbids:

```python
AccountIdReference        -> domains.core.account_ref.AccountReference1
AccountReferenceById      -> domains.core.account_ref.AccountReference1   # the same class
AccountReferenceByNaturalKey -> domains.core.account_ref.AccountReference2
AcquireRightsAcquiredResponse -> domains.brand.acquire_rights_response.AcquireRightsResponse1
AcquireRightsPendingResponse  -> ...AcquireRightsResponse2
AcquireRightsErrorResponse    -> ...AcquireRightsResponse4
```

Two public names bind one class in the first pair. So the compatibility requirement is not
"map 1,195 names onto 1,195 classes"; it is "map 1,195 names onto a smaller set of classes,
with synonyms", and the synonyms are the part §1 has to be reconciled with rather than the
renames.

The 317 also say WHY the aliases exist: `AccountReference1` is the positional name
`datamodel-code-generator` produced, and `AccountReferenceById` is the name a human wanted.
Our §4 derives the second kind directly, which is what makes the mapping tractable.

## 2. How many of those spellings have a class of ours to bind to

Matched by document plus a derived node identity — never by name, because §4's naming rules
changed deliberately. The document comes from each side's own provenance
(`__adcp_schema__` for ours, the `# filename:` header for theirs); the identity is the
member VALUE set for an enum, the wire field-name set for a model, the root's shape for a
root model.

| of the 849 public class spellings | count |
| --- | --- |
| a class of ours in the SAME document with the same node identity | **740** |
| a class of ours in another document — theirs inlined a `$ref` target | 12 |
| not the bundle-3.2 layer at all (`registry.py` from `registry-openapi.yaml`, `canonical_creative.py`, `core.py`, `projections.py`) | 71 |
| no counterpart by identity | **25** |
| unresolvable record | 1 |

**752 of the 778 bundle-derived public spellings already have a class of ours to bind.**
The 25 are listed in §5 and most of them are an artefact of their generator rather than a
node we do not represent — §5 proves one of them against `Draft7Validator`.

A second number bounds the work: 148 of the 1,195 public names could not even be resolved
in this environment, because reaching them imports `adcp.client`, which needs the `a2a`
extra. A compatibility surface should not have that property; see §6.

## 3. The shape, and the three candidates

### 3a. One module per domain, re-exporting with the legacy spelling

```python
# adcp/types/compat/v9.py
from adcp.types._schemas.core.account_ref import AccountReferenceById as AccountReference1
AccountIdReference = AccountReferenceById
```

Cheap and explicit. Its problem is that it is 1,195 hand-maintained lines whose correctness
nothing grades, which is the thing this compiler exists not to do.

### 3b. A generated mapping, keyed on (document, node identity)

The map is DERIVED: for each public name of the reference distribution, resolve its
declaring class to a (document, identity) pair and emit a binding to the class of ours with
that pair. §2's measurement IS this derivation, so the artefact is a run of
`tools/parity/audit.py` rather than a new idea, and the 25 unmatched entries are the
map's declared holes rather than silent omissions.

This is the recommended shape. It has the property every other generated artefact here has:
drop in a new reference version, regenerate, and the map is correct or it names what it
could not resolve.

### 3c. A module `__getattr__` that resolves lazily

`v9.2.0` does this already (`adcp/__init__.py`'s `__getattr__` reaching an import table),
which is how it keeps `import adcp` cheap over 1,195 names. Worth copying for the cost, not
for the structure: a lazy binding is still a second name for the class, so it changes
nothing about §1.

## 4. What §1 forbids, exactly, and why a carve-out is needed rather than an exception

§1 says:

> There is **one import path per class**, and never a second way to reach the same class.
> Two spellings for one class is two things to keep in agreement, and it makes a reader
> unable to tell from the import which document a class came from. The one path is the
> domain surface's.

An alias layer is a second way to reach the same class, for 1,195 names. The two reasons
§1 gives are the two things a carve-out has to answer:

* *"two things to keep in agreement"* — answered by DERIVING the map (§3b). A generated
  binding cannot drift from the class it binds, because it is emitted from the same run.
* *"a reader cannot tell which document a class came from"* — answered by CONFINEMENT. If
  every legacy spelling lives under one import root and nothing inside the tree imports
  from it, then a reader seeing `adcp.types.compat.v9.AccountIdReference` knows exactly
  what they are looking at: a compatibility spelling, resolvable to a domain path. A reader
  seeing a domain import still gets §1's guarantee unweakened.

§1 already has a carve-out of this kind and it is the precedent: "A second name bound to a
class by identity (§4, two nodes of identical content) is that class and not a second one:
`X is Y` holds, and the surface exports it once." The alias layer wants the same sentence
with `is` holding and the DOMAIN surface still exporting once — the compat module exports
the second spelling, and the domain surface does not.

## 5. The 25 spellings with no counterpart, and one of them measured

Grouped by what they are:

| group | count | what it is |
| --- | --- | --- |
| a nested model carrying `adcp_version` / `adcp_major_version` | 11 | the version envelope injected into a node the document does not put it on |
| two public names on one of their classes | 4 | e.g. `GetContentStandardsResponse1` and `GetContentStandardsSuccessResponse` |
| a `RootModel` whose root we represent as a base plus branches or as an alias | 4 | `DaastAsset`, `VastAsset`, `SignalPricingOption`, `FrequencyCapScope` |
| a node whose field set differs for another reason | 6 | `MediaBuyFeatures`, `ProductCard`, `ReportingWebhook`, `IdentityMatchTmpxMacro`, `BuildCreativeCreative`, `SyncCatalogResult` |

**The first group is not ours to bind, and it is measured rather than asserted.** Their
`Colors` is generated from `brand/get-brand-identity-response.json` at
`/oneOf/0/properties/colors`. That node declares `type`, `properties` and
`additionalProperties: true` — it says nothing about `adcp_version`. Against
`Draft7Validator` on the node, payload by payload:

| payload | the document | their `Colors` | ours |
| --- | --- | --- | --- |
| `{"primary": "#ffffff", "adcp_version": "3.2.4"}` | ACCEPTS | REFUSES — `String should match pattern '^(?:0|[1-9]\d*)\.…'` | ACCEPTS |
| `{"primary": "#ffffff", "adcp_version": "not-a-version"}` | ACCEPTS | REFUSES — same pattern | ACCEPTS |
| `{"primary": "#ffffff", "adcp_major_version": "banana"}` | ACCEPTS | REFUSES — `Input should be a valid integer` | ACCEPTS |

So their nested model is **narrower than the document**: it refuses three payloads the
document admits, because the envelope's fields were injected into a node that is not the
envelope. Ours admits all three. A compat binding for `Colors` would therefore bind a
spelling to a class that does not behave as the old one did — which is the right answer,
but it has to be DECLARED as a behaviour change and not shipped as a silent repoint. That
is the one place the map needs an annotation beyond the binding.

This is one node proven, not a verdict on their generator. The other ten in the group look
identical in shape and none of them has been measured.

## 6. The request to `docs/plan/rebuild-plan.md` §1

**Request 1 — a confined compatibility surface, stated as a carve-out from "one import
path per class".** Add after §1's existing identity carve-out:

> **A COMPATIBILITY spelling is not a second import path, under three conditions.** A
> prior distribution's public name may be bound to the class this compiler emits for the
> same node, provided (a) the binding is GENERATED from the same run that emits the class,
> so the two cannot drift; (b) every such binding lives under one import root reserved for
> it, and no module of this distribution imports from that root, so the domain surface
> stays the only path any of our own code or any new application takes; and (c) a name
> whose class does not accept what the prior one accepted is bound with that difference
> DECLARED, in the same idiom §2 declares an approximation — a spelling that silently
> changes what a payload validates against is the one thing this surface may not do.
>
> The reasons §1 gives for the rule are what the conditions answer: (a) answers "two things
> to keep in agreement", (b) answers "a reader cannot tell which document a class came
> from", and (c) is the reason a compatibility surface is a semantics question at all and
> not packaging.

**Request 2 — the surface is importable without an optional dependency.** 148 of the
reference distribution's 1,195 public names cannot be resolved without the `a2a` extra,
because reaching them imports its client. §1 should say that the compatibility root
imports nothing but the emitted tree, so a consumer who only wants types never installs a
transport.

Neither request is acted on in this document, and no code is emitted for the layer until
§1 carries them.
