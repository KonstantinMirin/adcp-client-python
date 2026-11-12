# Python SDK Development Learnings

## Type Safety & Code Generation

**Auto-generate from specs when possible**
- Download schemas from canonical source (e.g., adcontextprotocol.org/schemas)
- Generate Pydantic models automatically - keeps types in sync with spec
- Validate generated code in CI (syntax check + import test)

**Codegen variant numbering is unstable**
`datamodel-code-generator` numbers anonymous variant classes (e.g. `Assets162`,
`Idempotency3`, `Type11`) by traversal order. Adding or reordering even one
sibling schema shifts the entire numbering window — a clean re-run can produce
a 600+ file diff with zero semantic change. Treat any `git diff` on
`src/adcp/types/domains/` that consists of only `ClassNameN → ClassNameM`
renames as churn, not a schema delta, and discard it. `aliases.py` re-exports these
numbered classes under semantic names; accepting the renumber breaks the
alias layer for nothing.

**Import Architecture for Generated Types**
The type system has a strict layering to prevent brittleness:

```
domains/**/*.py (auto-generated from schemas; where every class is DEFINED,
                 and a public address: adcp.types.domains.<domain>.<schema>)
    ↓
_generated.py (internal consolidation)
    ↓
aliases.py + capabilities.py + _ergonomic.py + _forward_compat.py
    ↓
_eager.py (binds the full public surface; runs import-time patching)
    ↓
__init__.py (thin lazy facade; user-facing exports via PEP 562 __getattr__)
```

`adcp.types/__init__.py` is a lazy facade (PEP 562): `import adcp.types` is
cheap, and the generated Pydantic graph is built on first access to a type
symbol, by importing `_eager.py` (the former eager `__init__` body). The
runtime `__getattr__`/`__dir__` live under `if not TYPE_CHECKING:` so type
checkers see the surface only via the explicit `TYPE_CHECKING` re-export block
— a typo'd import is flagged, not silently typed as `object`.

`domains/` is where the generator writes, and that is the whole point: there
is no private tree behind the public one and no re-export tree in front of it,
so nothing is copied and nothing can drift. A domain path is a supported
import — reach for it when the flat `adcp.types` namespace cannot bind the
name you need, because several schemas declare it. The generated class NAMES
are still generator-derived, so a numbered name can renumber on a schema bump;
`aliases.py` is what gives those a stable spelling.

Only these modules may import from `_generated.py` — the one remaining
internal namespace, where a bare name resolves to a single winner (enforced by
`tests/test_import_layering.py`):
- `_generated.py`: Consolidates `domains/` exports into a flat namespace
- `_eager.py`: Eager realization of the public surface — binds every exported name and runs the import-time patchers (`_ergonomic`, `_forward_compat`)
- `aliases.py`: Creates semantic aliases for numbered discriminated union types
- `capabilities.py`: Re-exports `get_adcp_capabilities_response` sub-models with disambiguated names
- `__init__.py`: Public API surface (thin lazy facade)

All other source code should import from `adcp.types` (the public API), or from
a domain path when the name it needs is not bound there.

**Type Checking Best Practices**
- Use `TYPE_CHECKING` for optional dependencies to avoid runtime import errors
- Use `cast()` for JSON deserialization to satisfy mypy's `no-any-return` checks
- Add specific `type: ignore` comments (e.g., `# type: ignore[no-any-return]`) rather than blanket ignores
- Test type checking in CI across multiple Python versions (3.10+)

## Formats are addressed two ways, and the conversion is ONE-WAY

**`format_id` is the LEGACY (v1) way of addressing a format. `format_kind` is the NEW
(v2 canonical) way.** Both are stated by bundle 3.2 and both are live during the
migration window, so a class that carries only one of them is narrower than its
document. This has been explained more than once and mis-read more than once; the
measurements below are the record so it is not re-derived.

**The two addressing forms, with their documents:**

| | addresses a format by | document | state |
|---|---|---|---|
| v1, legacy | `format_id` — a structured `{agent_url, id}`, **not a string** | `core/format-id.json` ("Format Reference (Structured Object)", required `agent_url`, `id`) | `deprecated: true`, `x-removed-in: 4.0.0` at most sites |
| v2, canonical | `format_kind` + `params` | `core/product-format-declaration.json` (required `['format_kind', 'params']`, a 16-arm `oneOf`: "Image Format Declaration", "HTML5 Format Declaration", …) | live; what new products author |

