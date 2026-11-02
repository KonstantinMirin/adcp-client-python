# The AdCP types SDK: what it is, and how it is built

The AdCP schema bundle is a directory of JSON Schema draft-07 documents. This describes how we
turn it into Pydantic models: what we produce, the principles that decide every case, how we walk
a document, what we emit, and how each keyword compiles. Where a keyword compiles to nothing, or
to an annotation that says less than the keyword does, that is stated with the keyword — and no
keyword refuses a document (§2, §7).

No site counts appear here. A count is a property of one bundle version and the method has to
outlive it; the instruments under `survey/` and the test suite carry the measurements.

---

## 1. The artifact

A set of Pydantic classes, one per schema node that needs one, generated from the bundle. A
consumer reaches them through one import surface:

```python
from adcp.types.core import PaginationRequest     # the one import spelling
from adcp.types.enums import MatchType            # the domain says where it came from

req = PaginationRequest.strict_validate(payload)  # the schema decides, then construct
req = PaginationRequest(max_results=50)           # pydantic constructs, annotations only
mode = MatchType("broad")                         # a consumer uses these types directly
```

**Generated modules are private; the domain surface is public.** A document compiles to a module
at its own path under a private tree — `core/date-range.json` → `_schemas/core/date_range.py` —
and is re-exported from `adcp.types.<domain>`, where the domain is derived from the document's
own path. So `enums/match-type.json` is reachable as `adcp.types.enums.MatchType`, and a reader
of application code sees what kind of thing it is without looking it up.

There is **one import path per class**, and never a second way to reach the same class. Two
spellings for one class is two things to keep in agreement, and it makes a reader unable to tell
from the import which document a class came from. The one path is the domain surface's. A second
name bound to a class by identity (§4, two nodes of identical content) is that class and not a
second one: `X is Y` holds, and the surface exports it once. **That carve-out reaches across
modules as well as inside one (2026-10-26)**, because a document that is a bare `$ref` to another
document states the same node, and §4's rule for the same node stated twice does not change at a
file boundary. Where the target is a class the root is a subclass of it instead, which is one
class per name and needs no carve-out at all; the identity binding is for a target that is an
alias, an enumeration or a root model, where there is nothing to subclass.

**Every portable document of the bundle contributes a symbol** — a class, a root model, an
enumeration or an alias — because §2 admits no document without one.

**AND THE RULE'S OTHER DIRECTION, which this section forbade in neither words nor scope until now
(decided 2026-10-30).** "One import path per class" forbids two paths to one class. The domain
surface produces the INVERSE — **one path bound to two classes** — and that is forbidden too, at
the scope the surface creates: **no `adcp.types.<domain>.<Name>` may name two declarations.** §4's
collision rule settles a name inside one MODULE, and a domain is many modules, which is why it was
never reached. It is the same rule at a wider scope, and its answer is unchanged: all N colliders
lengthen.

**WHAT THE SURFACE EXPORTS: every document ROOT and every union BRANCH, and not every class
(decided 2026-10-30).** Measured over the emitted tree before choosing, at domain scope:

| export set | distinct `(domain, name)` | colliding names | declarations involved |
|---|---|---|---|
| roots only | 1,027 | **0** | 0 |
| roots **+ every branch** | 1,932 | **26** | 54 |
| every class the tree declares | 3,056 | **237** | 630 |

The middle row's figures were **first measured 196 declarations too low, and the undercount is
itself the finding (corrected 2026-10-30).** A reading over the emitted TEXT has to spell "branch"
as *a class one of whose bases this module declares*, and that misses every arm of a nested
`A | B` union, which subclasses nothing local. So the export set is read off the RUN's own record
— `ir.Module.exports`, written where a position's hop and its declaration are both in hand —
giving **1,951 declarations: 1,054 roots, 756 branches, 141 aliases**, over 1,932 distinct pairs in
23 domains. The 1,054 roots are exactly this section's "every portable document contributes a
symbol", read from the other end.

The third is **refused**: it makes
`core.Status` name one of FOURTEEN declarations, `core.Reason` one of eleven, `core.Location` one
of ten, and only 12 of its 237 collisions are identical-body. A name that means fourteen things is
not a surface, and the 225 genuinely different classes behind those names are inner structures of one
document each — a consumer reaches them through the field whose annotation names them, which is
the path the document itself gives.

Roots and branches are exactly the set a consumer must be able to NAME: a root to construct or
validate a message, and a branch because a union hands one back and `isinstance` is the question
the rewrite exists to answer. Its 11 collisions are nameable and lengthen under the rule above.
**Two of them collide inside `emit.exported` already**, so the module-to-module question is
ambiguous today independently of any surface: `brand.SignedResponse` and
`brand.SignedSuccessPayload`, each declared by both `verify_brand_claim_response` and
`verify_brand_claims_response`.

A D2 `Annotated` alias is a name an application writes, so the 113 distinct type aliases are
exported with the same rule. The 241 per-module `strict_validate` helpers are not: a domain name
cannot stand for 241 functions, and a caller reaches one through the class it belongs to.

**`adagents` is a domain (2026-10-30).** `adagents.json` sits at the tree's root with no directory
beside it, so the derivation answers 23 domains and not the 22 the directories suggest. It gets
`adcp.types.adagents`, carrying its 39 classes. §10's layout rule is untouched — that rule is
about a document whose path is ALSO a directory's, and this one has no directory.

The bundle directory is an argument (`python -m codegen.emit --bundle <dir>`). Nothing reads a
hard-coded path, so a second bundle version can be generated beside the first.

### A patched bundle is a legitimate input, and the test is the RECORD (decided 2026-10-27)

Upstream repairs land on upstream's schedule, and some of them cost this SDK a type name at
hundreds of sites. So the bundle we hand the compiler may be a PATCHED copy of the published
one — but only under a condition that makes the patch provable rather than a judgement:

**A patch is admissible exactly when no patched document's record differs from the published
document's record at a key that decides acceptance.** A key decides acceptance when the keyword
table says it does: `bundle.is_an_annotation(keyword, position)` is the predicate, and it is the
one `record` already reads to settle a `$ref`'s sibling, so the line is the table's and not a
second judgement.

That is a mechanical check with the machinery §3 already builds. `record` inlines every
cross-document `$ref`, so extracting a repeated subschema into its own document and referencing
it is the INVERSE of what `record` does: resolve the patch and the original comes back at every
key a validator can act on, or the check names the pointer and the keyword.

*This said "byte-identical" until 2026-10-27, and that rule forbade its own purpose.* `record`
inlines a reference's target WHOLE, so a site that comes to reference a **titled**
`core/currency-code.json` takes that document's `title` and `$schema` into the record where the
published site had neither. The sentence demanding byte-identity and the sentence asking for a
titled document could not both hold, and the row that built the patch measured the gap rather
than quietly widening the tolerance: over the 1,054 portable documents, **22,337 record
differences across 429 documents, every one a GAIN of `$schema`, `title` or `description`, and
zero differences a validator can act on — nothing lost or changed at any pointer.**

Byte-identity was the wrong instrument because it measures the record's bytes when what it is
protecting is the accepted set. The accepted set is exactly the keys the table calls
acceptance-deciding, so that is what the check compares. A patch that adds a name is admitted; a
patch that moves one acceptance key is not, and that line is where it always should have been.

What that admits, and it is the whole of the ergonomic win: **naming.** Extracting
`{"type": "string", "pattern": "^[A-Z]{3}$"}` into a titled `core/currency-code.json` and
referencing it at all 86 sites changes no instance's validity, so `strict_validate` still
decides exactly what the published protocol decides — and §5's `$ref` row turns those sites into
an import of one named type instead of 86 copies of a digest.

What it forbids, and this is the line the condition draws: **anything that moves the accepted
set.** Adding the `minItems: 1` that five documents omit changes the record, fails the check,
and must go upstream — because `strict_validate` would then accept or refuse differently from
the protocol, which is the one thing §2's first principle cannot survive. A patch that changes
acceptance is not a patch, it is a fork of the protocol.

**Every patch is also the upstream pull request.** The patch set is the diff we ask upstream to
take, so carrying one is a way of shipping the fix early rather than a way of living without it,
and the patch disappears when the backport lands. A patch with no filed issue behind it is the
same defect as an exemption with no issue behind it, which §9 already names.

---

## 2. Design principles

**THE VOCABULARY IS COMPUTER SCIENCE'S, and a word outside it is not a shorthand (decided
2026-11-02).** These documents say *compile*, *emit*, *value*, *validate*, *branch*, *type*,
*structure*, *constraint*, *reference*, *position*, *keyword*, *declaration*. A word that merely
gestures at a technical idea is banned, because it lets a sentence read as decided while leaving
the decision unmade — a reader cannot check "the form it takes" against anything, and two readers
will not agree on it. **"Shape" was the one this project used and it is removed**: 95 uses across
the three design documents, standing in for *type*, *structure*, *case* and *structural branch*,
four distinct meanings behind one word. Where a sentence needed one of those, it now says which.



### Where the `oneOf` entailment is derived (decided 2026-10-29)

§5's `type` row says an enclosing `oneOf` applies a type word it does not state. **The derivation
belongs in `adcp.types._base.applied_schema` and nowhere else**, and the two other readers derive
from it rather than restate it.

`bundle.constrained_to_object` already works that way and its own docstring says why: that
function is what the RUNTIME resolves a class's `__adcp_schema__` through, "so deriving the
lowering's answer from it is what makes it impossible for the emitter to admit a node whose class
would then be narrower than the schema it names. Two spellings of 'which hop keeps the instance'
is precisely how that divergence would arrive, and it would arrive silently."

So the entailment is one sentence in one function, and the walk inherits it. `harness._entails_type`
is the third reader and its combinator arm must derive from the same function rather than require
a STATED word on every branch — measured, requiring one reports `added /type` on 9 pairs, which is
the divergence that docstring forbids showing up as a verifier disagreement instead of a crash.
§9 permits it: `adcp.types` is the emitted package reached as a consumer reaches it, and
`_base.applied_schema` is the runtime's, not the walk's.

Three readers, one derivation. A row that adds the entailment to a parser and leaves the other two
alone has written the second spelling, whatever the measurement says that day.

### The intersection is idempotent (decided 2026-10-29)

`allOf` applies every conjunct to the same instance, so a conjunct already in the composed list
states nothing a second time: **A ∧ A ≡ A.** A merge that appends a base's reference appends it
only where the list does not already name it.

Measured on `creative/list-creatives-response.json`, where two individually-correct merges each
appended the same bare reference and the emitted class read `(Indicator, Indicator)` — which
Python refuses to build. Both merges were right about their own pair; neither asked whether the
conjunct was already there. The document states no `allOf` at that node at all, so **both
conjuncts were ours**, and that is why the answer is here and not at the base list: deduplicating
the bases would have left a node no document states standing for §8's document-side fold and for
every refusal pointer below it, which §9 forbids — "do not decide a position the bundle does not
hold from a view of it".

The composed list stays a LIST and not a set. Its order decides the pointer a nested class is
stamped at, so idempotence is a property of the one member a merge appends and not a set
conversion of the whole.

### A generated region of a plan document is its rendering, not an edit (decided 2026-10-29)

Both plan documents are blob-compared on every delivery, and a lane may not edit either. **A
region between `<!-- begin generated -->` and `<!-- end generated -->` is exempt, because a
keyword decision lives in `codegen/keywords.py`'s cell and the grid is its rendering** — a lane
that moves a cell and regenerates has changed the decision in the one place §5 names for it, and
the row following is the table agreeing with itself.

The exemption is narrow and testable: the diff must lie wholly inside a generated region, and it
must be exactly what `pytest tests/test_keywords.py --write-grids` writes. A row that moves
without its cell moving, or prose outside the markers, is an edit and is refused. `test_keywords.py`
holds the equality in both directions, so a hand-written row reddens it.

Prose is mine. The cells are the compiler's, read by four readers, and the grid is what they
render to.

### A refusal is the document's; a broken invariant is ours (decided 2026-10-29)

A `Refusal` names a fact about the document — a keyword it states that no row reads yet
(DEFERRED), or a thing the document itself says that admits nothing (VERDICT). **Where the
compiler cannot proceed for a reason that is not a fact about the document at all, that is not a
refusal and must not be reported as one. It raises.**

Two nodes of one document deriving one class name is a fact about `lower/names.py`. A base
ordered before its own subclass is a fact about the MRO this compiler builds. Neither is anything
the document's author could read, act on, or fix, and reporting one as the document's obstruction
is how `core/postal-area.json` and **the 31 documents chained behind it** came to be counted
`accounted` — "nothing more can be done here" — for a naming choice we make.

The practical test is the report line. If a reader of the refusal would go to the schema to
understand it, it is a refusal. If they would go to `codegen/`, it is ours, and an exception at
the pointer is both louder and honest where a refusal is quiet and wrong.

This is why an unreachable arm guarding a compiler invariant needs no `Refusal.kind`: the
question "is this a verdict or a deferral" does not apply to it, because it is neither. `kind_for`
answering DEFERRED for such an arm is not the table being wrong — it is the arm being the wrong
case.

### The schema decides acceptance

Every emitted class carries `strict_validate`, which validates a payload against the class's own
schema document before constructing anything. The model is not the authority on what the protocol
accepts; the document is.

*Why.* Pydantic and JSON Schema do not agree on every edge, and where they differ the document
wins — it is what the other side of the wire was written against. A model may therefore be looser
than its document without being wrong, because the schema half already refused the payload. It
must never be *tighter*, because then we refuse something the protocol permits.

This principle is what makes the widening rule at the end of this section possible, and the two
are one statement read twice: if the document decides acceptance, then a fact the annotation
drops costs precision and not correctness, and the only annotation that can be wrong is a tight
one. Every approximation below is therefore a loosening, and the check that guards it (§8's
accepts) is a check for tightness.

### Constraints bind to the type, not the field

A bound belongs to the thing it constrains:

```python
Annotated[int, Field(ge=1, le=100)]
```

not a `Field(ge=1)` sitting beside a bare `int` on one class. The constrained type is then
reusable: it nests into `list[...]`, into a mapping value, into a union branch, and into another
document's field, carrying its bound with it.

Two choices, in order of preference: a standard Pydantic type where one says exactly this
(`NonNegativeInt`); otherwise a named alias in `adcp.types.constraints`, its name derived from
the constraint and from nothing else (`StrMinLen1`, `FloatGt0`, `NonEmptyList[T]`; a `pattern`
contributes a digest of itself). An alias in `constraints` names a *constraint*, never a concept
— `NonEmptyList[T]`, not `MediaBuyStatusList`. **Every constrained scalar is named**, including
one the bundle states at a single site. A constrained container is generic over its element and
is named once for every element (`NonEmptyList[T]`); where a field holds the container the
annotation is written on that field's type.

*Why.* A bound written onto a field exists only at that field. The same bound reached through a
list, a mapping or a branch then has nowhere to live, and the usual repair is to put it on the
field holding the container — which constrains the wrong thing. On a union branch that repair is
actively wrong: the field also holds the other branch, so a bound there refuses values the
document accepts.

*Why every one.* Naming only the types that recur needs a census over the run, and a census
makes one document's module a function of which other documents the run includes: a run over
one document and a run over the bundle would emit different text for the same document. A name
that is a function of the constraint alone has no such coupling, and the cost — a name for a
constraint stated once — is a name a reader can derive from the constraint it spells.

### Rules are after-validators, written once

A keyword that spans fields, or spans a collection, has no field-level annotation that can carry
it. Those become rules: an after-validator in `src/adcp/types/_runtime.py` reading a class-level
tuple the emitter writes. The families are `oneOf`/`anyOf` over `required` or over pinned
values, `if`/`then`/`else`, `dependencies`, `minProperties`/`maxProperties`, `uniqueItems`,
`not`, and `contains`.

**Rule placement.** Declare a rule on the nearest enclosing class, which can read sibling
fields. Where no class encloses the value — a root array, a mapping value, a `definitions`
entry, a union branch — declare it as an after-validator on the value's own annotated type
(`AtLeastOne`, `NotValue`, `Distinct`).

Placement determines where a rule is declared, not which members it reads. A rule declared on a
value reads that value's own members, as a rule declared on a class reads its fields. A rule
naming keys — `ForbiddenGroups`, `RequiredGroups`, `PresenceGroups` — is therefore valid as an
after-validator wherever no class encloses the value.

**A composing DECLARATION is not a position where no class encloses the value** (decided
2026-10-29). A property whose declaration is an `allOf` still sits in the class that holds the
property, so the clause above is unchanged and the rule is declared there — the reader that
writes it must see through the composition rather than the rule move to the value's own type.

Measured on `core/catalog-selection.json` at `/properties/ids`, whose `uniqueItems` reached
neither half of the row: `rules_at`'s screen claims every RULE-cell key the node carries, and
`lower.rules._distinct` reads `uniqueItems` one level down off the array a property holds, so a
composing declaration fell between them. `_distinct`'s `type == "array"` gate is the thing that
has to read a conjunct; carrying `distinct` on the composition instead would declare the rule on
the value's annotated type, which this clause reserves for where no class encloses it, and one
does.

