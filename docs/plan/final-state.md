# The final state

**TEN READINGS. Each is a statement about the finished artifact, and each names what decides it.**

**Readings 1 to 9 are FAITHFULNESS and reading 10 is the DROP-IN, and the order is not a
preference: a class exists because a schema node states it, and reading 10 may not reshape any of
the nine to make itself easier. Designing the classes so the aliases are convenient is how
upstream's mistakes arrive through the back door.**

This file holds the target and nothing else. It carries no measurement, no progress, no row — those
go stale on the next merge, and a stale number in a rule document gets believed. **Current status
lives in `bd`.** Ask `bd` what holds today; ask this what holding means.

## What belongs here

**A READING IS OBSERVABLE IN THE ARTIFACT.** A consumer who has only the installed wheel and the
bundle can check it. A property of `codegen/` that no consumer can observe is not a reading and
must not be gated: there are unboundedly many wrong internal structures, enumerating a few proves
nothing, and gating them freezes the structure against the refactor the gate was meant to
encourage.

**A READING HOLDS OR IT DOES NOT.** Never M of N. A fraction is a statement about the instrument,
not about the artifact.

**A READING NAMES WHAT DECIDES IT**, and that must be something that fails when the reading fails.
A check that passes when nothing happens decides nothing.

**NO CHECK IS MARKED EXPECTED-TO-FAIL, SKIPPED, OR SCOPED AWAY FROM THE CODE IT IS ABOUT.** This
code is new; there is no legacy to carry and nothing to grandfather. A red is a defect with an
owner or it is fixed — never a marker, because a marker converts a failing check into a passing
suite and the suite is what anyone reads.

Three forms of the same evasion, and each has been found here:

- **An expected-failure marker.** Legitimate only as a gate written before the work it gates, and
  then it must be strict, so that the moment the work lands the marker's own passing is an error
  and must be removed in the same commit.
- **A skip when a tool is missing.** A gate that disappears with its own instrument is worse than
  no gate: it reports green. Absent tooling is an error.
- **A scope that omits the code the check is about.** A type checker configured over part of the
  tree is green for free on the rest, and a guard asserting "the scope is not a corner" is worthless
  if its own required set shares the omission. **The shipped package is in scope by definition** —
  it is the artifact every reading is about.

**AN INVARIANT OVER THE CODE IS NOT A STRUCTURAL ASSERTION, AND THE DIFFERENCE IS NOT A MATTER OF
DEGREE.** The rule against asserting code structure is right about what it
names — a count of lines, imports or call sites freezes the structure, blocks the refactor it was meant
to encourage, and proves nothing, because there are unboundedly many wrong structures and
enumerating a few is not a strategy. **It has been read as forbidding every check over the code,
and that reading is what let incidental complexity accumulate unmeasured.**

A COUNT says *there are N of these*. An INVARIANT says *this cannot happen*. The first goes stale
the moment anyone moves a line; the second is a statement about behaviour that survives any
refactor preserving it. **Invariants over the code are required, and these are the ones this
project has paid for by not having:**

- **every producer reaches a consumer.** A set with several producers and one consumer, placed
  where some producers do not reach it, loses facts silently — and did.
- **a claimed funnel is the only path.** A comment asserting "the one funnel X passes through" is
  an invariant written as prose; where a second path exists it is a defect the comment hides.
- **a derived reading has one owner.** A callee that re-derives what the caller already knows is
  both a cost and a divergence waiting to happen.
- **a figure in a comment or a docstring is derived, never written.** Every stale census in this
  code was a number someone typed, and each was believed for as long as it stood.
- **a name a layer mints is a name**, not an index. A layer that hoists a repeated thing and calls
  it by its position is doing anonymously what the layer above it does with judgement.

**And the ordinary tools count as invariants here.** A linter's unused-import, shadowed-name,
mutable-default and dead-code rules are invariants over behaviour, not structural pins — so their
absence is not neutrality, it is an unmeasured surface. A repository with none has no reading on
its own incidental complexity, which is the condition under which that complexity is mistaken for
the problem's own.

**A ROW THAT MOVES NO READING IS NOT BRIEFED.**

---

## 1. Every class states exactly what its document states

Every class accepts every value its document admits, refuses every value its document refuses, and
what it dumps validates against that document again.

This is the deliverable's correctness and the definition of "the schemas produced classes".
Emission is not this: a document emits when the walk produces a class for it, which says nothing
about what the class states.

**Decided by** the draw, over every pair of a class and the document and pointer it names. The
verdict is per pair and names the value. A pair the instrument cannot grade is not a pair that
passes: a budget cut is reported as a cut, and no pair passes by leaving the check unexecuted.

## 2. Every exception to reading 1 is a declared widening, proved by a value

A model may be wider than its document and never tighter. Each widening is declared at its own
pointer in the emitted module, the declared set equals the set a run mints in both directions, and
**every declaration holds a value that demonstrates it**. A declaration with no value behind it is
an allowlist wearing a measurement.

**Decided by** the set equality in both directions, and by the store of proving values containing
one for each declaration — where an entry recording a budget cut is not a value.