`core/format.json` is the v1 named-format definition and is **`deprecated: true`** as a
whole. Its own description: *"DEPRECATED in 3.2. Legacy named-format definition retained
for older 3.x peers and list_creative_formats compatibility projections. New products and
creative agents author ProductFormatDeclaration canonical contracts instead."* It is
`$ref`-ed by 3 documents; `core/product-format-declaration.json` by 24.

**A CONSUMER DOES NOT PICK THE BRANCH AT A REFERENCE POSITION — PYDANTIC DOES.** Where a
document states the choice, the emission is a base plus one child per branch and the payload
selects: hand it to the base and the branch it satisfies is constructed. Measured, the bundle
states that choice at exactly **three** positions, and all three are emitted:

| node | union parent | children |
|---|---|---|
| `core/creative-asset.json#` | `CreativeAsset` | `V1CreativeNamedFormatReference` / `V2CreativeCanonicalFormatKind` |
| `core/creative-manifest.json#` | `CreativeManifest` | `NamedFormatManifest` / `CanonicalFormatManifest` |
| `creative/list-creatives-response.json#/properties/creatives/items` | `CreativesItem` | `ListedCreativeNamedFormatReference` / `ListedCreativeCanonicalFormatKind` |

Each is Case C — no discriminator keyword, the branch decided by `format_id` XOR `format_kind`
presence — and `isinstance` holds against the parent.

`core/product.json` states the same choice at the FIELD level with an `anyOf` over
`required: ['format_ids']` and `required: ['format_options']`, which we lower to
`RequiredGroups(groups=(('format_ids',), ('format_options',)), combinator='anyOf')` — and its
own text says *"Products MUST carry `format_ids`, `format_options`, or **both** during the 3.x
migration window."* Both is legal there.

**AND THERE IS NO UNION OVER THE TWO DEFINITIONS. `Format` NAMES THE CANONICAL ONE.** This
reverses an earlier reading in this file, which said `Format` was the union over both
addressing forms. That was right about REFERENCE positions, where the three unions above are,
and wrong about the two DEFINITION documents, which are not branches of one subject:

* measured, **no document states a `oneOf`/`anyOf` over `core/format.json` and
  `core/product-format-declaration.json`** — the union has no node to be emitted from;
* no field accepts "either definition", so a value built from such a union could be handed to
  nothing — every position takes a reference, a declaration, or an id;
* the only code that handles both is `canonical_formats/v1_to_v2.py`, which converts one into
  the other and so needs the distinction a parent would erase.

So the names follow the documents' own words:

| name | subject | the document's own statement |
|---|---|---|
| `adcp.types.core.Format` | the canonical declaration, `format_kind` + `params` | *"New products and creative agents author ProductFormatDeclaration canonical contracts instead"* |
| `adcp.types.core.LegacyFormat` | the v1 named-format definition | *"**DEPRECATED in 3.2.** **Legacy named-format definition** retained for older 3.x peers"* |

`LegacyFormat` is DERIVED and not an override: the document's `title` is "Format" and its
`description` calls it a "Legacy named-format definition", and both are the document's words.
`Format` on the canonical declaration is an ALIAS and not a class name, because that document
is titled "Product Format Declaration" and §4 forbids minting a public name no document
states — the alias layer is what serves a word that is not the document's, and upstream's own
public `Format` already means this subject.

**THE RENAME MUST BREAK, NOT REDIRECT.** The v1 definition is reachable only as `LegacyFormat`
after this, so code that meant v1 raises instead of silently retargeting to v2. A public word
that changes meaning while staying importable is the worst available outcome.

**AND `format_id` IS NOT ON A REMOVAL SCHEDULE, which is why `LegacyFormat` stays fully
supported.** Measured over the bundle: `format_ids` carries `x-removed-in: 4.0.0` at 13 sites;
`format_id` names a removal version at NONE — 9 sites say `deprecated: true` with no target
and **3 are not marked deprecated at all**. "Legacy" is the document's word for it, not a
shutdown date.