The same reading answers it for every value keyword that composes, which is why it is stated here
and not per keyword. `contains` is the exception already recorded in §5's two-array clause, and
for its own reason: a declaration holds one `contains` key, so two cannot be spelled in a merged
declaration at all.

A rule's condition tests membership as well as equality: a `Match` clause reads a property's
`const` or `enum`, and also `value in field`.

*Why written once.* A generated validator body is code we would generate and then be unable to
review. A hand-written validator reading generated data is reviewed once and exercised by every
document that needs it.

### Composition merges by intersection

An `allOf` of `$ref`s makes those classes the bases. Where two composed schemas constrain the
same property, the field carries the **intersection**: an enum is the intersection of members, a
bound is the tighter one.

A composed class's `required` is the union of its own and every base's. An emitted class
redeclares an inherited field in exactly two cases. Where composition makes an inherited field
required, the subclass redeclares it with the base's type and no default. Where the subclass's own
document **restates the property with a different `default`**, it redeclares it with the base's
type and that default: a default is a value and not a constraint, so it neither widens nor
narrows what the class accepts, and the schema that states it is the one that decides. A
redeclaration that changes the TYPE is a build failure.

*Why intersection.* `allOf` means every conjunct holds. A union of their constraints would accept
payloads a conjunct refuses, making the model looser than its document.

### `extra` follows the schema, and nothing else

`additionalProperties: false` → `forbid`. `true` → `allow`. A typed `additionalProperties` →
`allow` with a typed `__pydantic_extra__`. **Absent → `ignore`.**

Absent and `true` are different statements. `true` says additional properties are part of the
document, so they are retained. Silence says only that they are permitted, so they are accepted
and dropped — retaining a property the document never mentions would be the SDK adding a claim
the schema does not make.

A consumer wanting stricter or looser behaviour sets it on a subclass. No generated class carries
a policy that is not in its document, and nothing reads an environment variable to decide.

### Nothing rewrites emitted output

A defect is fixed in the schema input, or in the compiler, before the output is written. There is
no post-processing pass over generated files.

*Why.* A rewriting pass is a second source of truth for the output's structure, and the two drift. It
also hides which input produced which line.

### The compiler is pinned, and a gap in it is fixed in it

The pipeline is `f(schemas, pinned compiler)`, and both arguments are ours to change: a defect is
fixed in the schema we hand it, or in the compiler itself. A fix we carry is offered upstream as a
pull request, and a fork exists only once something needs one.

*Why.* The alternative to fixing the compiler is working around it at the call site, which means
the workaround has to be understood by everyone who later reads the output and cannot find the
rule that produced it.

### An annotation is admitted by name

A keyword that cannot constrain an instance compiles to nothing, and is admitted by an explicit
**name** — not by a pattern over its spelling, and not by ignoring whatever is unrecognised.

*Why by name.* Silence cannot distinguish "this keyword carries no acceptance meaning" from "this
keyword constrains instances and we have not implemented it". The first is correct; the second is
a model looser than its document. Naming each one makes the first auditable and leaves the second
loud.

### A keyword we cannot express widens the annotation

**This replaces "a keyword we cannot express refuses the document", decided by the owner on
2026-10-26:** *"We accept ZERO refusals as an outcome in the scope of this work. Every single
schema should be represented as a Python class. And if it can't — then we look into the reasons
and approximate it, and raise the upstream issues."*

What it replaced said: where a position carries a keyword we have no compilation for, the
document is refused by name, pointer and keyword, and is not emitted — because "a partial model
is worse than none: it would claim conformance to a document it does not enforce."

*Why it is replaced: that sentence contradicts the first principle of this section.* The first
principle says the model is not the authority on acceptance — `strict_validate` runs the
document before anything is constructed, and the document decides. A model looser than its
document therefore claims nothing it does not enforce, because the claim is not the
annotation's to make: the schema half has already refused the payload. "It would claim
conformance" presumes the annotation IS the conformance claim, which is the proposition the
first principle denies. The two cannot both stand, and the first is the one every other
decision in this document rests on. The widened annotation costs **static precision**, not
runtime correctness, and the refusal was paying a document's whole typed surface for it.

The refusal argument survives in exactly two places, and the design keeps both.

- **A narrowing.** An annotation tighter than its document refuses a payload the protocol
  permits, and `strict_validate` cannot repair it: the schema half admits the payload and the
  construction then fails. A narrowing is the defect the old sentence was reaching for, and
  nothing below widens into one.

  **A narrowing taken on purpose is admitted by an ENUMERATED registry and by nothing else.**
  The registry is the authority, this sentence is not, and a narrowing absent from one is the
  defect above. Each entry is compared by equality so it admits that fact and not its kind — a
  rule admitting "the sort of bound a URL type adds" would be invisible and permanent.

  **A registry is a DECISION where no other check can report its edit, and a decision must be
  read by a test (added 2026-10-27).** That is the discriminator between a decision and a
  mechanical lookup, and it is the reason the distinction can be measured rather than argued:
  a lookup's error surfaces somewhere else — a wrong `_TIGHTER_BOUND` direction loosens the
  composed bound and the pair reports `added` — while a decision's edit is silent everywhere.
  `tests/test_decision_set.py` holds the guard, with both sides of every pin derived.

  **A per-pair reading cannot see one of these edits, which is why the guard measures REACH.**
  Measured: remove `maxLength` from `URL_IMPLIED` and `added` over all 1,571 graded pairs is
  unchanged — every pair grades exactly as it did. That silence is the signature of the
  incident this rule exists for, so the guard switches each admission mechanism off in turn and
  pins which keywords reappear.

  **The registry is EMPTY, because the URL type that filled it is withdrawn (decided
  2026-11-02).** It held two facts a pydantic URL type renders of its own — `minLength: 1`,
  `maxLength: 2083` — and those were the registered part. The type's NORMALISATION was never
  registered, and by the sentence above that makes it the defect: a pydantic URL lowercases the
  host and gives an empty path a `/`, so two distinct strings the document admits become one
  value, and the value dumped is not the string supplied.

  It cannot be registered either, and the reason is the one this subsection already gives: an
  entry is compared by EQUALITY so that it admits that fact and not its kind, and a
  normalisation is a kind. "The sort of rewriting a URL type performs" is exactly the invisible,
  permanent admission the rule forbids.

  Measured, both directions at once, which is what makes it a defect and not a trade:
  `core/attestation-capabilities.json#` admits `accepted_proof_formats:
  ["https://A.com", "https://a.com"]` — two distinct strings — and the class REFUSES it on its
  own `uniqueItems`, because both coerce to `https://a.com/`. And
  `core/product-offer-filters.json#` accepts `https://Qo1P.here` and dumps
  `https://qo1p.here/`, which the document then refuses on its own
  `pattern: ^https://[^/?#@]+$`. One type decision, a narrowing and a broken round trip.

  **A rule-level repair is provably wrong**, and was measured rather than argued: neutralise the
  `UniqueItems` comparison and the same pair fails the other way, because the DUMP then carries
  the duplicate and the document refuses it on `uniqueItems`. The rule is not the defect; the
  non-injective type is.

  **So `format: uri` carries the document's own string, with the URL grammar asserted beside
  it.** Reach: 50 `uniqueItems` arrays whose items declare `format: uri` in 29 documents, 149
  `format: uri` positions beside a pattern the normalised form violates, about 300 `uri`
  positions in 160 documents.

  This is a widening TOWARD the document on three counts, so `approximated` moves DOWN rather
  than up: both `URL_IMPLIED` facts stop being dropped, the URL type's refusal of `urn:` and
  `file:` — which `format: uri` admits — stops narrowing, and §5's "a `uri` beside another
  string constraint → refused" stops refusing, because a string carries bounds and a URL type
  does not. What is lost is a consumer receiving a parsed URL object instead of a string, and §2
  settles that trade where it always settles it: an annotation tighter than its document is the
  defect nothing may widen into.

  Three cells follow and are a lane's to write, not this rendering's: `format`'s (`uri` no
  longer selects a type), `pattern`'s (the pattern goes on the type rather than staying with the
  schema half), and `minLength`/`maxLength`'s (no URL type to refuse against).

  **A reading that finds code contradicting this section reports it and does not change either
  side.** A registry entry is a decision even though it is not in this document.
- **No document of record.** Where the record (§3) is undefined, there is no schema half at all,
  so `strict_validate` has no authority to run and the annotation is the only claim there is.
  That is the one case where a partial model really would claim conformance to a document it
  does not enforce, and it is the one refusal this compiler can still mint. §7 names its three
  cases and says what each is measured at.

#### Direction: every approximation of acceptance is a widening

A fact the annotation cannot carry is **dropped**, never substituted. Dropping a constraint
widens the admitted set and can do nothing else; substituting a "nearest expressible"
constraint could narrow, so substitution is not available. The handler takes the lowest rung of
one ladder it can render, and the ladder is finite, monotone and terminates:

1. **KEYWORD** — drop the one keyword, keep the type. (`uniqueItems` where no class and no
   named type hold the rule → `list[X]`.)
2. **TYPE** — drop a type selection the constraints contradict, keep the constraints.
   (`format: uri` beside `maxLength` → the constrained `str`, the format riding as
   `json_schema_extra`.)
3. **JOIN** — replace a type with the union of the types it holds. (A list-valued `items` →
   `list[A | B | …]`, dropping position and arity.)
4. **CONTAINER** — replace the node with its bare container: `list[Any]`, `dict[str, Any]`.
5. **TOP** — `Any`.

`Any` admits everything, so the ladder always has a rung left and no node can run out of
renderings. **Which rung a keyword takes is the keyword's decision and lives in its cell
(§5), never at the site that widens.**

A narrowing is not discouraged here; it is a **failing check**. §8's accepts draw covers the
node's admissible space by constraint class, so a type that refuses any value the document
admits is reported with the value. Where a widening would still leave a narrowing — the type
word itself refusing what a constraint admits — the type widens by another rung, to `Any` if
nothing else carries it.

#### An approximation is declared, and it is local

A refusal propagates: a parent returns it upward unchanged and the document emits nothing. An
approximation does **not**. It is a property of one node, the document still emits, and the
approximation travels upward only to be **accumulated** — a refusal is absorbing, an
approximation is additive. Every one carries its document, its pointer, the keyword whose fact
the annotation does not carry, the rung it took, that fact in the document's own spelling, and
an **attribution**. Nothing is approximated by silence: an undeclared widening is a defect and
§8 reports it as one.

#### Two kinds of approximation, and they are never summed

**ONE kind, after 2026-10-30: WIDENED.** The annotation admits a value the document refuses. The
schema half refuses it, so acceptance is unharmed; what is lost is what the type says, and §8's
DRAW proves each one by handing the class a value the document admits.

*UNDERDETERMINED is retired with the text diff that was its only grader.* It said the annotation
admits exactly what the document admits and the VALUE constructed is not determined — a union whose
branches §4's dispatch cannot separate, where `A | B` accepts the union either way and which
branch an overlapping payload becomes is a property of declaration order. **No draw and no dump can
observe that**, which was offered as the reason it needed a different instrument and is in fact the
reason it is not a fact about the artifact. An inseparable `oneOf` is unaffected and stays WIDENED:
there the model admits a payload the document REFUSES, and the draw shows it.

#### Attribution: ours, or upstream's, and the issue is a reference

§9's rule — "an exemption names an upstream issue, or it is this SDK's own decision and belongs
in this document" — governs every approximation, and the attribution is a choice of two and not
a free-text note:

- **Ours.** The design decided this widening; the sentence is the keyword's own row in §5, §6 or
  §7. The attribution is therefore the **cell's own address** and is derived, not stored: a
  reader goes from a widened field to the row that decided it, and that row says why.
- **Upstream.** The document could state the fact and does not, or states something no draft-07
  reading can carry. The attribution is an **issue reference**, and it is a property of a
  document and a pointer rather than of a keyword — the same keyword widens by our decision at
  one site and by an upstream defect at another. It therefore lives in one registry keyed by
  document, pointer and keyword, and an entry with no issue is a build failure rather than a
  missing field.

**Ours is work this project can do and must fall to zero. Upstream falls when an issue closes.**
Summing them would report someone else's backlog as ours, which is the second half of §9's rule.

#### What is counted, and over what

Three figures, three denominators, never summed (§8 states the grading side of each):

- **Emitted, over the population.** Every portable document of the bundle emits, and its
  complement is the one irreducible class above — no document of record. This is a partition and
  it is the directive's exit condition: *refused* is zero.
- **Round-trip failures, over the graded pairs.** A pair where the class refuses a value the
  document admits, or where the dump is a value the document refuses. Pinned at zero, because
  either one is the defect that matters.
- **Approximations, over the declared set**, split by attribution. This count moves with
  emission, so §9 forbids pinning it; it is reported, and its `Ours` half ratchets down. The
  four text-diff defect counts that stood here are deleted with the comparison (2026-10-30).

The approximation count is **not** a partition of the population the way *emitted / refused*
was: one document carries many and most carry none. The number of documents carrying at least
one is a different figure over a different denominator, and the two are never added.

---

## 3. Walking the tree

A document is walked once. Every node is reached at exactly one **position**, and a keyword's
compilation depends on the position as much as on the keyword.

| position | the node is |
| --- | --- |
| ROOT | the document root |
| PROP | a value of `properties` |
| ELEM | an array's `items` |
| MAPV | a mapping's value schema (`additionalProperties`, `patternProperties`) |
| KEY | a mapping's key schema (`propertyNames`) |
| BRANCH | a branch of `oneOf` / `anyOf` |
| CONJ | a conjunct of `allOf` |
| RULE | inside `not`, `if`, `then` or `else` |
| DEF | an entry of `definitions` / `$defs` |

RULE is the position that changes a keyword's meaning most: under a conditional, a keyword
describes what a rule *tests*, not what an instance must be, so no type is lowered from it.

A DEF entry is decided as its own kind under the name `<Root><Key>`, so a DEF answer is the
entry's own position's answer. An entry nothing references is not declared.

One dispatch seam decides a node's kind, so every position reaches the same reader for the same
case. **Every node reaches a lowering**: the seam is total, because a keyword the handler
cannot render widens the annotation by §2 rather than refusing the document. The one refusal
left is the record's own — a document whose references cannot be inlined has no record, so
there is nothing for the walk to read and nothing for `strict_validate` to validate against.
`Refusal` therefore lives with the bundle reader that mints it, not with the lowerings.

### The document of record

What the walk reads, what `strict_validate` validates against, and what §8 grades against is
one document: the bundle's document with every cross-document `$ref` replaced by a copy of its
target, and **nothing else changed**. Resolution inlines; it does not rewrite. No keyword is
dropped, derived, reordered or restated in another spelling, on the referring node or on the
inlined target.

*Why.* A resolver that canonicalises while it inlines — an `enum` of both booleans for a
`bool`, a `const` for a `null`, a bound derived from a sibling, an annotation dropped — writes a
document the bundle does not state, and every reader downstream then grades the model against
that document instead of the bundle's. A payload generator may canonicalise its own copy in order
to draw from it; that copy is an instrument of one check, and it is not the document.

---

## 4. The classes we emit

### What becomes what

| the node | emits |
| --- | --- |
| an object with `properties` | a model class |
| an object without `properties` | `dict[K, V]` |
| an `enum` node | `StrEnum` / `IntEnum`, base read off the members |
| an `enum` on an untitled union branch | a `Literal` of the members |
| a `const` | `Literal[value]` |
| an array at a root | `RootModel[list[X]]` |
| a scalar at a root | a module-level annotated alias, not a class |
| a `oneOf` / `anyOf` of object types | a base plus one class per branch |
| a `oneOf` / `anyOf` of scalars at a root | a module-level alias over the union of their types |
| a `oneOf` / `anyOf` at a root mixing a scalar branch with a class branch | a root model over the union of the branches' types |
| a root stating no schema keyword at all | a permissive root model |

A root scalar is an alias, so it has no class to carry `strict_validate`; its module binds the
same validation as a module-level function over the same schema reference, so a class and an
alias cannot disagree about what their document accepts.

**The last two rows are new on 2026-10-26 and each replaces a refusal.**

A root union mixing a scalar branch with a class branch used to refuse by name, on the reasoning
that "the root symbol is a class or an alias, no structure here carries both". A **root model**
carries both: its root type is the union of the branches' types, the scalar branch is a member
type and the class branch is its own class, and the root model inherits `strict_validate` like
any class. Nothing is dropped and nothing widens — the union admits exactly what the document
admits — so this row costs no approximation. What it costs is ergonomics: a consumer writes
`X(root=…)` where a base-plus-branches root takes the payload directly. That is a smaller price
than a document with no type, and the row the old sentence was protecting — an all-scalar root
union, which stays an alias — is untouched.

