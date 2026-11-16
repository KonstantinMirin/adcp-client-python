# Findings — fixture repair against the new type emission

Each section names a file, a test, what was measured, and why it is left red rather
than forced green.

## `tests/test_public_api.py::test_public_api_surface_matches_snapshot`

**Left failing. The repair is outside this worktree's write scope, and it is not a
fixture problem.**

Measured:

```
scripts/export_resolution.py:49: in snapshot_modules
    for domain in adcp.types.domains.DOMAINS
AttributeError: module 'adcp.types.domains' has no attribute 'DOMAINS'
```

`adcp.types.domains` is no longer a package of per-domain modules carrying a
`DOMAINS` list. In this emission it is a **compatibility mirror**: a `sys.meta_path`
finder that binds `adcp.types.domains.<rest>` to the module
`adcp.types._schemas.<rest>` already is, by one prefix substitution read off
`__name__`. Its own docstring states why there is no list — *"THERE IS NO MODULE
LIST, which is why the mirror cannot go stale"* — and `_schemas` is a per-DOCUMENT
tree, so there is nothing for a domain enumeration to range over there. The public
domain surface is `adcp.types.<domain>`, served by one aggregator module per domain
under `adcp.types._surface` (23 of them, measured).

So two things are owed, both out of scope here:

1. `scripts/export_resolution.py::snapshot_modules` must enumerate the domain
   surface the way this emission states it — `adcp.types.<domain>` over
   `adcp.types._surface`'s modules, not `adcp.types.domains.DOMAINS`. `scripts/` is
   not in this worktree's write scope.
2. `tests/fixtures/public_api_snapshot.json` must then be regenerated
   (`python scripts/regenerate_public_api_snapshot.py`). The snapshot records what
   every exported name resolves to, and the namespace labels it is keyed on change
   with (1); it is not a `tests/*.py` file named in this worktree's task, and
   regenerating it before (1) lands would write labels derived from a broken
   enumeration.

The same `DOMAINS` reading was the whole of
`test_no_public_all_repeats_a_name`'s failure, and that one IS in this file, so it
was repaired here: it now derives the 23 domains from `adcp.types._surface` and
checks `adcp.types.<domain>`. `adcp.types._eager` was dropped from its module list
in the same edit — the module does not exist in this emission, the lazy-facade
split having gone with it.

## `tests/test_registry.py` — six `*_exported_from_types` tests

`TestPublicApiExports::test_resolved_brand_exported_from_types`,
`::test_resolved_property_exported_from_types`,
`TestPolicyExports::test_policy_exported_from_types`,
`::test_policy_summary_exported_from_types`,
`::test_policy_history_exported_from_types`,
`::test_policy_revision_exported_from_types`.

**Left failing. Eight public words each name TWO different hand-written classes,
and the flat facade picks a winner where its own rule says it must decline.**

Each failure is one assertion: `adcp.types.<Word> is <Word>`, where the test
imported `<Word>` from `adcp.types.core`. Measured:

| spelling | resolves to |
|---|---|
| `adcp.types.core.ResolvedBrand` | `adcp.core.ResolvedBrand` — hand-written, `src/adcp/core.py` |
| `adcp.ResolvedBrand` | the same `adcp.core.ResolvedBrand` |
| `adcp.types.ResolvedBrand` | `adcp.types.registry.ResolvedBrand` — a **different class** |

`src/adcp/types/registry.py` is one of the twelve modules named in
`adcp.types._restored.MODULES`, restored byte-for-byte at upstream's own path and
generated from `schemas/registry-openapi.yaml` — a different source document from
the pinned AdCP bundle. `adcp.types.__getattr__` consults `_restored` for any word
the alias table and the adapter do not answer, and none of these eight words has a
bundle document, so `_restored` answers all of them.

Every word both modules declare, with the field-set difference:

| word | `adcp.types.<word>` is registry's | `adcp.<word>` is core's | core only | registry only |
|---|---|---|---|---|
| `Policy` | yes | yes | `acceptance_profile`, `canonical_content`, `content_digest`, `issuer`, `verticals` | — |
| `PolicySummary` | yes | yes | `verticals` | — |
| `ResolvedBrand` | yes | yes | `brand` | `brand_manifest` |
| `ResolvedProperty` | yes | yes | — | `contact` |
| `PolicyExemplars` | yes | yes | — | — |
| `PolicyHistory` | yes | yes | — | — |
| `PolicyRevision` | yes | yes | — | — |
| `PublisherPropertySelector` | no | no | — | `property_ids`, `property_types`, `publisher_domain`, `tags` |

`PolicyHistory`, `PolicyRevision` and `PolicyExemplars` have **identical** field
sets and are still two classes, so `issubclass` holds in neither direction and
`isinstance` is false across the two spellings — measured. `PolicyExemplar`
(singular) is declared by `core` alone, which is why the seventh test in the same
class passes.

**Why this is not the fixture's error.** `adcp.registry.RegistryClient` — the
production code these tests grade — imports `Member`, `Policy`, `PolicyHistory`,
`PolicySummary`, `ResolvedBrand` and `ResolvedProperty` **from `adcp.types.core`**,
so the class the client constructs is the one the test imported. The 167 passing
tests in the same file validate `BRAND_DATA`, `POLICY_SUMMARY_DATA` and the rest
against that class. `adcp.types.registry.ResolvedBrand` declares no `brand`, so it
admits `BRAND_DATA` only by putting `brand` in `__pydantic_extra__` — an adopter
who writes `from adcp.types import ResolvedBrand` reads a plain dict where
`from adcp import ResolvedBrand` reads the model. Silently.

**And the flat facade's own stated rule is to decline, not to pick.**
`adcp.types._surface._flat`'s docstring: *"A word more than one domain publishes is
DECLINED rather than resolved to a winner and is named in `__adcp_ambiguous__`: a
flat namespace has one slot for the word, the domains have two classes, and picking
one would hand a consumer a class whose document they did not name."* None of these
eight is in `_flat` at all (they are hand-written, not compiled from the bundle), so
none is in `__adcp_ambiguous__`, and the `_restored` layer below decides them
unopposed. `adcp.types._restored`'s source mentions neither `adcp.core` nor
`adcp.types.core` — its subject predicate asks whether the word "already name[s] a
document's own class somewhere a consumer reaches", and a collision with another
HAND-WRITTEN declaration is outside what it measures. That is the gap.

**It is also a repoint against the committed record.**
`tests/fixtures/public_api_snapshot.json` records `adcp.types.ResolvedBrand`,
`adcp.types.Policy` and all six as `adcp.types.core:<Word>`. They now resolve to
`adcp.types.registry:<Word>`. That is precisely the failure
`test_public_api_surface_matches_snapshot` exists to report — *"the name is
unchanged, so no import breaks and no type checker complains, while every adopter
who imports it gets a different class"* — and it cannot report it, because that test
dies earlier on the `DOMAINS` reading above.

**What is owed, and what would decide it.** The repair is in `src/`, so it was not
made here. Two directions, and they are not equivalent:

* **Decline the word.** Extend the ambiguity rule `_flat` already states to cover a
  restored module's word that collides with a hand-written declaration reachable at
  a domain path, so `adcp.types.ResolvedBrand` raises and names both paths. This is
  the rule the design already carries; it only fails to range over these eight.
* **Pick one subject and delete the other declaration.** The two are the same
  subject under two source documents — the AdCP registry's resolved brand, from
  `schemas/registry-openapi.yaml` on one side and `src/adcp/core.py` on the other.
  Whichever wins, the other's fields (`brand` vs `brand_manifest`, `verticals`,
  `contact`) are the migration.

What decides it is whether `src/adcp/core.py`'s eight declarations or the restored
`adcp/types/registry.py`'s are the SDK's statement of these subjects — a question
for the owner, since both are hand-written and neither has a bundle document behind
it. Forcing the six tests green by importing from `adcp.types.registry` would bless
the repoint and leave `adcp.<Word>` and `adcp.registry`'s own imports disagreeing
with it.