**THE CONVERSION IS ONE-WAY, AND THE REGISTRY SAYS SO NORMATIVELY.**
`registries/v1-canonical-mapping.json` ("v1 → v2 Canonical Format Mapping Registry"):

> **Direction of truth (normative).** This registry is authoritative for **v1 → v2
> projection only**. v2 → v1 projection MUST rely on `v1_format_ref` on the v2
> `ProductFormatDeclaration` — sellers assert the v1 mapping.

So:

* **id → kind is derivable.** The AAO-published registry maps v1 patterns to v2
  canonical declarations. The SDK does this at `src/adcp/canonical_formats/v1_to_v2.py`.
* **kind → id is NOT derivable** from the kind alone. It is only possible where the
  declaration itself carries `v1_format_ref` — an array of one or more `format_id`
  `{agent_url, id}` values, which the SELLER asserts. `src/adcp/canonical_formats/v2_to_v1.py`
  is that path, and without `v1_format_ref` there is no answer to invent.

**So never "normalise" a kind back to an id.** The mapping does not exist unless the
document carries it, and manufacturing one is inventing a format identity.

**And `deprecated` is metadata, not absence.** A document stating `format_ids` with
`deprecated: true` STATES the field; suppressing it from a class (`format_ids = None` at
class level) makes the class narrower than its document, which reading 1 forbids. Seven
documents state one of these fields as deprecated-but-present:
`core/product.json`, `core/package.json`, `core/placement.json`,
`core/product-filters.json`, `core/creative-filters.json`,
`core/creative-manifest.json`, `core/creative-asset.json`.

## Import-time model patches must defer their rebuild (#1694)

`_ergonomic`, `_forward_compat`, `canonical_creative` and `aliases` edit generated
models' `model_fields` at import. Never follow such an edit with
`model_rebuild(force=True)`: pydantic does not share nested `defer_build`
schemas between parents, so each forced rebuild of a request/response root
walks its whole subtree into pydantic-core — two dozen of them cost ~400 MiB
and 10 s at import on 9.3.0. Call `adcp.types.base.defer_model_rebuild(model)`
instead; the patched fields take effect on the model's first use.

A generated `class X(RootModel[A | B])` builds at the `RootModel[...]`
expression, before any config `X` declares. Generated composing roots
therefore parametrize `adcp.types.base.AdCPRootModel` (deferred); the
post-generate fixer does the rewrite. Every deferred SDK model also carries
`_DeferredValSer` placeholders (installed by `__pydantic_init_subclass__`) that
build on *instance* attribute access, which is how pydantic-core reaches a
serializer when it dumps by inference (`Any` field, `serialize_as_any`); a
subclass that overrides `__pydantic_init_subclass__` must call `super()`.
`tests/test_import_memory.py` imports
each entry module in a subprocess and fails when peak RSS exceeds its budget.

## ctx_metadata: write-only credentials prohibited

`RequestContext.metadata` is for non-secret request hints, not credentials. The
standard auth context factory adds framework fields and adopter-supplied principal
metadata. Buyer wire `context` is echoed separately; the framework does not project
it into `ToolContext.metadata`. An adopter's custom context factory or response code
can still expose secrets if it copies credentials into metadata or response context.

The dispatcher performs **best-effort key screening** at `_build_request_context`
as defense in depth against adopter mistakes. Passing this screen does not establish
that metadata is safe to expose or that it contains no credentials.
If you see a `ValueError` like `ctx_metadata may not contain credential-shaped
keys`, migrate the value to `AuthInfo.credential` or a typed credential class.

**Wrong** — credential stored in metadata; this key is rejected at dispatch:

```python
ctx = RequestContext(metadata={"upstream.api_token": secret})  # Rejected at dispatch
```

**Right** — credential stored in the typed `AuthInfo.credential` field:

```python
auth = AuthInfo(
    kind="api_key",
    key_id="kid_1",
    principal="agent.example.com",
    credential=ApiKeyCredential(kind="api_key", key_id="kid_1"),
)
ctx = RequestContext(auth_info=auth, metadata={"correlation_id": "req_xyz"})
```