A root stating no schema keyword at all is a registry's instance data sitting at a schema root,
and §7 used to refuse it. Read by its own declared draft it is the **empty schema**: draft-07
ignores an unknown key, so the document admits every instance, and a permissive root model is
**faithful** to it rather than wide. Refusing it was never a statement about the document's
accepted set; it was how the fact that the document is not really a schema showed up in the
report. That fact now shows up where it belongs — as an approximation at the root with an
upstream attribution, asking the registry either to drop its `$schema` or to declare a schema —
and §7 says why the keyword half of that row is not a refusal either.

Every one of these cases carries `strict_validate` against its own document by one mechanism,
so a class, a root model and an alias cannot disagree about what their document accepts.

Two nodes with identical content emit one class. Two nodes with different content never do. The
class is declared under the name of the position the walk reaches first, and every later
position of the same content binds its own derived name to that class by identity, `X = Y`. A
field is therefore typed by its own position's name: typing it by a sibling position's name would
read as one branch carrying another's type, and would make a symbol depend on which key the walk
reached first.

### Names

- **Root**: `pascal_case(title)`, acronyms kept; where the title is missing or derives no
  identifier, `pascal_case` of the document's own file stem.
- **Nested**: `pascal_case(property)` — `<Property>` for a property, `<Property>Item` for an array
  element, `<Property>Value` for a mapping value, `<Key>` for a `definitions` entry. The
  module path already carries the document, so a nested name does not repeat it.

  **The `definitions` entry dropped its `<Root>` prefix on 2026-10-28**, for the sentence above
  it: the module carries the document. `core/verification-token-claims.json` declares
  `VerificationTokenGradingProfile` and the old rule spelled it
  `AgenticAdvertisingOrgVerificationTokenClaimsVerificationTokenGradingProfile` — 75 characters in
  a module already named `core/verification_token_claims.py`. The prefix was there because this
  section had no collision rule when it was written; it has one now, so the prefix is what the
  collision rule spends when two entries of one module need it, not what every entry pays up
  front. **This is a function of the one document and carries no dependency on a sibling set**, so
  it is insertion-stable — unlike the branch rule tried and reverted at `64d0f897`.
- **Union branch**: its own `title`; else the `const`s it pins, in the document's own key order;
  else its sorted `required` set; else, where the branch is a bare `$ref`, **the TARGET's own
  derived name**; else its **index among the branches**, `<Base>Branch<i>`.

**A bare `$ref` branch is named for its TARGET, and the index is the rung after that (decided
2026-10-29; corrected on implementation the same day).** The name is the target's
DISTINGUISHING REMAINDER and never the target's own symbol spelled straight: the branch's second
base IS the target, so the module imports that symbol, and `spell()`'s `occupied` keeps a
shadowing name rather than refusing it where a chain of one segment has no ancestor to spend.
That case is already red — `core/vendor_pricing_option.py` emits
`class CpmPricing(VendorPricingOption, CpmPricing)` five times — so a rule producing it would
have shipped the defect it was written to avoid. Where the two names share nothing, the branch
takes `<Doc><Other>`. §4 already makes such a branch inherit the target's property map for the pin rung,
and the target is a document whose own class name this section derives — so the name is available
and the index is a worse answer that was reached only because no rung asked.

A positional name is the one outcome a consumer cannot work with. `AssetRequirementsBranch0`
through `...Branch11` are the twelve asset kinds — `image-asset-requirements.json`,
`video-asset-requirements.json`, `audio-asset-requirements.json` and so on — and a caller writing
`isinstance(req, AssetRequirementsBranch7)` has to count the document's branches to know it means
JavaScript. **Measured on a FRESH RUN: 18 classes over 7 documents take the index, of which 13 are bare
`$ref`s** and are what this rung reaches. The other five are other cases — a nested registry
branch, an `allOf` arm, a properties-only arm, and a `not`-complement branch with the copy another
document inlines. An earlier figure of 19 over 6 was read off the committed tree, which was 39
documents stale, and assumed one case for all of them.

Where the root's name and the target's share a leading run, the branch takes the root's name plus
the target's distinguishing remainder, so `core/requirements/asset-requirements.json`'s branch on
`image-asset-requirements.json` is `AssetRequirementsImage` and not the target's name repeated.
Both inputs are facts about the one branch — its root and its target — so the rule is
insertion-stable, which is what §4's own criterion asks and what the branch rule reverted at
`64d0f897` failed.

**The spelling needs a rename census before it lands**, as rung 2's did: the four single-pin
branches of `postal-country-system` had to keep `US`, `GB`, `CA` and `Plz`, and the same question
applies to every sibling of the 19.

**Rung 2 reads EVERY pin the branch states, and a rung that collides has not identified the
branch (decided 2026-10-29).** Two clauses, and both are functions of the one branch, which is
the insertion-stability criterion this section already states for the nested rule — a rule
reading "the property the most branches pin" would rename every sibling when a branch is
inserted, which is what was tried and reverted at `64d0f897`.

A branch pinning a `const` on several properties derives from all of them, in the order the
document writes the keys. Measured on `core/postal-country-system.json`, whose `/anyOf/4`
through `/anyOf/8` each pin two: `FRCodePostal`, `AUPostcode`, `BRCep`, `INPin`, `ZAPostalCode`,
where declining to choose between the two pins gave `Branch4` through `Branch8` — the positional
name for the most heavily identified branches in the bundle. The four single-pin branches keep
`US`, `GB`, `CA` and `Plz`, because one pin in key order is that one pin.

**A boolean pin contributes no segment, because `true` names nothing** (`adcp-client-python-10l.93`,
decided 2026-10-29). This is not a carve-out from the key-order rule — it is the same sentence this
section already states two paragraphs down, that `true` on both branches "names neither", applied
per pin instead of per branch. A pin identifies a branch by its VALUE, and a boolean's two values
are the same two for every property in the bundle. Measured: three branches pin something
identifying beside a `true`, so reading every pin appended a segment identifying nothing —
`PackageSignalTargetingBinary` became `PackageSignalTargetingBinaryTrue`.

It subsumes the collision case rather than sitting beside it. A branch whose pins are all boolean
contributes no segment at all, so rung 2 answers nothing for it and it falls through — which is
what `trusted-match/provider-registration.json` needs, reached now by one rule rather than two.

Where a rung derives one name for two branches it has not identified either, so **both fall to
the next rung** — the collision rule above lengthens a chain, and these chains are one segment
with nothing to lengthen by. Measured on `trusted-match/provider-registration.json`, whose two
branches pin `context_match: true` and `identity_match: true`: the value `true` is the same on
both and names neither, so rung 2 answers nothing and rung 3's `required` set gives
`ContextMatch` and `IdentityMatch`. What identifies those branches is WHICH property is present,
which is the fact rung 3 reads.

Rung 2 is not narrowed to unions that derive a dispatch discriminator. Measured: that reading
takes `postal-country-system`'s four working names away, because no property of it is shared by
all ten branches and the strict reading would send every branch to its index.

**A branch colliding with its own document ROOT: the root keeps the name and the branch falls to
the next rung (decided 2026-10-29).** The collision rule lengthens a chain, and a root has no
chain to lengthen — D5 fixes its symbol, because a document exports one importable symbol named
for the document. So the branch is the side that moves, and it moves the same way any colliding
rung does: to the next rung that answers.

Measured on `core/postal-area.json`, whose root is titled "Postal Area" and whose `/anyOf/0` is
titled "PostalArea". Both derive `PostalArea`, neither can spend a segment, and the compiler
raised a hand-minted verdict there — **writing off that document and the 31 chained behind it for
a naming choice this compiler makes, reported as the document's own obstruction.** That is the
case §2 forbids most plainly: a refusal must name a fact about the document, and "two nodes of
this document derive one class name" is a fact about `lower/names.py`.

The verdict goes with the rule (`adcp-client-python-10l.78`). No document of bundle 3.2 refuses
for a derivable name again: rung 4 always answers, because a branch always has an index.

**AND AN IMPORTED SYMBOL IS THE SAME CASE, stated because a lane had to reach it by analogy
(2026-10-30).** A module that imports a name and then declares a class under it leaves the name
meaning the subclass, so a consumer importing it from the two modules gets two classes with
different `__adcp_schema__` pointers. The reasoning above transfers exactly and is stronger: a
root keeps the name because D5 fixes its symbol, and an imported symbol is fixed more firmly
still — it is ANOTHER document's name, which this module has no standing to move. **So the
colliding branch falls, and the import keeps the name.**

The rule reaches both of §4's axes, and that is the half that was missing rather than the rule
itself. A position whose name is occupied is colliding when deciding whether to LENGTHEN *and*
when deciding whether to FALL; honouring it on the first axis alone reads "cannot lengthen" as
"resolved", which is exactly what a bare-`$ref` branch at rung 1 hits — it is a chain of one with
no ancestor to prepend, and it had three rungs still underneath. Measured at 56 names over 4
modules, every one of them that case.

**Collision, which this section never stated and the emitter therefore avoided by never
colliding (added 2026-10-28).** The nested rule above is the LAST path segment, so two positions
of one module can derive one name — `brand.properties.context` and
`artifacts.items.brand.properties.context` both derive `Context`. With no rule here, the emitter
took the branch that needs none: `names.derive` folds every hop to the root and concatenates, so
a name is unique by construction. That is why 770 of 2,014 emitted classes are longer than 30
characters and one is `GetMediaBuyArtifactsResponseArtifactsMediaBuyIdArtifactsItemBrandContext`.
Unique by construction is not what this section asked for; the module path already carries the
document.

The rule is:

1. Every position derives its short name by the rules above.
2. Where **N positions of one module derive the same name, ALL N lengthen** — each prepends its
   own nearest ancestor segment — and the step repeats until every name in the module is unique.
3. A position whose short name collides with nothing keeps it.

**All N lengthen, and that is the whole of why this is order-independent.** Lengthening only the
later collider would make the public symbol a function of which position the walk reached first,
which §9 forbids and which `names.adopt` already refuses for the same reason: a field must never
be typed by a *sibling* position's name. Lengthening all of them makes each name a function of
the SET of colliding positions, and that set is a function of the one document — so the name is
recomputable after the walk, and no census over the run enters.

The DEDUP is confined to one module, never compared across modules, because a name's module is
its namespace.

**The COLLISION rule is not, for a name §1 exports (2026-10-30).** This clause used to confine
both, on the ground that §9 forbids a document's output depending on which other documents the run
includes — and that ground is intact, but it is about the RUN and the collision scope is the
BUNDLE, which §9 now says in as many words. So: one module for every position, and **the domain
for a position the surface exports**, read off the bundle and never off the run's document set.
`names.COLLISION_SCOPE` states it beside `names.SCOPE`, which keeps the dedup's scope unchanged.

*What this costs:* a long name becomes the exception it was meant to be, arising only where one
document genuinely says `context` twice. The failure it avoids is the one the upstream v9 SDK
measures — 1,092 of its 4,360 classes are numbered variants, `WholesaleFeedEvent1` through
`WholesaleFeedEvent9` — because a numeric suffix carries no information about which position it
names, where an ancestor segment does.

**The two fallbacks are new on 2026-10-26, and each replaces a refusal with a derivation.** A
missing root title used to refuse, and a branch with no identity used to refuse. Neither is an
acceptance fact: a symbol is not something a document states about an instance, so deriving one
from the document's own path or from its own branch order neither widens nor narrows, and it
costs no approximation. Both fallbacks are functions of the one document — the file stem is the
same whichever documents the run includes, and the branch index is document order — so §9's rule
against deciding a document's output by a census over the run holds. A title is still preferred
wherever one exists, because a derived name reads worse; what changes is that its absence is no
longer fatal.

### A union root: the base, the branches, and how a payload reaches its branch

A `oneOf`/`anyOf` root emits a **base** carrying `BranchDispatchMixin` plus **one class per
branch**, and the base's name is what every referrer imports. A branch whose schema is a `$ref` is
a class with **two bases**: the target, which supplies the fields, and the union's base, which
supplies the dispatch.

Four mechanics make it work, each because one of the others does not reach a path:

- **`__get_pydantic_core_schema__` on the mixin returns the branches' union**, which covers every
  path Pydantic validates *through*: a nested field, a `TypeAdapter`, `model_validate`.
- **`__new__` on the mixin covers `Base(**data)`**, which no schema can reach, because
  `BaseModel.__init__` validates with the object already allocated. Direct construction therefore
  validates twice and is idempotent; `model_validate` stays single-pass.
- **The class that gets the union is the one that *declares* `_branch_models`.** A class that
  inherits it keeps its own schema, which is the whole of subclass support: a branch keeps its own
  schema, and so does a consumer's refinement declared elsewhere.
- **The union is the validator, not the serializer.** In the serializer slot the class has no
  serializer for an instance of itself: the union's serializer matches no branch, infers a model,
  finds the same union and recurses. So the serialization slot carries a wrap serializer built
  from the plain model schema the class would otherwise have had, which terminates.

  *What that schema is, settled 2026-10-27, because the sentence above admits two readings and
  both lose data.* Read as "the base's own plain schema, alone", a BRANCH reached through a
  base-typed field serialises as the base's fields and the branch's own are dropped silently —
  measured, it comes back as `{"shared": null}`. Read as a union of the branches plus that
  schema, a BASE instance matches no arm under a smart union and the serialiser falls through to
  the circular reference the mechanic exists to avoid. Both readings were live: the second is
  what the code does, and it became reachable for the first time at §14 step 9, because while a
  root declaring `properties` was refused every base had no fields and matched the plain arm
  trivially.

  **The serialiser dispatches on the instance's own class, and each class serialises through its
  own plain model schema.** A branch serialises the branch's fields; a base serialises the base's.
  That is not a union in the serializer slot at all, which is why it terminates — there is no
  arm to fail to match and nothing to infer. It also states the obvious invariant the two
  readings each broke in one direction: **a value serialises as what it is.** A base instance is
  a legitimate value, because `__new__` covers `Base(**data)` and validates it, so the slot owes
  it an answer rather than treating it as unreachable.