## 3. Every union root dispatches

A payload offered to a union base resolves to its branch, for every payload the document admits.
The dispatch key is one that **determines** the branch, which requires the document to guarantee
its presence in every instance it admits — pinning a key is not determining it.

**Decided by** constructing every union base's dispatch over the whole tree and requiring that none
raises, plus: no union dispatches on a key its document lets an instance omit.

## 4. Each distinct TYPE is one type, at every layer the catalogue has

**A type stated at more than one position is written once and referenced, never restated — and
this reading ranges over ALL FOUR of the catalogue's layers**, not the first: enum vocabularies,
constrained scalars, object types, and array types. The named type is constructed from that one
definition, and the entry lives in the narrowest namespace containing every position that
references it.

**This reading was written as "each distinct VOCABULARY is one type" and that was too narrow.** A
vocabulary is a set of values, so the sentence asked for one layer while the design specifies four
— and when the value-list gate went green the other three were neither built nor asked for. A
reading narrower than the rule it is named for does not merely miss work: it makes this file lie
about what done means.

**Two positions stating the same thing are not automatically the same concept.** The three-way
split is the rule at every layer, not only the first: one named type where the bundle names the
subject; separate types over one definition where the positions are genuinely different subjects;
and separate types pending a name where nothing in the bundle names it, which is an upstream ask
and not a local answer. A description states what a thing IS, not what it is CALLED, so it mints
no name.

**And the split is decided before the collapse, never by the collapse.** Two classes with one
field set is a hypothesis. Whether the bundle REFERENCES one node from the others or RESTATES it
is the question that tells our defect from the schema's own duplication — the first is ours to
fix, the second is faithful emission and an ask stated over a set of the bundle.

**Decided by** one census per layer, each keyed on that layer's own
identity — and **not every layer has a set of classes to census over the tree**: an array type
renders as `list[X]` inside an annotation and declares no class, so the array layer is read off the
bundle's own stating positions while the object layer can be read off either. A census that assumes
every layer appears as a class silently skips one. The key is that layer's
identity — the value list, the constraint set, the field set, the element type. The key is what
makes a census a census: a gate keyed on a name, an export path or a constraint set cannot see a
repeated object type, which is how three layers stayed invisible while their own measurements sat
in the design.

## 5. The record states each distinct subtree once

A document of record stores each distinct subtree once and references it at every occurrence. **The
pointers readers spell do not change** — the storage is a DAG, the pointer language is not, because
the corpus key hashes the pointer and a respelling discards every held value.

**Decided by** the record's own size: no record exceeds its source document by more than the
references it resolves.

## 6. Every class is importable at exactly one path

`from adcp.types.<domain> import <Name>` reaches every class the tree declares — roots, union
branches and aliases alike — at exactly one such path, with the domain derived from the document's
own path. No second way reaches the same class, and no name in one namespace means two classes.

**AND ONE NAME MEANING TWO THINGS IN TWO NAMESPACES IS NOT A VIOLATION OF THIS READING, BUT IT IS
NOT NOTHING EITHER.** `AudienceSource` is a class at `adcp.types.core` and an enumeration at
`adcp.types.enums`: `core/audience-source.json` is an object with a `oneOf`, `enums/audience-source.json`
is a string with six members, neither references the other, and **both are titled "Audience
Source"**. Reading 4 is right to keep them apart — they admit different sets — and this reading is
satisfied, because each is at exactly one path and no single namespace carries one name for two
classes.

**What it costs is a consumer importing from the wrong module and getting something that silently
is not what they meant**, which no gate here can see because nothing is duplicated. So it is
**reported, with both schema nodes named, and it is an upstream ask over the set of titles the
bundle uses twice for different subjects** — never resolved by renaming one of ours, because the
name comes from the bundle and §4 forbids us to choose a different word for a subject the protocol
has named.

**Decided by** counting OBJECTS, not names: the number of export paths equals the number of distinct
objects behind them, and the object reached is the same object as the private path's. A check that
resolves every export and requires exactly one path each is answered `yes` by two names for one
object, each resolving cleanly — so it reads green while this reading is false. Both checks belong;
the per-name one is incomplete, not wrong.

## 7. The package declares its types to a consumer's type checker

`py.typed` ships, so every annotation the compiler derives — constraint, branch type, enum member —
is visible at the boundary it was built for. The marker promises that a consumer's checker can USE
these annotations; it does not promise that our internals type-check, and an internal error is a
defect we own rather than a bar to shipping it.

**Decided by three directions against an environment holding only the installed wheel**, because
the first two alone pass on a checker that sees nothing: a consumer module using the package
correctly checks clean; a consumer module misusing a field, an enum member and a constructor
reports one error per misuse; and removing the marker from the *installed* package makes every one
of those errors vanish, leaving only the missing-marker notice. Checking our own source tree
decides nothing here — it is readable with or without a marker, which is why the gap survived.

## 8. The wheel is the artifact

The wheel builds, installs into an environment that has never seen this repository, and every
exported name imports from it.