The credential-shaped key suffix list is in
`adcp.decisioning.dispatch._CREDENTIAL_SHAPED_KEY_SUFFIXES` and matches
case-insensitively through nested dictionaries and lists: `credential`, `credentials`, `token`,
`secret`, `api_key`, `apikey`, `password`, `bearer`. Keys that don't match
(`correlation_id`, `feature_flag.beta_pricing`, `trace_id`, `tokenizer`) pass through.
This finite suffix list misses other credential names, including plural or embedded
forms such as `api_tokens` and `access_token_value`, and names such as `private_key`
and `authorization`. Other containers, including tuple values, are not traversed.
An unrecognized key or container is not permission to store a secret in metadata.

For credentials the framework propagates to upstream calls (governance agents,
signal providers, audience activations), use the typed credential classes from
`adcp.decisioning`: `ApiKeyCredential`, `OAuthCredential`, `HttpSigCredential`.
The framework dispatch threads these explicitly without going through the
context-echo path.

## Testing Strategy

**Mock at the Right Level**
- For HTTP clients: Mock `_get_client()` method, not the httpx class directly
- For async operations: Use `AsyncMock` for async functions, `MagicMock` for sync methods
- Remember: httpx's `response.json()` is SYNCHRONOUS, not async

**Test API Changes Properly**
- When API changes from kwargs to typed objects, update tests to match
- Remove tests for non-existent methods rather than keep failing tests
- Test the API as it exists, not as we wish it existed

## CI/CD & Release Automation

**GitHub Actions Secrets**
- Secret names matter! Check actual secret name in repository settings
- Guarded PyPI publishing uses environment-bound Trusted Publishing and attestations, not a static API token
- Legacy PyPI/App credentials are retired only through the separately authorized historical-run audit in `docs/releasing.md`
- Test locally with `python -m build` before relying on CI

**Release Please Workflow**
- A push to `main` opens or updates the normal Release Please PR using the GitHub App token.
- An input-free manual run on `main` bootstraps the workflow after it is re-enabled.
- Merge the reviewed release PR after CI; Release Please creates its tag and GitHub release.
- `release-publish.yml` waits for exact-commit CI, builds and checks distributions, then awaits `release-publish` environment approval before PyPI Trusted Publishing.
- Follow [docs/releasing.md](docs/releasing.md) for setup, approval, and verification.

**Entry Points for CLI Tools**
```toml
[project.scripts]
toolname = "package.__main__:main"
```
This enables `uvx toolname` and `pip install toolname` to work correctly.

## Python-Specific Patterns

**Optional Dependencies with TYPE_CHECKING**
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from optional_lib import SomeType

try:
    from optional_lib import SomeType as _SomeType
    AVAILABLE = True
except ImportError:
    AVAILABLE = False
```

**Atomic File Operations**
For config files with sensitive data:
```python
temp_file = CONFIG_FILE.with_suffix(".tmp")
with open(temp_file, "w") as f:
    json.dump(config, f, indent=2)
temp_file.replace(CONFIG_FILE)  # Atomic rename
```

**Connection Pooling**
```python
# Reuse HTTP client across requests
self._client: httpx.AsyncClient | None = None

async def _get_client(self) -> httpx.AsyncClient:
    if self._client is None:
        limits = httpx.Limits(
            max_keepalive_connections=10,
            max_connections=20,
        )
        self._client = httpx.AsyncClient(limits=limits)
    return self._client
```

## Common Pitfalls to Avoid

**String Escaping in Code Generation**
Always escape in this order:
1. Backslashes first: `\\` → `\\\\`
2. Then quotes: `"` → `\"`
3. Then control chars (newlines, tabs)

Wrong order creates invalid escape sequences!

**Python Version Requirements**
- Union syntax `str | None` requires Python 3.10+
- Always include `from __future__ import annotations` at top of files
- Use `target-version = "py310"` in ruff/black config
- Test in CI across all supported Python versions

**Test Fixtures vs. Mocks**
- Don't over-mock - it hides serialization bugs
- Test actual API calls when possible
- Use real Pydantic validation in tests
- Mock external services, not internal logic

## Pre-Commit Checks

Run these checks locally before every commit:

```bash
make lint
make typecheck-all
make test
```

All must pass. `make ci-local` runs the core local gate: lint, all type-check
contracts, tests, and generated-code validation. Specialized CI jobs such as
storyboard runners, Postgres conformance, and conventional-commit validation
still run separately in GitHub Actions. CI runs the core matrix across Python
3.10–3.13; locally running on your current version catches most issues.