The emitter writes three facts onto the base that are not recoverable at runtime: `_ROOT_REQUIRED`,
the fields the root requires as opposed to the ones that select a branch; `_BRANCH_DISCRIMINATOR`,
the property every branch pins a `const` on (the first dispatch source below), which the mixin
reads to build the discriminated union, and which is empty where dispatch is the third source or
is declaration order; and `_branch_combinator()`, `anyOf` or `oneOf`, because a **validation
error** has to name a JSON Schema keyword and a payload satisfying no branch fails each branch at
field validation, where Pydantic reports `missing`. (That is a runtime refusal of a payload, not
§2's refusal of a document — the compiler refuses no document for a union.)

Branches subclass the base, so they do not exist while the base is built: the hook returns the
base's own schema then, and the declaring module calls `model_rebuild(force=True)` afterwards.

**Every keyword beside the combinator compiles onto the base, and every branch inherits it.**
Draft-07 applies a root's `properties`, `required`, `additionalProperties`, `allOf` and rule
keywords to the same instance a branch describes, so they compile as they would on any class —
fields, `extra`, bases, rules — onto the base, and a branch composes its own with them. A root
`properties: {}` beside a union declares no field and contributes nothing. §8 says how a branch
class is then compared: against its branch node read under the root's siblings, so an inherited
field is a fact the branch's node states.

**Which branch a payload is, is derived from bundle data, never from a hand-written map.** Three
sources, in order:

1. **A `const` every branch pins on one shared property.** The union carries
   `Field(discriminator=<property>)` and the key alone selects the branch, so Pydantic reports
   against that branch rather than against all of them.
2. **A key the bundle's manifest states.** `manifest.task_result_resolution` names the
   discriminator field and a template resolving a schema from it, and `manifest.tools` is the
   table. Such a union emits as a mapping keyed by that field: its discriminant is in the
   envelope, not in the payload.
3. **Branches no instance satisfies twice.** Where the branches are pairwise disjoint, the
   payload selects its own branch and the order they are tried in cannot change which one it
   reaches. Disjointness is derived from the branches themselves: one property pinned to
   **disjoint value SETS**, a `required` name one branch declares and another forbids, **one
   branch forbidding a VALUE another pins**, or scalar branches of different `type`.

   *The first separator reads SETS and not single values, decided 2026-10-29.* An `enum` is a
   set of pinned values and a `not: {"enum": [...]}` is its complement, so two branches whose
   sets do not intersect are disjoint for the same reason two different `const`s are — the
   single-value case is the one-member set. Reading only single values made
   `core/postal-country-system.json#/anyOf` inseparable on 12 pairs, every one involving the
   branch pinning `country` to `["DE", "CH", "AT"]` or the branch pinning its complement, while
   all ten branches are pairwise disjoint in fact and the emitted classes dispatch
   deterministically: ten probed payloads, document and model agreeing on every one,
   `{"country": "DE", "system": "plz"}` reaching `PostalCountrySystemPlz` and
   `{"country": "ZZ", "system": "custom"}` reaching the complement branch. That one union
   accounted for **116 of the 235 approximated facts**, declared for a disjointness the
   derivation could not see rather than one the document does not have. A pair the
   derivation cannot separate is treated as overlapping, because admitting a union on an unproven
   disjointness is the defect this source exists to avoid.

   *The third separator is new on 2026-10-27, and it exists because neither of the others was
   sound for a real union.* `media-buy/sync-catalogs-response.json` has a branch forbidding
   `status == "submitted"` and a branch pinning `status` to that very `const`. Every instance of
   the second carries a value the first forbids, so the two are disjoint in fact — and no
   separator reached it: the pinned-`const` separator needs BOTH branches to pin and the first
   pins nothing, while the required/forbidden separator needs the NAME forbidden outright and the
   first forbids only the value.

   The verifier reached the right answer by an unsound route, which is how this was found. It
   collected every singleton `required` under a `not`, so it read
   `{"properties": {"status": {"const": "submitted"}}, "required": ["status"]}` as forbidding
   `status` by NAME — which the document does not say. Here the conclusion was right and the
   reasoning wrong; at a branch pinning some other value it would be wrong in both directions,
   separating a pair that overlaps. **That over-reading is a defect whether or not this separator
   lands, and it goes either way.**

A union matching none of the three emits a plain `A | B` over its branches and **declares an
WIDENED approximation at the union's pointer where the combinator is `oneOf`, and nothing at all where it is `anyOf`.**

*This replaces a refusal on OVERLAP, 2026-10-26.* The old sentence said a branch is never chosen
by trying each and keeping the first that validates, because overlapping branches make that
answer a property of declaration order rather than of the payload — and that reasoning is
unchanged and is exactly what the approximation now records. What changes is that the
order-dependence is no longer worth a document. `A | B` admits the union of the branches, which
is what the document admits, so **nothing widens and nothing narrows** — **for `anyOf`.**

**For `oneOf` it is false, and an inseparable `oneOf` owes TWO declarations (decided
2026-10-29).** `oneOf` admits an instance satisfying exactly one branch; `A | B` admits one
satisfying two. The old sentence said "the schema half still enforces exclusivity", and that is
true only of a caller who invokes `strict_validate`: measured on `core/evaluator-spec.json#/oneOf`
with `{"evaluator_id": "e1", "agent_url": "https://x.example/a"}`, `Draft7Validator` refuses it
and `EvaluatorSpec.model_validate` returns `EvaluatorSpecEvaluatorId`. The class carries
`strict_validate` and `model_validate` does not route through it, so the type is wider than the
document for every caller who uses pydantic's own entry point.

So the dropped exclusivity is a WIDENED fact and is declared as one. **It is ONE declaration and
not two, which REVERSES the "owes TWO declarations" half of the 2026-10-29 decision on
2026-10-30.** The reversed reasoning was that "the two losses are different: which branch an
overlapping payload lands in, and that it is admitted at all". Both losses are real, and they are
**coextensive**: the branch question arises only for the payloads the widening admits, at the same
pointer, over the same values. Two declarations therefore say one thing twice, and saying it twice
costs four changes to §8's instruments — a site key that carries a kind, a pointer in two places
at once, a split of a shared §5 cell, and an upstream issue that does not exist. Measured by
implementing it: the two collided on a `(document, pointer, keyword)` site and **which kind
survived was path-dependent**, 15 sites keeping the WIDENED and 3 the UNDERDETERMINED. That is a
substitution, which §2 forbids.

**The kind is the fact §8 grades, and the other loss is the REASON carried on it.** An inseparable
`oneOf` declares WIDENED, because the model admits values the document refuses and a consumer sees
that through `model_validate`; its reason also states that such a payload's branch is decided by
declaration order, which the document does not decide. Nothing is dropped — the kind moves to the
one §8's DRAW can prove, by handing the class a value the document refuses.

**And the `anyOf` case then declares NOTHING, which is what retiring UNDERDETERMINED means.**
`anyOf` admits an instance satisfying at least one branch and so does `A | B`, so the model is not
wider and nothing is owed but the branch choice — invisible to all three checks, as §2 says. The
reading to expect is `approximated` unmoved with the kinds re-split: the inseparable `oneOf` sites
leave the UNDERDETERMINED column for the WIDENED one, deterministically and with no site holding
two.

**The attribution is OURS until an issue exists (decided 2026-10-30).** A union whose branches are
not separable is a defect in the union — the bundle already writes the idiom that separates them,
each branch forbidding a name the other requires, so the fix is a copy from elsewhere in the same
bundle. That makes it a candidate for an upstream attribution and not an upstream attribution:
§2 keys one to an entry of `codegen/attribution.py` naming an issue, an entry with no issue is a
build failure, and §10's fifth clause is that every upstream attribution names a LIVE issue.
Minting a number for an unfiled gap creates exactly the defect that clause prevents, so §14's rule
governs — **an unfiled gap IS ours.** Filing the issue reclassifies these sites and changes no
type, no emission and no count.

Where nothing overlaps there is no order to depend on and no approximation, which is why the third
source is a dispatch and not a relaxation.

A hand-written map per document is still not a dispatch source: it is complete with respect to
itself, so a branch added upstream leaves it silently wrong — and unlike declaration order it
would be wrong without saying so, where an approximation says so by construction.

---

## 5. How each keyword compiles

The draft-07 keywords the bundle uses. An answer is given per position where the positions differ.

**The grids in this section are generated from `codegen/keywords.py` and are the cells as they
stand before §2's widening rule lands.** Every clause reading "→ refused" in them is a decision
§2 replaced on 2026-10-26, and the cell that carries it has not yet been rewritten. *"The
widening each row takes"* at the end of this section is the hand-written half and states the cell
each such row takes; the generator writes those sentences into the grids when the cells change,
and until then the grids and that subsection are read together. Nothing hand-edits a grid: a cell
is the one place a keyword decision lives, and a grid is its rendering.

### Structure

<!-- generated from codegen/keywords.py -->
| keyword | compiles to |
| --- | --- |
| `type` | A scalar word → `str` / `int` / `float` / `bool`, unless a constrained type or `format` selects one. `object` with `properties` → a class; without → `dict[K, V]`. `array` → `list[X]`. `null` → `None`. A LIST of words → `A \| B`, each sibling keyword going to the one type word that can carry it. Absent → `Any`; absent beside `properties` → an object, where an enclosing node applies `type: object` to the same instance, and refused otherwise. An enclosing `oneOf` APPLIES a type word it does not state, where TWO OR MORE of its branches admit that type vacuously: `oneOf` admits an instance satisfying exactly one branch, so an instance two branches both admit is refused by the combinator, and the type is excluded by the document itself. This is EXACT and not a widening — it reads a constraint the document imposes rather than relaxing one — so it owes no declaration and no rung. It holds at `oneOf` ALONE: at `anyOf` an instance one branch admits is admitted, so the same derivation there would state a constraint the document does not (`adcp-client-python-10l.69`, decided 2026-10-29). |
| `properties` | A class with one field per key. An entry whose subschema ADMITS NOTHING — `false`, or `{"not": {}}`, which draft-07 makes the same schema — is NOT a field: draft-07 validates a `properties` entry only where the key is PRESENT and that entry then always fails, so the document's statement is that the key MAY NOT APPEAR and it says nothing at all about a value. The accepted set is the accepted set of `not: {required: [key]}`, which the `not` row already compiles to a `ForbiddenGroups` rule, so the key joins that rule on the nearest enclosing class and no field is declared. EXACT, not wide: nothing is dropped reaching it and no declaration is owed. `extra` is NOT the carrier — all three sites of the bundle state `additionalProperties: true` beside the forbidden key, so closing the class would refuse the other extras the document admits. Where `required` ALSO names the key the document admits nothing, and so does the class without an arm of its own: the `required` row's undeclared-name field refuses a payload omitting the key and this rule refuses one carrying it. ROOT beside a union → fields on the base, inherited by every branch. PROP / ELEM / MAPV / DEF → a nested class. BRANCH → the branch class. CONJ → fields of the composed class. A property two conjuncts declare is one field: its constraints intersect by §2, and two object declarations compose as an `allOf` of the two at that property; an empty intersection — two type words, disjoint enums — refuses, because the document admits nothing there. A `default` or a `description` is not a constraint, and the document's own statement wins over a base's. RULE: under `if` → the values a `Match` clause tests, read only where `const` or `enum`; under `then` / `else` / `not` → nothing. |
| `required` | The named fields are required: no `\| None`, no default. Naming a property NO declaration declares → a required field of type `Any`, and it is EXACT rather than wide: `required: ['x']` with no entry for `x` admits an object carrying `x` with any value, which is what the `type` row already gives an absent type word, so nothing is dropped and no declaration is owed. The model-only `properties` entry it renders is the empty schema, which states nothing the document does not. `required: []` → nothing. ROOT beside a union → required on the base's fields, and the names recorded in `_ROOT_REQUIRED`, so a refusal can separate a field the root requires from one that selects a branch. BRANCH → the branch class's requiredness, and the third of the branch-naming choices. CONJ → unioned into the composed class's `required`; a `required`-only conjunct → the overlay. RULE → a presence rule: `RequiredGroups`, `ForbiddenGroups` under `not`, the keys a `Match` clause tests under `if`, `ConditionalRequired` / `NegatedConditional` under `then` / `else`. |
| `definitions`, `$defs` | Nothing by itself: a bag of named subschemas. Each entry is declared on demand when a `$ref` names it, as the node's own kind, under `<Root><Key>`. |
| `$ref` | Another document's root → an IMPORT of that module's symbol; nothing of the target is copied into the module, and in the document of record (§3) the target is inlined unchanged. A fragment of another document → an import of a symbol the target declares. Local `#/…` → the entry decided on demand in this module; a cycle refuses. An annotation sibling → the sibling's description wins. A CONSTRAINING sibling → nothing, and REPORTED: draft-07 ignores every sibling of `$ref`, so the keyword constrains no instance and the document's accepted set is the target's alone. The record keeps the key, because §3 drops none; the declaration's cell says it compiles to nothing at this co-occurrence; and the report names it, because a key that reads as a constraint and is inert is worth reading once. Refusing it instead would refuse a document whose accepted set its own draft decides, and letting the referring value win would make the record state an acceptance fact the bundle does not — §9's last rule. KEY → the key type. BRANCH of a root union → a class with two bases; of a nested union → a member type. CONJ → a BASE where the target is a class declaring fields. Where it is not — a scalar, an enum, a container, or a union root — it is not a class a model can extend: the target is this node's own TYPE, and the other conjuncts and the `allOf`'s siblings constrain it, which is §2's intersection at a node that declares no fields of its own. A UNION root beside a node that DOES declare fields distributes: conjunction distributes over disjunction, so `(A | B) and C` is `(A and C) | (B and C)`, and the node is a union whose branches each take one of the target's branches as a base and add the node's own fields. Each branch of a union root is a class declaring fields, so this is the CONJ rule above applied once per branch and not a second answer. A property the node and the target's branch BOTH declare is one field taking §2's intersection, exactly as the `properties` row at CONJ states it for two conjuncts — the node's declaration does not shadow the branch's, and two `const`s intersect to the pin where they agree and to nothing where they differ. A distributed branch whose intersection is EMPTY is DROPPED, and the node refuses only where every branch is: `(A \| B \| C) and D` with `A and D` empty is exactly `(B and D) \| (C and D)`, so the accepted set is unchanged and nothing is approximated. The emptiness must be PROVED from the pins the two sides state — disjoint `const`s, disjoint `enum`s, disjoint type words — which is the same test the empty-intersection row names; an intersection this compiler cannot compute is the restatement row and not this one. |
<!-- end generated -->

### Values

<!-- generated from codegen/keywords.py -->
| keyword | compiles to |
| --- | --- |
| `const` | `Literal[value]`; the type word is not restated, since Pydantic renders it. A `format` beside the pin compiles to NOTHING and the pin alone is rendered, because a fixed value either satisfies the format or the node admits nothing: the pin is checked against the format, and where it satisfies it the `Literal` is already strictly tighter than any type the format would select, while where it does not the node is §5's empty intersection and refuses upstream. So no fact is dropped, and the cell declares the `format` as rendering nothing at this co-occurrence (`adcp-client-python-10l.70`, decided 2026-10-29). A `str`, `bool` or `int` value; an object, array, `null` or float refuses. On a branch's property → also the second of the branch-naming choices. AT a branch node, pinning the whole branch → the branch is a scalar: a `Literal` member of the union. Where EVERY branch of a root union is a scalar there are no branch classes to declare, so the root emits as an alias over the union of their types — `Literal['asap'] | AwareDatetime` — and not as a base with branches. A root union with a scalar branch beside a class branch → refused by name: the root symbol is a class or an alias, no structure in §4 carries both, and the first document to state one decides it rather than taking a rendering nothing has exercised. RULE: under `if` → a `Match` clause's value; under `then` / `else` / `not` → nothing. |
| `enum` | A named node → `StrEnum` / `IntEnum`, base read off the members; `enumDescriptions` → member docstrings. An untitled BRANCH of a root union → a `Literal` of the members. Mixed member types, an empty list, or a duplicate member → refused. Two members whose spellings yield one Python name → a `Literal` of the members and NOT an enum class (decided 2026-10-29). The collision exists only because an enum mints a Python IDENTIFIER per member; a `Literal` needs none, so both values are carried exactly as the document spells them and nothing is dropped. This is the same answer the row already gives an untitled branch of a root union, reached by a second route. Refusing instead cost **21 of the 95 refusals** for one node — `formats/canonical/html5.json`'s `clicktag_macro`, whose `clickTag` and `clickTAG` both spell `CLICKTAG` — including `core/product.json`. The cost is that one node gives a string-literal union rather than an enum class, which is a DX difference and not a correctness one; dropping a member, which the old clause rightly refused to do, remains forbidden. ROOT → the enum with a module-level `strict_validate`. PROP → a nested enum. KEY → a `Literal` of the members as the mapping's KEY type, which pydantic renders back as `propertyNames: {enum: […]}` — the document's own keyword, rendered and gradable; where the key node carries a `title` the `StrEnum` is the key type and renders the same way. CONJ beside a `$ref` whose target is an enumeration → §2's intersection of the two vocabularies, rendered as a `Literal` over the TARGET's MEMBERS and not over their raw values. The two dump identically — `{"enum": [the members], "type": "string"}` — so they state the same fact either way, and the member form keeps the imported symbol a caller can name: where two renderings state one fact, DX decides. A vocabulary the target does not contain is the empty intersection and refuses, by the same rule that refuses a member the node's own constraints exclude. RULE: under `if` → `Match` values; else nothing. |
| `default` | On a REQUIRED property → dropped and reported, because no rendering makes a field both required and defaulted. On a node that becomes an alias → no slot. PROP → the field's default; `None` is a default, absence is not. |
<!-- end generated -->

### Strings

<!-- generated from codegen/keywords.py -->
| keyword | compiles to |
| --- | --- |
| `pattern` | `pattern` on the type, as a named alias. On `format: uri` → selects the type instead, and the pattern stays with the schema half. The regex engine is derived per class, because a pattern using look-around needs Python's engine rather than Rust's. ROOT → the root alias over it. ELEM / BRANCH → the alias as the element or member type. KEY → an annotated `str` key. RULE → nothing. |
| `format` | Selects a TYPE where the document's draft asserts the format and a type is named: `date-time` → `AwareDatetime`, `date` → `datetime.date`, `uri` → a URL type chosen by `pattern`. Otherwise rides as `json_schema_extra={"format": …}` on the field. A `uri` beside another string constraint → refused: a URL type carries none. ELEM / MAPV with no type selected → a named alias carries it. BRANCH → the selected type as the member. |
| `minLength`, `maxLength` | `min_length` / `max_length` on the type, as a named alias. On a URL type → refused, not representable. A node stating the bound and **no `type`** is `Any` (§5's `type` row, "absent → `Any`"), which carries no bound: the keyword is dropped at rung KEYWORD — the type is unchanged, which is what that rung is — and the drop is declared. Selecting the type the bound implies instead would NARROW, because a typeless node admits an instance of every type and the bound constrains only one of them. ROOT → the root alias. ELEM / MAPV → the alias inside the container. KEY → the key type, which Pydantic renders back as `propertyNames.minLength`. RULE → nothing. |
<!-- end generated -->

### Numbers

<!-- generated from codegen/keywords.py -->
| keyword | compiles to |
| --- | --- |
| `minimum`, `maximum` | `ge` / `le` on the type: a standard Pydantic type where one says exactly this, a named alias otherwise. ELEM / MAPV → the alias inside the container. BRANCH → the alias as the member type. RULE → nothing. |
| `exclusiveMinimum`, `exclusiveMaximum` | `gt` / `lt` on the type, **never `ge` / `le`**. The bundle distinguishes `minimum: 0` from `exclusiveMinimum: 0`, and the two differ on exactly one instance, so rendering either as the other makes a field accept a zero its document refuses or refuse a zero its document accepts. |
| `multipleOf` | Unused by the bundle. The first document to carry one refuses by name, rather than taking a rendering nothing has exercised. |
<!-- end generated -->

### Arrays

<!-- generated from codegen/keywords.py -->
| keyword | compiles to |
| --- | --- |
| `items` | `list[X]`, X decided by the same walk and named where it needs a symbol. A list-valued `items` → refused: that is tuple validation. ROOT array → `RootModel[list[X]]`. RULE → nothing. |
| `minItems`, `maxItems` | `min_length` / `max_length` on the annotation of the **array's own type**, at every position. `minItems: 0` states nothing. `constraints` declares it once, generically, as `type NonEmptyList[T] = Annotated[list[T], Field(min_length=1)]`. A node stating the bound and **no `type`** is `Any` (§5's `type` row, "absent → `Any`"), which carries no bound: the keyword is dropped at rung KEYWORD — the type is unchanged, which is what that rung is — and the drop is declared. Selecting the type the bound implies instead would NARROW, because a typeless node admits an instance of every type and the bound constrains only one of them. PROP → on the field. ELEM / MAPV / DEF → the container's type must be named to carry it. BRANCH → on the branch's own type, never on the field holding the union. RULE → nothing. |
| `uniqueItems` | A `UniqueItems` rule on the class holding the array, plus `json_schema_extra={"uniqueItems": true}` on the field so it is graded, and the keyword is stripped off the array's own declaration. Where no class encloses the array → a `Distinct` after-validator on its own annotated type, beside the same `json_schema_extra`. |
| `contains` | An existential quantifier — `items` constrains every element, `contains` says at least one matches — and the model states the **predicate**, not a transcription of the subschema. Every position → an `AtLeastOne` after-validator on the array's own annotated type, because no class has a kind for it: `AtLeastOne(pinned=((property, const), …))` where the subschema requires properties pinned to a const, `AtLeastOne(values=(value,))` where it is a bare `const` or a one-member `enum`. A property KEY is not required to be a Python identifier, so the predicate is a tuple of pairs and not keyword arguments. Any other predicate — a bound, a pattern, a nested `contains`, a `$ref` — → the keyword is CARRIED and the schema half answers alone: a transcription of the subschema is the thing this row declines to emit, and the first document to state such a predicate decides its rendering. RULE position → a `Match` MEMBERSHIP clause, `value in field`, and no validator. |
<!-- end generated -->

### Objects

<!-- generated from codegen/keywords.py -->
| keyword | compiles to |
| --- | --- |
| `additionalProperties` | The empty schema `{}` IS `true` and is read as `true` everywhere below, never as a typed value schema. On a class: `false` → `forbid`; `true` → `allow`; typed → `allow` with a typed `__pydantic_extra__`; absent → `ignore`. **A class DECLARES the `extra` the document gives it and never inherits it** (decided 2026-10-29): pydantic merges `model_config` along the MRO, so a branch composing TWO bases takes whichever value the later base happens to carry, and `absent → ignore` on that base silently overrides an `allow` the document states. Measured on `content-standards/get-content-standards-response.json#/oneOf/0`, where the union base states `allow` from the root's envelope conjunct and the composed target's default `ignore` wins the merge, so the model drops keys the document admits. The value is read from what the document states at the class's own pointer after the document-side fold — which is where the root's conjunct arrives — and written on the class, so MRO order decides nothing a document states. On a mapping (no `properties`) → the VALUE type; `true` or `{}` → `Any`; `false` → refused, it admits only the empty object. Beside `patternProperties` → refused, two value schemas. `false` on an `allOf` overlay would reject the fields its sibling conjunct contributes, which is why `true` is the only value an overlay can carry. ROOT beside a union → the same, on the base, inherited by every branch; a branch stating its own composes with it by the CONJ rule below. CONJ → `true` is the identity and contributes nothing, `false` on any conjunct closes the composed object, and two typed ones intersect their value schemas; a typed conjunct beside a `true` one is a widening and refuses. |
| `patternProperties` | A mapping whose KEY carries the pattern: `dict[Annotated[str, StringConstraints(pattern=…)], V]`, which Pydantic renders back as `patternProperties` — the document's own keyword. More than one pattern → refused: that is a value schema per key case. Beside a non-`false` `additionalProperties` → refused. |
| `propertyNames` | The mapping's KEY type: a `$ref` → that type; `minLength` / `maxLength` → a length-bounded `str`; `pattern` → an annotated `str`; `enum` → a `Literal` of the members, which pydantic renders back as this very keyword; `anyOf` → a union of key types. Beside `patternProperties` → the key type carries both, by §2's intersection: each states a constraint on the same key. On a CLASS with declared `properties` → checked against the declared names when the class is emitted and carried nowhere, because those names are fixed and known; a declared name the constraint refuses is a contradiction in the document and refuses by name. Where that class also admits extras, a key beyond the declared names is checked by the schema half alone, and the model is looser than its document there, which §2 permits. RULE position → nothing on the model: a rule position constrains which keys a conditional *tests*, so there is no key type to annotate and no value to annotate. |
| `minProperties`, `maxProperties` | On a class → a `PropertyCount` rule. `minProperties` is written only where `additionalProperties` is stated, because a dropped key would make the rule refuse what the document accepts; `maxProperties` needs no such gate, since a dropped key only lowers the count. On a mapping → `Field(min_length / max_length)` on the dict's type, because a `PropertyCount` rule counts declared fields and a dict has none. |
| `dependencies` | The list form → a `Dependencies` rule: if A is present, B is required. The schema form refuses by name on the first occurrence, rather than being skipped. |
<!-- end generated -->

### Combinators and conditionals

<!-- generated from codegen/keywords.py -->
| keyword | compiles to |
| --- | --- |
| `allOf` | ROOT with no union beside → `$ref` conjuncts are BASES, inline conjuncts are fields and rules of this class; beside a union → the same, onto the base: `$ref` conjuncts are the base's bases and inline conjuncts are its fields and rules, and every branch inherits them. PROP / ELEM / DEF → the same reader at the node's own pointer. BRANCH → the branch class composes, with the union base first. CONJ → the same rule applied to the conjunct's own conjuncts. RULE: under `not` → single-group conjuncts merge into one group; else nothing. |
| `oneOf`, `anyOf` | Presence-only, every branch `required`-only → a `RequiredGroups` rule naming the combinator. Presence-only where a branch also `not`s a group of `required` → a `PresenceGroups` rule naming the combinator, whose clauses are the branches: each clause carries its OWN required group and its own forbidden groups, because the `not` is per branch — a `ForbiddenGroups` over the union of them forbids every group unconditionally and refuses a payload the document admits. Structural branches at ROOT → the base plus one class per branch. Structural branches nested, with nothing beside the combinator → one type `A \| B`. A sibling a CLASS carries → that same base-plus-branches case, at a union in ANY position: the siblings become the base, each branch becomes a subclass narrowing what it narrows, and the union is over the subclasses. A sibling no class carries refuses, because it is a conjunction with every branch and `A \| B` has no slot for a fact of its own. For `oneOf`, `A \| B` admits an instance satisfying two branches and the schema half enforces exclusivity. A union whose branches declare the same properties with the same `required`, and differ only in the `const` or `enum` each pins on some of them → one class: each such field admits the union of the branches' values, and one rule whose clauses are the branches themselves — one clause per branch pinning that branch's values, satisfied when the instance matches at least one clause. A branch that differs in a type, a bound, a format, a nested case or its `required` is a structural branch and takes the base-plus-branches answer. For `oneOf` the schema half enforces exclusivity, as it does for `A \| B`. KEY → a union of key types. CONJ → one class per branch over the composed bases. RULE: under `not` → the union of the branches' groups; else nothing. |
| `if` | A `Match` clause list where it states `required` plus `properties` with `const` or `enum` values; otherwise nothing, and the schema half answers. With `then` / `else` → a rule on the nearest class. |
| `then`, `else` | `ConditionalRequired` / `NegatedConditional` from its `required` and a single-name `not`. Its `properties` → nothing on the model; the schema half narrows the value. |
| `not` | `not: {required: …}`, and `anyOf` / `allOf` of those → a `ForbiddenGroups` rule. Over a `const` or `enum` → a `NotValue` after-validator on the value's own annotated type. Any other case → nothing on the model; the schema half answers and the ceiling is named. `not: {}` admits nothing, which the typeless `Any` carries — at a node whose OWN accepted set is the thing being typed. As a `properties` entry it is not that node: the enclosing object still admits every instance without the key, and the `properties` row answers it there with the `ForbiddenGroups` this row already decides for the keyword's other spelling. |
<!-- end generated -->

**`oneOf`'s CELL SPLIT IS WITHDRAWN (2026-10-30, same day it was decided).** It was decided
hours earlier for one reason — that an inseparable `oneOf` is a WIDENED fact §8's COMPARISON had
to see, and one shared cell could not answer both combinators. The comparison is deleted, so the
reason is gone with it: `oneOf` and `anyOf` keep the one cell, because what differed between them
was never the lowering, only what a text diff could notice about it.

The document-side disjointness fold decided beside it is withdrawn for the same reason. It existed
to stop a SEPARABLE `oneOf` reporting `missing` at every union root, and nothing reports `missing`
any more.

**What survives is the fact itself, and the draw proves it.** An inseparable `oneOf` admits a
payload the document refuses — measured on `core/evaluator-spec.json#/oneOf`, where
`{"evaluator_id": "e1", "agent_url": "https://x.example/a"}` satisfies two of three branches,
`Draft7Validator` refuses it and `model_validate` returns `EvaluatorSpecEvaluatorId`. That is a
WIDENED declaration and §8's draw hands the class exactly such a value. The cell's own text still
says "the schema half enforces exclusivity", which is true only of a caller who invokes
`strict_validate`; correcting that sentence is a cell edit and not this rendering's.

**ONE VOCABULARY IS ONE TYPE, COLLECTED BEFORE EMISSION (decided 2026-11-02).** The bundle
states the same value set at many positions and says so in many spellings, and compiling each
position independently turns one protocol concept into several Python types that are not
interchangeable. Measured:

| reading | |
|---|---|
| distinct string-enum vocabularies in the bundle | **807** |
| declared at more than one position | **663**, covering **16,135** positions |
| enum classes emitted for them | **897** |
| distinct member-sets among those classes | **715** |
| member-sets emitted MORE THAN ONCE | **128**, across **310** classes |

One member set is emitted as `Status`, `BuyerAssetAcceptance` **and** `HostReceiptStatus` — seven
classes, three names, one concept. A function annotated with one refuses the others and
`isinstance` fails across them, so a consumer meeting the same protocol value in two messages
cannot pass it between them. §4's identity rule does not reach this: it collapses nodes of
IDENTICAL CONTENT, and these are the same vocabulary spelled independently.

**So the walk COLLECTS vocabularies before it names anything, and every position references the
one type.** The alias is the emission's single declaration of that value set; a position holds a
reference to it and never a copy.

**The NAME comes from the bundle and from nowhere else**, which is §4's standing rule and is what
makes this derivable rather than a mint:

- **the bundle gives exactly one `title` — 203 vocabularies.** That title is the name. The widest
  is titled "Authentication Scheme" at 94 of its 259 positions, which is enough: one title, no
  conflict.
- **the bundle gives no title anywhere — 457 vocabularies.** These are **NOT collapsed across
  documents.** Nothing names the concept, and §4 already refuses to mint a public name no document
  states. Two fields sharing a member set by coincidence are not one type, and without a title
  there is nothing to tell coincidence from identity.
- **the bundle gives conflicting titles — 3 vocabularies.** A decision, brought to the owner with
  the titles and the positions. Not resolved by picking the commonest.

**And this fixes the `const` override by construction rather than by a second rule.** Where the
root's `enum` and a branch's `const` are the same vocabulary, both positions reference the one
alias, so the branch's pin is `Literal[Alias.MEMBER]` because there is no other member to name.
The rule below stands as the general case — a pin whose field has no collected alias — and stops
being the mechanism for the discriminator case that produced the 362.

**TWO RENDERINGS THAT DO NOT TYPE-CHECK, and both are cells (decided 2026-11-02).** Measured
against the shipped package: mypy reports **440 errors in the generated tree — 362 `[assignment]`
and 78 `[list-item]`** — so the wheel cannot honestly ship `py.typed` (`architecture.md`), and a
consumer's checker sees `Any` instead of any of this. Each has one cause and neither costs the
architecture anything.

**A `const` pinning an enum member emits the MEMBER, not the raw value.** `core/registry-event.json`
states `enum: [...]` at its root's `event_type` and `const: "property.created"` at its branch's. The
`enum` cell gives `EventType`, a `StrEnum`; the `const` cell gives `Literal['property.created']`, a
`str` literal. **Those are not narrower-and-wider, they are different vocabularies for one field** —
`str` is not a subtype of the enum, so the branch is an INCOMPATIBLE OVERRIDE rather than a
refinement, and that is the whole of the 362.

The fix keeps base-plus-branch inheritance, which this section does not reopen. Measured on all
three candidate cases:

| case at the branch | mypy | `isinstance(branch, base)` |
|---|---|---|
| `Literal['property.created']` — today | **error** `[assignment]` | True |
| `Literal[EventType.PROPERTY_CREATED]` | **clean** | True |
| a generic base parameterised per branch | clean | True |

So the second is taken: **where a `const`'s value is a member of an enum the same field's enclosing
declaration compiles to, the pin is that member.** An enum-member literal IS a subtype of its enum,
so the override is legal; `isinstance` is unaffected; and pydantic still accepts the raw wire string,
because the enum is a `StrEnum`.

**The stronger rule — "a `const` compiles to a StrEnum of its own" — is refused, and by two facts
rather than a preference.** First, Python forbids it from working: an enum carrying members cannot
be subclassed (`TypeError: <enum 'Sub'> cannot extend <enum 'E'>`), so a branch's own StrEnum could
never be a SUBTYPE of the root's, and the override would stay incompatible with a one-member class
added per pin. Second, half the pins have nothing to enumerate: of **37,999 `const` positions,
19,036 sit at a field whose declaration carries an enum and 18,963 do not — and 2,975 of those are
`bool` and 2,439 are `int`.** A boolean pin has no string vocabulary to join.

So the condition is necessary and not a convenience, and it is exactly the declaration being
overridden — not "an enum appears somewhere in the document", which is a looser reading and would
pin a member of an enum the field does not take. Where no enclosing declaration gives the field an
enum there is no override to conflict with, and `Literal[value]` stands as §5 already has it.

**A `default` is emitted through its annotation's OWN TYPE, and the document's `default` survives
it.** The field must carry a value of the type it declares; a raw JSON literal against a model or
an enum annotation is the defect, **and it reaches callers and not only checkers**: pydantic does
not validate a plain default, so `CanonicalFormatNativeInFeed().slots[0]` was a `dict` and reading
`.asset_group_id` off it raised `AttributeError`. Measured over the emitted tree by pydantic's own introspection —
2,552 classes — **146 sites over 66 documents disagree**, and the population is not where this
rule first read as though it were:

| annotation | sites with a default | disagreeing |
|---|---|---|
| a model | 2,229 | **0** |
| a list of models | 1,232 | **14** (72 list items) |
| an **enum** | 1,040 | **126** |
| a list of enums | 408 | **6** |
| a dict of models or enums | 46 | 0 |

**No bare-model default exists anywhere in the bundle**, so the case this rule was first written
about has no population; the defect is a list of models and, far more of it, a plain enum —
`asset_source: AssetSource | None = 'buyer_uploaded'`, 126 times across 57 documents. The two
carry different error codes and belong to this rule rather than to §3a's catalogue: 78
`[list-item]` and **98 of the 362 `[assignment]`**, where the remaining 264 are the override
incompatibilities the catalogue dissolves.

**And `default_factory` alone is NOT the mechanism, because it drops the document's fact.**
Measured on pydantic 2.13.5: a field carrying `default_factory` renders `model_json_schema()` with
**no `default` at all**, where a plain default renders it. A document's `default` is a fact §8
grades, so the factory must be accompanied by `json_schema_extra={'default': …}` carrying the
document's own JSON — through the one channel `render` already merges `format` and `uniqueItems`
into, not a second one.

**THE VALUE IS CONSTRUCTED THROUGH A `TypeAdapter`, NOT BY CALLING THE CARRIER (decided
2026-11-02).** Calling it is undecidable where the decision has to be made: the renderer cannot
tell an imported enumeration from an imported `Annotated` alias. Measured at `render._field` over
all 1,054 documents, `brand.json`'s `default_language` and `markdown-asset.json`'s
`markdown_flavor` produce **byte-identical `TypeRef`s** — and `MarkdownFlavor` is a `StrEnum`
while `LanguageTag` is `Annotated[…]` and **not callable**. `ir.Module` carries no kind for an
imported symbol and **58 of the 120 defaulted sites name a symbol from another module**, so a rule
reading "call the carrier" emits `LanguageTag('en')` and the package fails at import. The kind
exists at lowering time and the reference lowering drops it at PROP.

So the field renders `default_factory=lambda: TypeAdapter(X | None).validate_python(<the
document's value>)`, which needs no kind, and the same spelling serves the scalar and both list
positions rather than a per-position discriminator that would be a bet.

**And two of the 120 sites must NOT be converted**, which no error count will tell anyone: the
`Annotated`-alias carriers at `brand/__init__.py` 1567 and 1590 produce no mypy error at all. The
population is **118 convert, 2 leave**, and the two are named in the gate by hand.

*The mutable-default argument for the factory is withdrawn as a reason, having been measured:*
pydantic deep-copies a plain mutable default per instance, so two instances already receive
distinct objects and mutating one does not reach the other. What the factory still buys is real
and smaller — no shared object behind `model_fields[…].default`, and no model instances
constructed at import time.

**A NARROWED `enum` INSIDE AN INHERITED VOCABULARY NAMES ITS MEMBERS (decided 2026-11-02).** This
is the `const` rule above generalised from one value to several, and it is the whole of the 158
`[assignment]` errors left after Pass B. Measured on `core/postal-country-system.json`: the base
declares `system: PostalCodeSystem`, 23 members; the `US` branch narrows it to
`['zip', 'zip_plus_four']` and we mint a **separate** `StrEnum` named
`PostalCountrySystemUSSystem`. Two unrelated enum classes, so the branch is an incompatible
override — exactly the defect the `const` case had, with a set in place of a single value. The
branch's members are a strict SUBSET of the base's, verified.

Python forbids the obvious repair, as it did before: an enum carrying members cannot be
subclassed. So the branch pins `Literal[PostalCodeSystem.ZIP, PostalCodeSystem.ZIP_PLUS_FOUR]` —
a literal over the base vocabulary's own members, which IS a subtype of that enum. The same
document already shows the one-member form working where Pass B reached it:
`Literal[PostalCodeSystem.PLZ]`.

It is also the better surface. A consumer reads the base vocabulary's members at the branch
instead of meeting a second two-member class that exists only because a branch narrowed.

### The widening each row takes

Every "→ refused" clause above becomes one of three answers, and **the largest group is neither
a refusal nor an approximation.** The rows sort as follows.

**(a) Rows whose answer is already decided here and was never implemented.** These cost no
approximation at all: the sentence that grades them exists, the compiler does not honour it, and
the directive's first effect is to make it. They are the dominant class.

- **A plain keyword beside a `oneOf` / `anyOf`.** §4's union section already decides it — "every
  keyword beside the combinator compiles onto the base, and every branch inherits it" — and §8
  already decides how the result is graded, against the branch node read under the root's
  siblings. The refusals reading "there is no pointer to the conjunction for it to name" predate
  that pairing rule and are answered by it. No widening; the keyword compiles.
- **`propertyNames` with an `enum`, and `enum` at KEY.** Both rows refuse "by name with the key
  set". A `Literal` of the members is the key type, and Pydantic renders `dict[Literal[…], V]`
  back as `propertyNames: {enum: […]}` — the document's own keyword, rendered and gradable.
  Faithful, not wide. Where the key node is named, the `StrEnum` is the key type and renders the
  same way.
- **`format` beside another string constraint.** The `format` row refuses a `uri` beside a
  string constraint because a URL type carries none. The row's own fallback already answers it:
  the type is the constrained `str` and the `format` rides as
  `json_schema_extra={"format": "uri"}`. Both facts are kept and neither half narrows; what is
  given up is the URL type's parsing, which is not an acceptance fact.
- **A local `$ref` cycle.** The `$ref` row says "a cycle refuses". A cycle is not an obstruction
  in Python: a forward reference under a string annotation plus `model_rebuild()` after the
  module's declarations represents it exactly, and §4 already calls `model_rebuild(force=True)`
  for union branches. The cell's answer becomes the forward reference. A *cross-document* cycle
  is a different thing and is not this row's: the record cannot be built for it, so it is §2's
  one irreducible refusal, and the difference between the two cycles is the record and not the
  type.
- **A root that is a bare `$ref`.** Refused because binding this module's symbol to another
  module's class would be a second way to reach one class, against §1. Where the target is a
  class the answer is a **subclass** of it, which is one class per name and accepts exactly what
  the base accepts, so §1 is untouched. Where the target is an alias, an enumeration or a root
  model there is nothing to subclass and the symbol is bound to the target **by identity**, which
  §1's own carve-out already admits inside a module and now admits across one: `X is Y` holds and
  the domain surface exports it once.
- **A scalar, enum, container or union target as a conjunct of an `allOf`.** The `$ref` row
  already decides it — "the target is this node's own TYPE, and the other conjuncts and the
  `allOf`'s siblings constrain it" — and the refusals reading "*X* is not a class, so it cannot
  be a base" are the unimplemented half of that sentence.
- **`uniqueItems` and `contains` where no class holds the value.** §2 already decides it: where
  no class encloses the value, the rule is an after-validator on the value's own annotated type. A root array
  is a root model, and a root model carries a rule tuple exactly as a class does, so `Distinct`
  and `AtLeastOne` reach it. The keyword is enforced, not dropped.
- **A root stating only `if` / `then`.** Refused because "a root is exactly one kind and this one
  states `if`". The conditional is a rule, and §2 declares a rule with no enclosing class on the
  value's own type: the root is a permissive root model carrying `ConditionalRequired`. The
  document states a conditional and nothing else, and so does the model.

**(b) Rows whose answer is a declared widening.** Each names its rung (§2's ladder) and its
attribution.

- **`patternProperties` beside a non-`false` `additionalProperties` (added 2026-10-27, and it was
  a VERDICT).** The `patternProperties` row refuses this case as "two value schemas". **It is
  not the document's obstruction, and that is measured:** `{"patternProperties": {"^x_":
  {"type": "string"}}, "additionalProperties": true}` under `Draft7Validator` accepts
  `{"x_a": "ok"}`, refuses `{"x_a": 1}`, and accepts `{"other": 123}`. Draft-07 is perfectly
  clear — keys matching the pattern take the pattern's schema and every other key is
  unconstrained. So §9's test fails on all three counts: the obstruction is not the document's,
  not the pointer space's, and not Pydantic's either, since a key-pattern check is expressible as
  a rule.

  Rung CONTAINER: the mapping is `dict[str, Any]`, the pattern's value typing is the fact
  dropped, and `strict_validate` still enforces it from the document. Attribution ours, and the
  one sentence is that a faithful answer is a rule family for "keys matching this pattern take
  this type", which no row has written.

  **This is why the verdict ceiling rose.** `onq`'s Group A let 15 documents get further and land
  on this already-decided verdict, which is a verdict they should never have reached. Moving the
  row off the verdict column takes all 15 with it — the largest single correction available to
  `refused` after the root-siblings group.

- ~~**`uniqueItems` and `contains` where even a named type cannot hold the rule.**~~ **WRONG, and
  withdrawn 2026-10-27: a named type holds the rule perfectly well, and §2 already said how.**
  This row claimed the duplicate and existential checks are the schema half's alone where no
  class encloses the array. §2 says the opposite and is right: "Where no class encloses the
  value — a root array, a mapping value, a `definitions` entry, a union branch — the rule is declared
  off the value's own annotated type as an after-validator (`AtLeastOne`, `NotValue`,
  `Distinct`)." `Annotated[list[X], AfterValidator(…)]` carries a rule; nothing about a named
  alias prevents it.

  The reason this went unnoticed is that **those three validators were never declared.** §2 names
  them and `src/adcp/types/_runtime.py` has no `AtLeastOne`, no `NotValue` and no `Distinct` —
  emitted 0 times each, against `UniqueItems` at 212 and `ForbiddenGroups` at 64. So the
  class-level path is well travelled and the value-level path had simply never been walked, and
  "we cannot express it" was standing in for "nobody wrote it". That is §9's first mistake
  wearing a different hat: not a verdict minted for unwritten code, but an APPROXIMATION declared
  for it, which is worse because an approximation looks accounted for.

  **The faithful answer:** declare the three in `_runtime.py` beside the other rule kinds, and
  declare each on the value's own annotated type where no class encloses it. Measured at the point this
  was withdrawn, **13 of 17 declared approximations were `uniqueItems`** at exactly these
  positions, so they become faithful and the *ours* backlog falls by 13 rather than being
  reported forever.

  `contains` keeps its own refusal of transcription — `AtLeastOne` takes the predicate §5's
  `contains` row already decides (`AtLeastOne(**{property: const})`, or `AtLeastOne(value)` for a
  bare `const` or one-member `enum`), and a richer predicate still widens rather than being
  transcribed. The distinction is between a rule having nowhere to LIVE, which was never true, and
  a predicate having no decided RENDERING, which is.
  **`contains` keeps its own refusal of transcription and drops only the document.** The row
  declines to transcribe a `contains` subschema into a validator, and that decision stands —
  what it may no longer do is refuse the document for it. Dropping the keyword widens the array
  (a list with no matching element is accepted by the model and refused by the schema half) and
  transcribes nothing, so the row gets both of the things it wanted.
- **A list-valued `items`.** Rung JOIN: `list[A | B | …]` over the positional schemas, dropping
  position and arity, with the element type collapsing to `Any` where `additionalItems` is
  absent or `true`. **The arity bound is not derived.** `additionalItems: false` implies
  `maxItems: len(items)`, and §3 forbids deriving a keyword the bundle does not state, so the
  bound stays with the schema half and the model does not restate it. Attribution ours.
  Unexercised: bundle 3.2 states no list-valued `items` and no `additionalItems`, so this row
  decides a case before it arrives rather than after.
- **An `allOf` restatement that neither matches nor narrows.** §2's intersection is the document's
  own accepted set, and the refusal exists where the intersection of two object or two array
  declarations is not computable. Rung KEYWORD: the field takes the base's declaration and the
  restatement's extra facts are dropped. That widens relative to the intersection and cannot
  narrow, because the base is one conjunct and the intersection is a subset of it. Attribution
  ours.
- **An empty intersection** — two disjoint type words, two disjoint enums. The node admits
  nothing, which is a contradiction in the document. Rung TOP, and this is the answer the `not`
  row already gives for `not: {}`: "admits nothing, which the typeless `Any` carries", with the
  schema half refusing every payload. Attribution upstream, because a conjunction admitting
  nothing is a defect in the conjunction. This row is about a node whose WHOLE accepted set is
  empty. One empty DISJUNCT of a union that still admits something is not that node: §5's `$ref`
  distribution clause drops the branch, the document's accepted set is unchanged, and no
  declaration is owed.
- **A keyword in none of §5, §6 or §7.** Rung TOP: the node is `Any`. Draft-07 ignores an
  unknown key, so the document may be narrower than `Any` but can never be wider, which makes
  `Any` the one safe rung when the keyword's reach is unknown. §2's by-name principle is intact
  — the key is not silently ignored, it costs a declared approximation at the top rung and a loud
  report line — and the node losing its whole type is exactly as visible as a refusal was.
  Attribution ours.
- **A union whose branches §4's dispatch cannot separate.** Declares a WIDENED fact where the
  combinator is `oneOf` and nothing where it is `anyOf`; §4 states it.
- ~~**A root stating no schema keyword.**~~ **Moved to (a) on 2026-10-26: it is faithful and
  carries no declaration.** This row sat here and its own sentence called the answer "faithful to
  a document that admits everything", which is group (a)'s definition and not this group's. A
  permissive root model over a document that constrains nothing DROPS nothing, so there is no
  fact to declare, and a declaration the draw cannot prove is deleted rather than carried.
  Measured on `core/asset-group-vocabulary.json`, which declares draft-07 and whose keys
  (`version`, `lastUpdated`, `vocabulary`) are not schema keywords: `Draft7Validator` accepts
  `42`, `"x"`, `null`, an object and an array, so the permissive model is exactly as wide as the
  document. The upstream issue stands — the schema should say more than it does — but **an
  upstream issue is not an approximation**, and filing one is the issue list's job, not a
  declaration's.

**(c) Rows that refuse nothing because there is no fact to approximate.** `errorMessage` and the
registry data keys constrain no instance, so no annotation drops anything for them. They move to
§6 — admitted by name, compiling to nothing, reported — and §7 says what becomes of its own set.

### A union of presence-only branches that also forbid (decided 2026-10-27)

The `oneOf`/`anyOf` row's presence clause reads "every branch `required`-only", and 11 documents
hold a union whose branches constrain presence only and are NOT `required`-only. Row `.20`
measured them as two cases and this section answered neither. They go to different places, and
the generated cell is written by the row that implements each.

**Group A — every branch is `required` plus a `not` of required groups. This is FAITHFUL, and
it needs one new rule kind.** Six documents: `core/audience-characteristic.json`,
`core/catchment.json`, `core/creative-asset.json`, `core/creative-manifest.json`,
`core/frequency-cap-impression-constraints.json`, `core/frequency-cap-interval-constraints.json`.

Every branch constrains which keys are present and nothing else, so it is a rule on the root's
class and not a branch class. **The answer is ONE rule whose clauses are the branches, each
clause carrying its own required group AND its own forbidden group, with the combinator deciding
how many clauses an instance may satisfy.**

Widening `_required_only` to admit `not` is the obvious move and it is WRONG, measured: the `not`
is per BRANCH, so branch *i* reads "every name in R*ᵢ* present and no group of F*ᵢ* present". A
`RequiredGroups` over the R*ᵢ* beside a root-level `ForbiddenGroups` over the F*ᵢ* forbids every
F*ᵢ* unconditionally — `core/catchment.json` states three methods and forbids the other two per
method, so a root-level rule forbids all three and refuses a payload the document admits. The two
halves must stay paired per clause, and neither `RequiredGroups` (groups and a combinator) nor
`ForbiddenGroups` (groups alone) has a slot for the other half. So `_runtime.py` declares the
new kind and `lower/rules.py` writes it. Nothing is dropped: `APPROXIMATED` does not move.

**Group B — the union MIXES case branches with presence-only ones. This is a WIDENING, and it
belongs to §14 step 10.** Five documents, among them
`error-details/vast-version-mismatch.json` `/anyOf/2`, `media-buy/buy-products-request.json`
`/anyOf/0` and `media-buy/create-media-buy-request.json` `/anyOf/2`.

A presence-only branch admits ANY object carrying those keys, which is wider than any of the
case branches' classes. So no type over the case classes covers the instances the presence
branch admits, and there is no faithful type for the union: the case branches give classes, the
presence branch gives a rule, and an instance satisfying only the rule is none of the classes.
That is the asymmetry Group A does not have, and it is why the two cases separate. The fact
dropped is the case precision of the branches, the type widens by §2's ladder, and the gap is
declared and attributed.

### The dispatch mixin is named where no base already carries it (decided 2026-10-29)

`BranchDispatchMixin` has to come FIRST so the MRO finds its `__get_pydantic_core_schema__`,
and a union base that composes already carries it — so naming it beside such a base puts a
class before its own subclass and Python refuses to build the module.

**The suppression is a function of the BASE LIST and not of the route that reached it.** That is
the whole decision, and it is the one reading both routes can ask: at the point the base list is
built, the mixin is named where no base in it already carries the mixin, and omitted where one
does. `base_if_none_composes` is the same case at the same seam — "what the base would be if
nothing composed" — and this is "what the mixin is if nothing already carries it".

A guard keyed to the route is the alternative and it is wrong. `Enclosing` is constructed at one
place, inside the enclosing union's branch loop, under the arm that claims a branch the parser
classified `nodes.Union`. A nested union reaching `lower_union` through the DISPATCH instead —
because it declares `properties` beside its own combinator, so the enclosing loop's arm does not
claim it — arrives with no carrier, and a second guard there would be a second copy of the
reading `Enclosing` was built to hold once (§11). Measured on `core/postal-area.json#/anyOf/0`,
which is a fifth case beside the four that arm's own comment counts, and the only inconsistent
MRO in the 1,006-module tree.