Until this holds, no claim about what ships is verified — including readings 6 and 7, which are
otherwise measured against the source tree, and packaging decides which files a wheel contains.

**Decided by** building, installing clean, and importing every exported name.

## 9. Every approximated fact is attributed

Each declared fact is ours with a decision recorded, or upstream with an issue that exists. An
unfiled gap is ours. And every narrowing taken deliberately is admitted by an enumerated registry
compared by equality against the narrowings the run actually takes — admitted by nothing else,
because a predicate waiver is invisible and permanent.

**Decided by** every `upstream` attribution naming a live issue, and by that registry's equality in
both directions.

## 10. Every spelling an application uses today resolves to our object

**EVERY TYPE SPELLING AN APPLICATION USES RESOLVES TO OUR OBJECT.** Every name upstream exposes
publicly **from its type surface** either **is** one of ours, or is an **alias** to one of ours, or
carries a **verdict** saying why it should not exist.

**THIS READING IS STATED OVER THE TYPE SURFACE AND NOT OVER UPSTREAM'S WHOLE WHEEL, because the
wider claim was measured and is not achievable by anything this project emits.** It said "installs
in place of upstream `adcp` and keeps working without an edit". Measured: of the distinct names
consumer code imports, **under a quarter are types** — the rest is machinery we do not emit and
cannot derive from a schema. And the three mechanisms that would let our types shadow theirs while
depending on them were tested with real installs and all three fail, **for one reason that is not a
packaging reason**: upstream's own machinery imports its types from `adcp.types`, so a shadow of
that module breaks the package that depends on it. Its non-type code imports **806 distinct
(module, name) pairs from `adcp.types` across 1,628 sites, of which none resolves at the same
module against ours and 421 exist nowhere in ours at all** — and those come from the very layers
this reading's own verdicts say should not exist.

**So "a wheel installed in place of upstream" is a decision about a PRODUCT and not a reading about
an artifact**, and it is recorded as the owner's: either we own upstream's machinery too, at the
cost of 421 names with no schema node behind them, or we are the type surface others depend on.
**This reading holds under both** — which is why it is worded over the types, and why that wording
is not a retreat: the type surface is what this compiler produces, what the schema decides, and
the only part whose correctness a reading can state.

**An alias is a NAME and never a second type.** Reading 6 still holds with the aliases counted:
export paths equal distinct declarations, and `isinstance` holds across every spelling. An alias
that is a second class is the duplication this whole project exists to remove, arriving as
compatibility.

**AN ABSENT UPSTREAM NAME IS A QUESTION WITH A VERDICT, NEVER AN INSTRUCTION TO ADD A CLASS.** It
splits two ways and the verdict says which: **we represent it differently** — a fold that keeps
every fact the schema states is us being right and their class redundant, which is the expected
outcome; a fold that is awkward for a caller is answered by an export or a name, never by splitting
a class; a fold that LOSES something the schema states is **our defect** and the fix is in the walk,
which makes it a reading 1 failure and outranks this reading entirely — or **their class should not
exist**: a duplicate of theirs, a hand-written ergonomic layer, or a class from a bundle version
that is not ours. **Name the schema node, or say there isn't one.** Neither verdict may be reached
by reading two class definitions side by side.

**And the comparison is one-directional.** Every name upstream exposes gets a verdict; the reverse
is not asked. **A smaller count on our side is the expected outcome and not a deficit.**

**THE TARGET IS A NAME AT A CANONICAL MODULE, NEVER A SPELLING.** Upstream exposes one name at up
to nine modules, and most of its public modules declare no `__all__` at all — so the set of
spellings is several times the set of names. **Reproducing spellings would put one object at nine
export paths and break reading 6 outright**, which is the back door this ordering exists to close:
compatibility that reintroduces the duplication the rest of the project removed. So an alias layer
targets the NAMES, at a declared set of modules, and a spelling upstream carries only because its
own surface is undisciplined is answered by a verdict and not by a path.

**AND THE SET THIS READING RANGES OVER IS THE DELIBERATE SURFACE.** A name reachable only because a
module forgot to declare what it exports is not a name an application was invited to import, and
treating it as one makes upstream's omission our obligation. Where the two sets differ, say so and
state which one a figure is over — the undisciplined count is the larger and the less meaningful.

**A NAME THAT RAISES ON UPSTREAM'S OWN WHEEL IS NOT A NAME WE OWE.** It is a finding about them,
reported with the error, and it belongs in no bucket that implies work for us.

**Decided by** installing the wheel into an environment that has never seen this repository and
resolving every name in the cross-check's present, renamed and relocated sets — plus every absent
name carrying a verdict that names a schema node or says there is none. A count of unmatched names
with no verdicts attached is not a result.

---

## How to change this file

Change a reading when the **target** changes, not when progress is made against it. If a sentence
here would read differently next week because something landed, it is status and belongs in `bd`.

To add a reading, state the fact about the artifact and name what decides it. If nothing decides it
yet, say so and name what would — a reading whose check is imagined is a wish, and this file holds
the target.