## Parallel Agent Isolation (git worktrees)

When multiple agents work in the same checkout simultaneously, they clobber each other's
branches — there is no error, the work is silently lost. Use `git worktree` to give each
agent an isolated checkout.

> **Note:** Conductor worktrees handle this automatically via `.conductor.json`
> (runs `setup_conductor_env.py` + `pre-commit install` on create). Use the
> manual steps below only for raw `git worktree` outside of Conductor.
> See `CONDUCTOR.md` for Conductor-specific setup and troubleshooting.

**Create a worktree:**

```bash
git worktree add /tmp/claude-issue-<N>-<slug> -b claude/issue-<N>-<slug> main
```

**Setup checklist (run inside the new worktree):**

```bash
cd /tmp/claude-issue-<N>-<slug>
cp "$(git rev-parse --git-common-dir)/../.env" .env   # .env is not inherited
make bootstrap                     # requires uv; installs deps and hooks here
```

**Teardown (after branch is merged):**

```bash
git worktree remove /tmp/claude-issue-<N>-<slug>
# or: git worktree prune   # removes all stale worktrees at once
```

**Branch naming:** always follow `claude/issue-<N>-<short-slug>` — branch-protection
rules enforce this pattern and PRs from non-conforming names may be rejected.

## Parallel Agent Coordination

When spawning parallel sub-agents, each agent must receive an explicit write-scope
declaration in its prompt. Agents do not detect or refuse out-of-scope writes at
runtime; this contract is the only enforcement mechanism.

**Prompt template for a parallel sub-agent:**

```
Task: <what this agent should do>

Read scope (consult freely):
- <file or glob pattern>
- <file or glob pattern>

Write scope (the ONLY files this agent may create or modify — exact paths, no globs):
- <exact file path>
- <exact file path>

Do not edit files outside your write scope even if you believe the change
would be an improvement. If you discover during execution that you need to write
a file outside your scope, stop and record it in your reply instead.
```

**Pre-spawn checklist:**

1. List every file any agent in the group is expected to write. If an agent may
   discover additional files during execution, note that in your scope planning —
   do not silently expand the write scope at runtime.
2. Partition that set so each file appears in exactly one agent's write scope.
   For files both agents need to write, assign one owner; have the other emit the
   required change as a note in its reply.
3. Pass each agent its partition explicitly (see template above).
4. After all agents complete, check for collisions:
   `git log --name-only --oneline -<N>` (N = number of agent commits), then look
   for the same file appearing in more than one entry.

## Issue Triage Bot

A Claude Code routine ("issue triage", wired in
`.github/workflows/claude-issue-triage.yml`) fires automatically on every
new issue and on every non-`/triage` comment. It reads the issue body,
decides whether to clarify, defer, or open a draft PR, and posts back via
comment. PRs it opens land on `claude/issue-<N>-<slug>` branches, are
labeled `claude-triaged`, and the issue carries `claude-triaging` while
the routine is actively running.

**Coordination rules:**

- **Do not open a new PR for an unlabeled issue without checking the
  triage state first.** If the issue carries `claude-triaging` the bot is
  actively working — your work will collide. If it carries
  `claude-triaged` the bot has already produced (or deferred to) a PR;
  find that PR before starting fresh work.

- **Apply `no-triage` at issue creation when you (human or designated
  agent) plan to do the work.** The label short-circuits the workflow
  `if:` gate so the routine never fires. Labels added after the fact do
  not retroactively cancel an in-flight run.

- **Manual `/triage` overrides the `no-triage` label.** The
  slash-command-dispatch path is gated only by member-association — use
  it when you explicitly want the bot to engage on a `no-triage` issue.

- **Stale `claude-triaged` draft PRs lose parallel races.** When a
  human-authored PR for the same issue lands on main first, the bot's
  draft becomes superseded. Prefer closing-as-superseded over rebasing —
  always check recent main commits before investing time in a rebase of
  a triage-managed draft.

## Additional Important Reminders

**NEVER**:
- Assume a "typo" without checking the actual secret name in GitHub settings

**ALWAYS**:
- Verify secret names match repository settings before "fixing" them