`Enclosing` keeps its other job. It carries the enclosing base and that base's `Case` so a
property both declare takes §2's restatement rule, which no base list states and which the
dispatch route genuinely does not have.

### An `enum` conjunct beside a `$ref` to an enum (decided 2026-10-29)

§2 decides the semantics already — "an enum is the intersection of the members" — and what was
unwritten is the RENDERING. `keywords.cell("enum", CONJ)` carries effect `TYPE` with an empty
`compiles` string: the cell says the keyword lowers and no handler claims it, which is the
defect this epic has now found seven times.

**The intersection renders as a `Literal` over the TARGET's members, not over their raw values.**
`Literal[CreativeApprovalStatus.PENDING_REVIEW, …]` and `Literal['pending_review', …]` dump
identically — `{"enum": [the three], "type": "string"}` — so §8 compares the same fact either
way, and the member form keeps the imported symbol a caller can name. Where §8 cannot tell two
renderings apart, DX decides, and a caller reaching the enum class is worth more than a bare
string.

Population one: `core/creative-approval-scope.json` at `/properties/approval_status/allOf/1`.
Measured over every `allOf` in the bundle whose conjuncts are a bare `$ref` plus an inline
conjunct stating none of `type`, `properties`, `required`, `additionalProperties` or `allOf` —
186 sites, of which `if`/`then` is 142, `not` 34, `anyOf` 3, `oneOf` 3, `else`/`if`/`then` 2,
`errorMessage` with `not` 1, and `enum` **1**. Every one but the `enum` is a rule or a
combinator and is already routed.

The cell is where this belongs, and the grid row is its rendering.

### Two ARRAY declarations under one `allOf` (decided 2026-10-29)

§5's `properties` row at CONJ states the `allOf` spelling for two OBJECT declarations and says
nothing for two arrays, which is what the `$ref` row's own "the other conjuncts **and the
`allOf`'s siblings** constrain it" runs into at an array target.

**Two array declarations intersect, member by member, as two object declarations do.** `items`
intersects as a declaration and is handed back to the parser as one node, which is §2's rule
unchanged. The bounds take the tighter end — the greater `minItems`, the lesser `maxItems` — and
a `minItems` above a `maxItems` is an empty intersection and refuses. `uniqueItems` holds where
either conjunct states it, because a conjunction of constraints is satisfied only by an instance
satisfying both. Every `contains` is kept: two `contains` predicates are two independent
`AtLeastOne` rules over the same value, never merged into one, because `contains: A` and
`contains: B` demand a member satisfying each and a single merged predicate would demand one
member satisfying both.

That last clause is the only place the array case is not symmetric with the object case, and the
reason is that `properties` is keyed and `contains` is not: two declarations of one KEY are one
field, while two `contains` are two facts about the list.

### A presence clause whose required half is a disjunction of groups (decided 2026-10-29)

Group A's clause carries "its OWN required group" — one group, read as a conjunction of names.
Four documents spell that half as a DISJUNCTION: `formats/canonical/image.json`,
`formats/canonical/html5.json` and `formats/canonical/display_tag.json` at `/allOf/1`, and
`governance/check-governance-request.json` at `/allOf/1`. One branch of each states an `anyOf`
of `required` groups where the others state `required` directly.

**A clause's required half is a disjunction of GROUPS, which is what its forbidden half already
is.** `Presence.forbid` holds groups because `not: {"required": [a, b]}` forbids the PAIR and
says nothing about either name alone. The same reading of the required half makes
`required: [a, b]` the single group `((a, b),)` and an `anyOf` over `required` the groups it
states. A clause holds when at least one of its groups is present in full, and a clause stating
no group states no requirement and holds. One field means one thing — the groups this branch's
requiredness admits — where a second field beside it would make one clause carry two readings of
one keyword.

Both halves derive from `schema.required_groups`, which already reads `required` and a
combinator over `required` into groups. That is §11's one reading with two readers: the `not`
half and the required half reach the same derivation from the two sides of one branch.

Dropping the disjunct is not available, measured on `image.json`, whose four size modes are
`{}`, `{min_width}`, `{width, height}` and `{sizes}`. With the disjunct dropped the rule rejects
`{}`, which the document admits as the "none" mode, so the model is TIGHTER than its document.
§2 admits a widening and never a narrowing.

`RequiredGroups` reads the same document fact as a RULE and stays separate, for the reason
`Presence` states itself: a clause has no `errors` because a branch is not violated on its own,
and only the combinator above it decides how many branches an instance may satisfy.

**A conjunction of a group with a disjunction of groups DISTRIBUTES into a disjunction of
groups**, which is the same principle the `$ref` row's distribution clause states one row above:
conjunction distributes over disjunction. `required_groups` reads an `allOf` of single-group
conjuncts as one group, the union of their names; an `allOf` whose conjuncts each give a LIST of
groups is the product of those lists with the names unioned per combination, and the single-group
case is that product over one-element lists. So
`allOf: [{"required": [g]}, {"anyOf": [{"required": [a]}, {"required": [b]}]}]` is the two groups
`((g, a), (g, b))`, which is what the document says and what `governance/check-governance-request.json`
states at `/allOf/1`.

The product arm never takes `partial`, for the reason the `allOf` arm already does not: dropping an
unreadable conjunct from a product leaves FEWER names in each group, which under a `not` forbids
MORE, and a rule stronger than its document is the narrowing §2 refuses.

---

## 6. Keywords we admit and do not compile

None of these can constrain an instance, so none compiles to a type, a rule or a base. Each is
admitted **by name**. Several carry something anyway, and the table says what.

**`errorMessage` and the registry data keys join this section on 2026-10-26**, from §7. Neither
constrains an instance — `errorMessage` customises an `ajv-errors` message and the registry keys
are a registry's own instance data — so no annotation drops a fact for them and there is nothing
to widen. They are admitted by name and compile to nothing. **Whether the reader is TOLD is a separate
column of the cell, and the two rows answer it differently** (decided 2026-10-30): a dropped
`errorMessage` is reported, the registry data keys are not, and neither is `$comment`. Three
cells settle it by agreeing in every other field and differing here — a comment is manifestly a
note and a registry's own data is manifestly data, so a reader who is not told has lost nothing,
while `errorMessage` sits BESIDE a constraint and a reader who is not told has no way to see that
the class carries nothing for it. `errorMessage` is the only reported cell in the table. §7 says
what refusing these two was buying and where it now shows up.

<!-- generated from codegen/keywords.py -->
| keyword | what it does, or why nothing |
| --- | --- |
| `$schema` | Nothing on the class, but it selects the **validator** the schema half runs, and through it the format checkers a type may be selected for. The one annotation that decides a behaviour, and it decides it on the schema half. |
| `title` | Nested → nothing: a nested node is named by its property or entry key. Its presence selects `StrEnum` over `Literal` for an enum node. Never rendered. ROOT → the symbol. BRANCH → the branch class's name. |
| `description` | A `$ref` sibling's description wins over the target's; a composed base's loses to the document's own. ROOT class → the docstring; ROOT alias → `Field(description=…)`; ROOT enum → the enum's docstring. PROP → `Field(description=…)`. ELEM / MAPV → the named alias carries it. BRANCH that is a class → its docstring; a non-object branch of a nested union → its own annotated type. CONJ / RULE → nothing. |
| `examples` | Nothing on the model. The accepts check replays every one, at every position: a ROOT example constructs the class, and an example at a nested node is validated against that node's own annotated type. A payload the document refuses is a spec defect, reported by document and pointer; one the document accepts and the class refuses is ours. |
| `$comment` | Nothing. A note to a reader. |
| `readOnly`, `writeOnly` | Nothing. Pydantic can render them, but the SDK has one model per document and no read/write split for them to state. |
| `deprecated` | A `false` → nothing. Rendered, so graded. ROOT / BRANCH → the class's `json_schema_extra`. PROP → `Field(deprecated=True)`. |
| `enumDescriptions`, `x-enum-descriptions` | Member docstrings on the enumeration, keyed by the member's value. Two spellings of one keyword; both are read. |
| `enumMetadata` | Nothing: recovery and action metadata for a reader. The `enum` beside it has already closed the value set. |
| `notes` | Nothing: English sentences for a reader. |
| `discriminator` | Nothing on the class. It names a branch where that branch pins more than one `const`, and separately it **confirms** a dispatch key the branches already state — it does not establish one. A union whose branches pin a distinct const dispatches on that property whether or not the keyword is present, and a declared keyword the branches do not confirm is not a dispatch source. |
| the `x-` namespace | Nothing, and **still listed by name** — see below. |
| `errorMessage` | Nothing. An `ajv-errors` extension customising a validator's message, so it constrains no instance and an annotation that omits it omits no fact. It has no Pydantic rendering and never needed one. **The drop is reported**, at every position the document states it at. |
| `version`, `lastUpdated`, `vocabulary`, and the registry payload keys | Nothing. A registry's own instance data sitting at a schema root: `_generated`, `_generatedAt`, `adcp_version`, `architecture`, `asset_types`, `baseUrl`, `extensions`, `governance`, `last_updated`, `mappings`, `prerelease`, `protocol_layers`, `published_version`, `stability`, `usage_notes`, `versioning`. None of them constrains an instance, and draft-07 says the same thing by ignoring an unknown key, so an annotation that omits one omits no fact and admitting it by name says only what is true of instance data. A root stating only these keys is the empty schema and emits as a permissive root model; a document stating them BESIDE a real schema emits normally, with the data keys compiling to nothing. |
<!-- end generated -->

### The `x-` namespace is admitted by prefix AND listed by name

A vendor extension cannot be a schema keyword, so the `x-` prefix is sufficient to admit one.
That is the one place the by-name principle has an exception — and the exception is leaky, which
is why the names are kept as well: `x-enum-descriptions` carries member docstrings, and the
prefix rule dropped it silently because nothing was looking at the list.

So a key matching the prefix is admitted, and every key the bundle carries is also listed. A key
in the namespace but not on the list is admitted and **reported**, so it gets read once rather
than assumed to be metadata.

Carrying only organisational metadata: `x-accessibility`, `x-added-in`,
`x-adcp-file-size-units`, `x-adcp-hoist`, `x-adcp-model-context-inline`, `x-adcp-schema-uri`,
`x-adcp-sdk-local`, `x-canonical-policy-required-params-not-enforced`,
`x-compatibility-projection-only`, `x-deprecated-enum-values`, `x-deprecated-enum-values-doc`,
`x-deprecated-in`, `x-entity`, `x-entity-definitions`, `x-governed-commitment`,
`x-idempotency-key-required`, `x-legacy-fallback`, `x-mutates-state`, `x-operation-family`,
`x-removed-in`, `x-status`, `x-superseded-by`, `x-task-result-schema-overrides`,
`x-tool-summary`.

Four need a reason beyond that:

- `x-adcp-validation` constrains in intent and not in the document, so a model enforcing it would
  be narrower than its document (upstream: `adcontextprotocol/adcp#8472`).
- `x-extensible` and `x-pattern` describe an open vocabulary in a namespace the validator ignores,
  so the document's accepted set is the closed `enum` beside them and a closed `StrEnum` is
  faithful to it.
- `x-canonicalization` reads `"set"` beside the document's own `uniqueItems` and `minItems`, so
  the duplicate half is already the document's own keyword and the order half is not an
  acceptance statement.
- `x-adcp-open-payload` sits beside `additionalProperties: true`, or on a typeless node, so
  `allow` and `Any` already carry it.

---

## 7. Keywords we refuse — the set is empty

**Emptied on 2026-10-26 by the owner's directive (§2).** No keyword's presence refuses a
document. The section stays, with its membership still a projection of the declaration, because
a reader looking for "which keywords refuse" has to find the answer, and because the one
refusal left in the compiler is not a keyword's at all.

Both rows have moved to §6, each refused for a reason that was never about the document's
accepted set. **`errorMessage`'s cell was the last `REFUSE` in the table, and moving it is what
let `Effect.REFUSE` retire (2026-10-30).** The effect no longer exists, so "refuse a document on
a keyword" is a name error rather than a path the compiler can take — which is the whole of what
that step was buying.

- **`errorMessage`** has no Pydantic rendering, and never needed one: it customises a validator's
  message and constrains no instance, so an annotation that omits it omits no fact. The drop is
  reported, as it was.
- **The registry data keys** — `version`, `lastUpdated`, `vocabulary`, `_generated`,
  `_generatedAt`, `adcp_version`, `architecture`, `asset_types`, `baseUrl`, `extensions`,
  `governance`, `last_updated`, `mappings`, `prerelease`, `protocol_layers`, `published_version`,
  `stability`, `usage_notes`, `versioning` — are a registry's own instance data at a schema root.
  The old row's reasoning was that "admitting them by name would be admitting data as vocabulary"
  and that "the documents carrying them are registries rather than schemas, and refusing them is
  how that shows up". The first half was answering a question nobody asked: admitting a key by
  name says it carries no acceptance meaning, which for instance data is simply true, and
  draft-07 says the same thing by ignoring it. The second half was real — the refusal was a
  SIGNAL about the document, not a statement about its accepted set — and a refusal is the wrong
  instrument for a signal, because it costs the document its type to carry it. The signal moves
  to the approximation record: a root stating only these keys is a permissive root model (§4)
  with an upstream attribution asking the registry either to drop its `$schema` or to declare a
  schema. A document that states these keys *beside* a real schema — a `type` and `properties`
  at its root — emits normally, with the data keys compiling to nothing.

**The one refusal the compiler can still mint is not a keyword's.** Where the document of record
(§3) is undefined, there is no schema for `strict_validate` to validate against and no document
for §8 to grade against, so §2's partial-model objection applies with nothing to answer it. The
principle is that **the document has no defined accepted set**, and three cases reach it:

- a `$ref` whose target is not a bundle document;
- a cross-document reference cycle, which the inliner cannot resolve. A LOCAL cycle is not one
  of these — it is never inlined and renders as a forward reference (§5);
- a document that fails its own declared draft's meta-schema, so it is not a schema at all and
  has no accepted set to be faithful to.

Measured over bundle 3.2's 1,054 portable documents, **all three are empty**: 0 undefined
records, 0 meta-schema failures. That is why "zero refusals" is reachable for this bundle rather
than aspirational, and it is the figure to re-measure on every bundle version. The refusal stays
in the compiler regardless, because a bundle that grows one must report it rather than crash on
it (§9).

<!-- generated from codegen/keywords.py -->
| keyword | why |
| --- | --- |
<!-- end generated -->

The grid above is generated and is **EMPTY**, because no cell can say `REFUSE` any more. The
section's title is therefore a fact the artifact holds rather than a claim its prose makes, which
is the only form in which this document is worth reading.

**The drop is reported at every position the keyword occupies, and not only where a conjunct
encloses it.** `media-buy/sync-catalogs-request.json` is the one portable document carrying
`errorMessage`, and it carries it twice — at `/allOf/1` and at `/then`. The reader used to be
told about the first and not the second, because the channel that built the note screened `CONJ`
while the cell refused at every position, and `/then` is a RULE source the rule lowering reads
raw, so no screen ever saw it. A keyword's effect is a decision about the keyword at a position;
a report that reaches one position and not another is a defect in the channel, not a second
decision. **So the channel is a function of the DOCUMENT** — `bundle.reported_drops` over the one
descent walk, which carries the position the column assigned and cannot privilege one — and the
reading that settles it is the number of reported drops naming the keyword: **two as of
2026-10-30, where it was one**, inside a report that went from 73 notes over 15 documents to 74
over the same 15.

A keyword in none of §5, §6 or §7 is one the bundle does not use. The first document to carry one
**widens its node to `Any`** — §5's rung TOP — and declares the approximation, so a new keyword
is loud rather than ignored. `Any` and not a narrower rung, because an unrowed keyword's reach is
unknown: draft-07 ignores it, so the document may be narrower than `Any` and can never be wider,
and `Any` is the one rung that is safe without knowing what the keyword does. A node that loses
its whole type is as visible in the report and in the emitted module as a refused document was,
which is what the old sentence was buying.

---

## 8. How we know the output is right

**TWO checks and one declared set**, run once per emitted class against the schema document it
names. Both checks are payload checks: a value is drawn, and the class and the document are asked
about the same value. Nothing here reads one schema against another, and nothing here grades a
rendering. **Anything that is not one of these two checks or the widening set they prove does not
belong in this section** — that rule is what the 2026-10-30 deletion below enforces.

- **Accepts.** Draw payloads the document accepts and construct the class from each. A refusal
  here means the model is tighter than its document, which is the defect that matters.

  **An approximation is a claim about this check, and this check is what proves it.** §2 says
  every approximation of acceptance is a widening. A widening is therefore not a thing a
  declaration asserts and a reader believes: for every fact an approximation drops, the draw
  takes the values that keyword distinguishes — the same coverage classes below — and the class
  must accept every one of them. An approximation that still refuses a value the document admits
  is a NARROWING wearing a declaration, and it fails here, by value and by pointer. This is
  what keeps "approximated" from being an allowlist.

  **The draw COVERS the node's admissible space by constraint class; it does not sample it.**
  "Never tighter" is a claim about every value the document admits, and a sampling draw reports
  only the values it drew — so it can run green forever against a type that refuses a whole class
  of admissible value. For each keyword the node states, the draw takes the classes that keyword
  distinguishes: every member of an `enum`, both sides of each bound and the bound itself, and for
  a `format` every case the format's own checker admits rather than the case a generator finds
  most likely. A Python type chosen for a node admits everything the node admits, or the choice is
  a narrowing and this check names it with the value.

  **Every position a widening can land at has an instance location (settled 2026-10-27).** The
  draw places a value at the instance location the node's pointer names, and a position with no
  location makes a widening UNPROVABLE — which that check counts as a failure, correctly, since
  an unproved widening is a claim with no instrument on it. Two positions had none, and §5(b)'s
  `uniqueItems` row lands at both, so 4 of its 5 declarations were unprovable:

  - **A mapping value** — `#/properties/x/additionalProperties`, and the same for
    `patternProperties`. The location is `x` then any key the mapping admits; a key is a free
    choice and the draw makes one, so the location exists and simply was not read.
  - **A `definitions` entry** — `#/definitions/x`. This one has no location of its own and never
    will: an entry is reachable only through a `$ref` that names it, and §5 declares no entry
    nothing references. **It needs no new reading, because the rule that a declaration travels
    with the fact already re-points it to the referring pointer**, which is a `properties`
    segment the draw already places. The two settlements compose: one gives the declaration a
    pointer the declaration names, and that same pointer is one the draw can reach.
- **Dump.** Serialize the instance and validate the dump against the document. A failure means we
  emit something our own schema refuses.
**THERE IS NO THIRD CHECK (decided 2026-10-30).** A comparison of the class's
`model_json_schema()` against the document stood here and is **deleted** — code, tests, pins,
prose, as if it had never existed. It was not a check on the artifact; it diffed schema TEXT, and
it existed as a proxy for coverage the draw had stopped providing. The draw runs at ONE example
per pair against `check_accepts`'s own default of 25, while this section demands the draw COVER
the admissible space rather than sample it — so the method was throttled and a second instrument
was built beside it to compensate. It produced 1,086 "facts" over 155 pairs that no payload had
ever demonstrated, and they were reported as the SDK's correctness for weeks.

**A fact no payload can demonstrate is not a fact about the artifact.** A consumer meets these
classes through validation and construction, so a disagreement a drawn value cannot expose is a
disagreement in rendering, and §2's "nothing rewrites emitted output" already says rendering is
not ours to grade. Where the draw provably cannot reach a keyword, the honest answer is to NAME
that residue and raise the example count until the pile stops shrinking — not to diff text and
count the difference as a defect.

**THE WIDENING SET, which is the one thing beside the two checks.** §2 makes every keyword the
model cannot express a WIDENING rather than a refusal, so the artifact is deliberately looser than
its document in a declared, enumerated set of places. That set needs proving, and the proof is
the draw and nothing else: for every fact an approximation drops, the draw takes the values that
keyword distinguishes and **the class must accept every one of them.** An approximation that
still refuses a value the document admits is a NARROWING wearing a declaration, and it fails
here, by value and by pointer. That is what keeps the declared set from being an allowlist, and
it is why the widening set belongs to the round trip rather than beside it.

**An approximation nothing can demonstrate does not belong in the set.** With the text diff gone,
a declaration earns its place by a value: either a payload exists that the document admits and
the class now admits, or the declaration is describing a difference no consumer can reach and it
is deleted rather than counted. This retires the UNDERDETERMINED kind and the disjointness
equality that graded it — nothing widens at an UNDERDETERMINED site, the annotation admits exactly
what the document admits, and the only loss is which branch an overlapping payload becomes, which
no draw and no dump can observe. §4's inseparable `oneOf` is unaffected: it is a WIDENED fact,
because the model admits a payload the document refuses, and the draw shows it.

**AND THE TWO DERIVED EQUALITIES THAT GRADED IT GO WITH IT (2026-10-30).** A generic keyword set
derived from the declaration, the equality between it and what the declaration renders, the
equality between the declared set and the approximated set, and the pointer-translation rule that
made the second comparable — all of that existed to keep the text diff honest. With the diff gone
there is nothing for them to be honest about. What replaces them is the draw: a declaration is
proved by a value the document admits and the class accepts, at the pointer the declaration
names, and a declaration no value can prove is deleted rather than graded.

**The VERDICT count is not pinned either, and a ceiling on it was the wrong instrument
(2026-10-27).** It is not monotone under progress, measured in both directions within one day:
clearing `union.ROOT_CONJUNCTS` moved it DOWN 85, because 46 documents' real obstruction turned
out to be unwritten code; clearing `onq`'s Group A moved it UP 16, because 15 documents got
further and landed on a verdict already decided elsewhere. Both moves are documents progressing,
and a ceiling that forbids the second while rewarding the first is §9's pin with no denominator —
it would oblige a row that unblocks a document to loosen it. What is pinned instead is the SET,
named by document, so a verdict arriving is attributable and a verdict arriving for a NEW reason
reddens. The figure to drive to zero is `refused`, and the verdict column is a reading of it.

**What else is pinned, and what is only reported.** §9's rule that a pin with no denominator is
not a ratchet decides this. A round-trip failure in either direction is pinned at zero:
none of them moves with emission, because each is a disagreement between a model and its document
and a correct emitter produces none however many documents it emits. The approximation count is
**not pinned** — it rises when a document starts emitting, which would oblige every later change
to loosen the pin, the opposite of a ratchet — and is instead reported with its denominator (the
the declared set) and split by attribution, with the *ours* half ratcheting down as §5's cells
land.

*The worked example, which is why the split is necessary rather than tidy.* One keyword's gap —
`deprecated`, rendered by its §6 row and not yet written through — moves *missing* from 0 to 57
facts. Under the directive, without the split, every keyword's gap does that at once and the pin
is abandoned on the first wave. With the split, those 57 are *approximated* against one cell-level
attribution, *missing* stays 0, and the figure that moves is the one that is supposed to move.
A grader whose pin survives the directive is the test of this section, and this is how it
survives it.

Pydantic is deliberately less strict than JSON Schema, so a payload the *document* refuses tells
us nothing about the generated class on either route. There is therefore no "refuses" check on
the model; the equivalent check confirms the schema half is wired to the class at all.

Every class, root model and alias the tree carries is paired with the schema node it names, and
all three checks run over that pairing. **The population every check ranges over is every
portable document of the bundle**, and under §2 every one of them emits, so there is no second
set to reason about: a document that does not appear in the pairing is a defect in the run,
where it used to be a refusal with a reason.

A branch class of a union is paired with its branch node read
under the union's siblings: draft-07 applies every keyword beside the combinator to the same
instance the branch describes, so a field the branch inherits from the base is a fact its node
states and not one it added. A pair the payload generator cannot draw for still has to pass the
draw, and names the case that blocked it.

**At a union in ANY position, not only a root one.** The reason above is draft-07's evaluation
rule, which does not care where the union sits.

So a sibling beside a union lowers by COMPOSITION and nothing is approximated: the siblings
become a base class, each branch becomes a subclass narrowing what it narrows, and the union is
over the subclasses. Where a branch also restates a property the siblings declare, the
restatement composes by the conjunct rule below — composition and intersection are the same
operation reached from two directions.

**The dual of that rule, for a node whose `type` is a LIST (added 2026-10-26).** A class cut
out of a type list is paired with its node read at **its own type word**, not at the whole list.
The union-branch rule above adds the root's siblings because the branch describes the same
instance the root does; this one subtracts the list's other words for the mirror reason — the
class describes one member of the union and the other members are carried by the field holding
it, not by this class.

Without it the same fact is counted twice and reported as a defect once. `core/delivery-metrics.json`
is the measured case: `/properties/quartile_data` states `type: ["object", "null"]`, the field
renders `QuartileData | None`, and the ROOT pair passes because `_normalize`
folds the model's `anyOf: [{$ref}, {"type": "null"}]` back into the document's own list. The
nested class is then paired with the same node and reports `differs /type` — `object` against
`["object", "null"]` — for a fact the parent already carries.
The model is faithful at both pointers; only the pairing was wrong.

**A `properties` entry whose subschema is the EMPTY SCHEMA is not a fact these checks grade
(decided 2026-10-29).** §5's `additionalProperties` row already fixes the reading — "the empty
schema `{}` IS `true` and is read as `true` everywhere below" — and a `properties` entry stating
`{}` therefore constrains nothing. A document with no entry for a key and a model carrying
`properties: {key: {}}` admit exactly the same instances, so the entry is vacuous and reporting it
`added` counts a non-fact as a defect. One reading of the empty schema, two readers.

This is what `required` naming a property no declaration declares was caught between, and it is
**27 of the 95 refusals, 5 of them primary**. §5's `required` row called such a name "a presence
rule with no field", a rule renders no `required` in a model's JSON schema, and the keyword's own
cell is `rendered=True` — so the rule half reported `differs /required` and the field half
reported an `added` `properties` entry, and the handler refused rather than emit a pair it knew
was red. Two of this compiler's own decisions disagreeing, with no document at fault.

**The field half is the right one and it is EXACT.** `required: ["x"]` with no declaration for `x`
admits an object carrying `x` with any value, which is precisely a required field of type `Any` —
`Any` being what §5's `type` row already gives an absent type word. Nothing is widened, nothing is
dropped, and no declaration is owed.

So a `null` member of a type list is the FIELD's fact, graded where the field is, and a member
class is graded against the case it actually describes. Row `.20` found this by emitting new
documents into the three checks, reported it, and declined to invent the rule — which is why it
is here and not in a handler.

**The third pairing rule, for a node at a CONJUNCT of an `allOf`.** A class, root model or
alias cut out at `…/allOf/N` is paired with its node read **as the composition** — the
intersection of every conjunct of that `allOf`, taken with the keywords stated beside the
`allOf`. Not with the conjunct's own text.

Draft-07's `allOf` holds every conjunct against the same instance, so a fact a sibling conjunct
states is a fact this node's instance must satisfy, not one this class added. Pairing against the
conjunct's own text instead reads every such fact as one this class ADDED, i.e. as a model
NARROWER than its document — so a reader pairing that way reports the faithful model as the defect.
A fact a sibling conjunct states is therefore never declarable.

This rule is what makes §5's `properties` row at CONJ gradable.

**A declaration is counted at the `SchemaRef` spelling of its pointer, and at no other (decided
2026-10-30).** A node reached through an `allOf` conjunct has two spellings — the one the document
writes and the one §2's intersection produces, `{**child, "allOf": [base]}`, which puts an index
below every pointer the document has no `allOf` at. `render.declared_at` tests a prefix on ONE
spelling, `compiler.schema_ref`'s, and `compiler.schema_ref` is its sole producer; a declaration
written at the other spelling therefore attaches to the wrong class or to none.

**This is one rule and it settles three separate readings**, which is why it is stated here rather
than per site. Measured on `adagents.json`: `#/oneOf/1/anyOf` is declared and separable while
`#/oneOf/1/allOf/0/anyOf` is inseparable and declared by nothing — one union, two spellings,
counted twice, and the same pair appears five times over. So the over-count in the declared
backlog and the approximation instances no strict walk can resolve are not two defects. They are
one spelling question asked twice.

The reading that follows: §2 asks a declaration to be a fact §8 can look for in the document and
find. A pointer that resolves to nothing is not that, whatever it is counted against.

**An ANNOTATION is not a fact these three checks grade, at any pointer.** The predicate is
`bundle.is_an_annotation(keyword, position)` — §1's own, the one `record` already reads to settle
a `$ref`'s sibling. An annotation is a key whose cell compiles to no type, no field and no rule,
which is what "states nothing about acceptance" IS; so `added`, `missing` or `differs` on one
reports a difference that cannot change what a payload is accepted as, and these checks grade
acceptance.

Annotation COVERAGE is its own obligation, graded with §5's ergonomic rows and not among these
three: every description the document states reaches some emitted class. A check that mixes
acceptance with ergonomics reports a defect in one as a defect in the other.

A check is exhaustive over the set of nodes it claims, or it does not exist. A check that
enumerates a subset reports on that subset only, and says so.

---

## 9. Mistakes to avoid

Each is one sentence and its reason.

- **Code nobody has written is an APPROXIMATION, never a refusal.** *This replaces "a refusal for
  code nobody has written is a DEFERRAL, never a verdict" on 2026-10-26.* The old rule separated
  two kinds of refusal because minting the permanent kind for unwritten code reports clearable
  work as finished. §2 now says unwritten code costs a declared widening and never a document, so
  the DEFERRAL has nothing left to be the kind of: the two kinds collapse to one, and the one
  that survives is the record's own (§7). The rule is the same rule one level stronger — do not
  charge a document for work we have not done — and the thing that must not be lost is what the
  deferral was carrying: *clearable* work stays visible, as the *ours* half of the approximation
  count, which ratchets down.
- **An approximation that narrows is not an approximation.** It is a model tighter than its
  document wearing a declaration, and §8's accepts draw is pointed at exactly that. Widen by
  another rung — to `Any` if nothing else carries it — rather than declaring the narrowing.
- **A declared approximation the model does not make is a stale excuse.** The draw cannot prove
  it — no value the document admits is newly accepted at that pointer — so it is deleted, because
  a declaration that outlives its widening hides the next real gap at the same pointer.
- **Do not pin the approximation count.** It rises whenever the emitted set grows, which is the
  next rule in this list. Pin the round-trip failures, which do not, and ratchet the *ours* split
  down.
- **Do not hand-write the set a generic check ranges over.** Derive it from the declaration the
  tables are read against (§8). A hand-written set is complete with respect to itself, so what it
  omits passes in both directions and nothing says so.
- **A keyword handled in code but named in none of §5, §6 or §7 is an invented rule.** Those
  tables are exhaustive by intent, and a rendering no section decided departs from the design as
  far as a decision nothing implements.
- **An exemption names an upstream issue, or it is this SDK's own decision and belongs in this
  document.** Attributing our own cost to upstream means waiting forever for someone else to fix
  it.
- **A pin with no denominator is not a ratchet.** A count that rises whenever the emitted set
  grows obliges every later change to loosen it, which is the opposite of what a
  ratchet is for. Pin what does not move with emission and derive the rest.
- **Never approximate on a keyword the walk itself inserted.** An approximation must name
  something the document states, or the document is blamed for the compiler's own rewriting —
  and the declaration then cannot be checked, because §8 looks for the fact in the document and
  does not find it.
- **A crash is not an outcome.** Every node reaches a lowering, and the document reaches emission
  or the one refusal §7 names. An unhandled type error names nothing and stops the run. Under §2
  the walk is total, so this rule loses the type checker that used to enforce it — a handler had
  to answer the refusal branch — and what replaces it is that `approximate` is the one function a
  handler calls when it cannot render, reached by its own final arm. A handler that raises
  instead is the defect this rule is now about.
- **Do not decide one document's output by a census over the run.** A name, a case or an
  import that depends on which other documents the run includes makes a one-document emission
  and a whole-bundle emission disagree about the same document; §2 names every constrained
  scalar from its constraint alone for this reason.

  **THE RUN IS NOT THE BUNDLE, and that distinction is what §1's domain-scope collision rule
  rests on (2026-10-30).** This prohibition is about the run's DOCUMENT SET — the argument list,
  which varies between `./check --why one-document.json` and a whole-population emission. The
  BUNDLE is neither: it is pinned, declared, and an input to every run alike, so a name derived
  from a bundle-wide reading is the SAME name in both, which is exactly the property this rule
  protects. So a census over the RUN is forbidden and a reading of the BUNDLE is not, and the
  rule is kept rather than amended.

  What that costs is stated plainly: resolving a collision at domain scope needs the domain's
  other exported names, so naming can no longer be a function of one document and its reference
  closure. It becomes a function of the bundle, and the one-document path has to read the domain's
  exported names before it can name its own.

  **And the alternative is refused on the project's own evidence.** Making it a function of the
  run instead is one line, and the shipped artifact would be identical because the committed tree
  is always a whole-population run — but it leaves
  `test_one_documents_module_is_the_same_text_alone_as_with_the_whole_bundle` GREEN while the
  property it names is false for the documents behind the collisions, because its population does
  not include one of them. A test green on a false property is this project's most expensive
  recurring defect, and buying one line with one is not a trade.

  **THE ROOT AXIS IS A PARSE; A NESTED NAME IS A WALK.** A ROOT's name is a title and parse
  gives it — 1,054
  raw documents read at ROOT cost 0.23 s, which is why the root axis is free. A NESTED name needs
  which positions exist and what kind each one is, and that is the WALK's decision, not the
  parse's: an untitled `enum` branch becomes a `Literal` and declares no class, §5's widenings drop
  a position outright, and §4's bare-`$ref` rung takes its target's distinguishing remainder, which
  needs the target already named in §10's dependency order. A parse answering that would
  re-implement every one of those decisions, which is the second derivation §3 forbids.

  So the case is **two passes: walk and name with an empty surface, collect the exported symbols,
  walk and name again with the real one.** Approved, with the scope reduced: **pass one ranges over
  the DOMAIN, not the bundle**, because the collision scope is the domain and a domain's membership
  is a function of the bundle — so the pass stays bundle-derived and §9 stays true. `core` is 497 of
  the 1,054 documents and is the worst case; most domains are a handful.

  Where that still costs too much on the one-document path, the answer is a CACHE and not a
  shortcut: the export symbols are a function of the bundle, so they key on the bundle's content
  exactly as `tests/compiled.py` keys a compile. A miss costs the walk, a hit costs nothing, and a
  content address cannot go stale — which is why this is not the second derived artifact the
  corpus argument was about.
- **Do not decide a position the bundle does not hold from a view of it.** A case that appears
  only in a canonicalised or otherwise rewritten copy of a document is the copy's, and a row
  deciding it decides nothing the bundle states; the document of record (§3) is what the tables
  decide over.
