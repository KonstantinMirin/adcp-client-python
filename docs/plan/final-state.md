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

Three forms of the same evasion:

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
DEGREE.** The rule against asserting code structure is right about what it names — a count of
lines, imports or call sites freezes the structure, blocks the refactor it was meant to encourage,
and proves nothing, because there are unboundedly many wrong structures and enumerating a few is
not a strategy. It does not forbid every check over the code.

A COUNT says *there are N of these*. An INVARIANT says *this cannot happen*. The first goes stale
the moment anyone moves a line; the second is a statement about behaviour that survives any
refactor preserving it. **Invariants over the code are required, and these are the ones:**

- **every producer reaches a consumer.** A set with several producers and one consumer, placed
  where some producers do not reach it, loses facts silently.
- **a claimed funnel is the only path.** A comment asserting "the one funnel X passes through" is
  an invariant written as prose; where a second path exists it is a defect the comment hides.
- **a derived reading has one owner.** A callee that re-derives what the caller already knows is
  both a cost and a divergence waiting to happen.
- **a figure in a comment or a docstring is derived, never written.**
- **a name a layer mints is a name**, not an index. A layer that hoists a repeated thing and calls
  it by its position is doing anonymously what the layer above it does with judgement.

**And the ordinary tools count as invariants here.** A linter's unused-import, shadowed-name,
mutable-default and dead-code rules are invariants over behaviour, not structural pins — so their
absence is not neutrality, it is an unmeasured surface.

**A ROW THAT MOVES NO READING IS NOT BRIEFED.**

---

## 1. Every class states exactly what its document states

Every class accepts every value its document admits, refuses every value its document refuses, and
what it dumps validates against that document again.

This is the deliverable's correctness and the definition of "the schemas produced classes".
Emission is not this: a document emits when the walk produces a class for it, which says nothing
about what the class states.

**THIS IS A PROPERTY OF THE COMPILER AND NOT OF ONE BUNDLE.** It must hold for every document of
every bundle the compiler is pointed at, so nothing deciding it may be keyed to one bundle's state.

**Decided by two checks and there is no third:**

1. **Draw a value from the document. The class must admit it.**
2. **Instantiate the class, dump it. The document must admit the dump.**

Plus the declared widenings of reading 2, each proved by a value.

**BOTH CHECKS ARE A FUNCTION OF (class, document) AND OF NOTHING ELSE.** Point them at another
bundle and they answer for that bundle, because there is nothing to carry over and nothing to
expire. **A stored value, a key over a document's bytes, or any artifact that must be re-derived
when the bundle moves makes an improvement to the schema cost exactly as much as a regression** —
and it makes the instrument answer for the bundle it was built against instead of for the compiler.

**A PAIR THAT CAN ONLY BE GRADED FROM A STORE IS NOT VERIFIED, IT IS REMEMBERED.** Where a store is
load-bearing rather than a saving, the reading does not hold for that pair and the store is hiding
it.

**AND WHERE A VALUE CANNOT BE DRAWN, THE DOCUMENT'S OWN `examples` IS THE VALUE.** It is the
schema's statement about itself, it needs no generator, and it survives any transformation that
preserves what the document admits. A document that states no example and admits no value a
generator can produce is an ask over a set of the bundle — not a budget, not an exemption, and not
a pair that passes by leaving the check unexecuted. A budget cut is reported as a cut.

## 2. Every exception to reading 1 is a declared widening, proved by a value

A model may be wider than its document and never tighter. Each widening is declared at its own
pointer in the emitted module, the declared set equals the set a run mints in both directions, and
**every declaration holds a value that demonstrates it**. A declaration with no value behind it is
an allowlist wearing a measurement.

**AND THE DEMAND IS OVER FACTS, PROVED AT THE INNERMOST POSITION THAT CARRIES ONE.** A fact stated
at a node and re-declared at every position composing that node is **one** fact, and the value
proving it is drawn where the value can compose. A carrying position inherits that proof; it does
not owe a second one. **The condition is that the innermost carrier is itself graded and passing**
— inheritance from an ungraded position proves nothing, and that is the only way this clause could
be read as a weakening.

**BECAUSE A PRESENCE-TRIGGERED CONDITIONAL AT A CARRYING POSITION ADMITS NO VALUE AT ALL.** The
document there refuses the pair (value, its siblings) rather than the value, so no payload composes
and the demand is not merely expensive but unsatisfiable. **A reading that asks for a value which
cannot exist is not strict, it is wrong** — and its cost is paid in instruments that look like
rigour while measuring nothing.

**Decided by** the set equality in both directions, and by the store of proving values containing
one for each FACT — where an entry recording a budget cut is not a value, and where a count over
carrying positions is not the count this reading names.

## 3. Every union root dispatches

A payload offered to a union base resolves to its branch, for every payload the document admits.
The dispatch key is one that **determines** the branch, which requires the document to guarantee
its presence in every instance it admits — pinning a key is not determining it.

**AND WHERE THE DOCUMENT DETERMINES NO BRANCH, THE DISPATCH REFUSES AND SAYS SO.** A union whose
document states no discriminator and whose branches overlap admits one payload at many branches at
once — so there is no branch to resolve to, and a structural first match is a **guess wearing a
type**. The honest answer is a refusal naming the branch it would have chosen, the absent
discriminator, and the document's own sentence.

**THAT REFUSAL IS NOT A NARROWING, AND READING 1 IS NOT IN TENSION WITH IT.** Reading 1 forbids a
class tighter than its document over the values a pair admits. A union root with overlapping
branches and no key **has no determined pair** — the document admits the value and names no type
for it — so declining to answer is not refusing a value the pair accepts. **A quiet wrong object is
worse than a loud refusal**, because the caller discovers it at the far end of their own code, and
the ambiguity is the schema's to resolve rather than ours to guess past. It is an upstream ask in
every instance, and the ask is usually one word.

**Decided by** constructing every union base's dispatch over the whole tree and requiring that none
raises, plus: no union dispatches on a key its document lets an instance omit; and **where the
document admits exactly one branch, the dispatch may not refuse** — which is what keeps the clause
above from becoming a licence to refuse anything hard.

## 4. Each distinct TYPE is one type, at every layer the catalogue has

**A type stated at more than one position is written once and referenced, never restated — and
this reading ranges over EVERY LAYER THE CATALOGUE HAS**, not the first: enum vocabularies,
constrained scalars, object types, array types, and the repeated DOCUMENT above them all. The named
type is constructed from that one definition, and the entry lives in the narrowest namespace
containing every position that references it.

**This reading names no number of layers: it names the catalogue, and the catalogue's layers are
the structure document's to add to.** A count here is a ceiling nobody intended.

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

**AND A CENSUS CONFIRMS THIS READING; IT DOES NOT ESTABLISH IT.** This reading holds because the
compiler **decides a type once** — the catalogue is built complete before anything is lowered,
every node asks it, and **a name is minted per ENTRY and never per position.** Where that order
holds, there is nothing for a census to find; where it is inverted, no census can do better than
enumerate the leaks one instrument at a time. **A gate that FINDS duplication is therefore evidence
the order is wrong, not evidence the gate is working.** The structure document fixes that order and
a handler does not get to negotiate it.

**Decided by** the catalogue being the thing that answers, at every node — and a regression guard
per layer, keyed on that layer's own identity, confirming that nothing slipped. The guard's key is
that layer's identity: the value list, the constraint set, the field set, the element type. **A
guard keyed on a name, an export path or a constraint set cannot see a repeated object type.** And
**not every layer has a set of classes to read over the tree**: an array type renders as `list[X]`
inside an annotation and declares no class, so the array layer is read off the bundle's own stating
positions while the object layer can be read off either. A guard that assumes every layer appears
as a class silently skips one.

## 5. The record states each distinct subtree once

A document of record stores each distinct subtree once and references it at every occurrence. **The
pointers readers spell do not change** — the storage is a DAG, the pointer language is not, because
the corpus key hashes the pointer and a respelling discards every held value.

**Decided by** the record's own size: no record exceeds its source document by more than the
references it resolves **plus the bookkeeping the sentence above mandates** — the entry names and
the occurrence references that storing once requires.

**THE ALLOWANCE IS NOT A CONCESSION, IT IS ARITHMETIC.** A stored reference costs more bytes than
the shortest subtrees in the bundle contain, so storing those once makes the record LARGER. Without
the term, the decider reddens for obeying its own first sentence — and a decider that punishes the
thing it mandates is measuring the wrong quantity, not finding a defect.

## 6. Every class is importable at exactly one path

`from adcp.types.<domain> import <Name>` reaches every class the tree declares — roots, union
branches and aliases alike — at exactly one such path, with the domain derived from the document's
own path. No second way reaches the same class, and no name in one namespace means two classes.

**AND ONE NAME MEANING TWO THINGS IN TWO NAMESPACES IS NOT A VIOLATION OF THIS READING, BUT IT IS
NOT NOTHING EITHER.** Where the bundle titles two unrelated nodes alike — one an object with a
`oneOf`, one an enumeration, neither referencing the other — reading 4 is right to keep them apart,
because they admit different sets, and this reading is satisfied, because each is at exactly one
path and no single namespace carries one name for two classes.

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
decides nothing here — it is readable with or without a marker.

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

**EVERY TYPE SPELLING AN APPLICATION USES RESOLVES TO OUR OBJECT.** Every name upstream's wheel
exposes publicly **from its type surface** either **is** one of ours, or is an **alias** to one of
ours, or carries a **verdict** saying why it should not exist.

**THIS READING IS STATED OVER THE TYPE SURFACE AND NOT OVER UPSTREAM'S WHOLE WHEEL.** Most of what
consumer code imports from that wheel is machinery this project does not emit and cannot derive
from a schema. **And no layer of ours shadows `adcp.types`**: upstream's wheel imports its own
types from that module, so a shadow of it breaks the package that depends on it, and the names
behind those imports come from the very layers this reading's own verdicts say should not exist.

**THE FLAT `adcp.types` NAMESPACE IS AN ALIAS LAYER.** §1's design separates the private generated
tree from the public surface for exactly this reason: **so that a generated class can change
without disturbing what an application imports.** Every name upstream's flat namespace carries
becomes **an alias into whatever we generate**, and `adcp.types.<domain>` is the new surface beside
it rather than instead of it.

So the three layers are:

- **`adcp.types._schemas.<path>`** — private, generated, free to change.
- **`adcp.types.<domain>`** — the surface §1 decides, one import path per declaration.
- **`adcp.types` flat** — the compatibility surface: **an alias for every name an application
  actually imports today, pointing at the generated class.** An alias is a NAME, so reading 6 holds
  with the aliases counted.

**AND "ALREADY RESOLVES" IS MEASURED AT THE SPELLING A CONSUMER WRITES, NEVER AT THE MODULE THAT
DECLARES IT.** A name upstream carries at `adcp.types.<domain>.<Name>` and that we also declare at
`adcp.types.<domain>.<Name>` is **not thereby reachable**: the import an application has already
written is `from adcp.types import <Name>`, and the flat namespace is where that resolves or raises.
So a name counted *present* because its domain path matches **owes a flat alias exactly as a
relocated one does** — the buckets differ in where the alias points, never in whether one is owed.

**THIS IS NOT THE SPELLING RULE'S OPPOSITE, IT IS ITS BOUNDARY.** Refusing to reproduce upstream's
spellings means refusing to put one object at every module upstream happens to expose it from. It
does not mean refusing the **one** namespace an application imports from, which this reading names
as a layer. One declared flat surface is a canonical location; a name at every module that mentions
it is the accident.

**AND THE CLAUSE IS GRADED OVER WHAT CONSUMER CODE ACTUALLY WRITES, NOT OVER THE TABLE'S OWN ROWS.**
A table can be complete against itself and leave the written import failing — so the measurement is
the set of flat spellings appearing in upstream's own examples, scripts and documentation, resolved
from an environment holding only the installed wheel. A bucket that explains why a row needs no
alias is only sound if the spelling it refers to is the one a caller uses.

**Decided by** the spellings consumer code actually writes — not our table's rows — each resolving
from an environment holding only the installed wheel or carrying a **declared verdict** saying why it
should not exist; by `is` holding across every spelling of one subject, since an alias is a NAME and
a second object would be a second type; and by reading 6 still holding with the aliases counted.
**A table complete against itself proves nothing here**, because the thing being claimed is about
an import someone else already wrote.

**A NAME WITH NO SCHEMA SUBJECT GETS A MIGRATION NOTE AND NEVER A CLASS.** Where upstream's flat
namespace carries something no document states — a hand-written ergonomic, eager, legacy or
registry layer — an alias has nothing to point at, and **minting a nodeless class to satisfy an
import is the back door this ordering exists to close.** Those are named in a migration guide, with
what to use instead.

**AND THE SET IS WHAT CONSUMERS IMPORT, NOT WHAT UPSTREAM'S WHEEL EXPORTS.** Most of that export
surface is reachable only because a module forgot to declare what it exports. **The set that decides
this reading is measured off real consumer code** — upstream's own example server and a production
application — and it is the only denominator that means anything here.

**AN ALIAS IS KEYED ON A SCHEMA SUBJECT, NEVER ON A NAME.** A name resolves to a *different* class
of ours depending on which upstream module the import came from, so one flat alias cannot serve
both. **The key is identity: the field set read by wire alias, or the enum's value list.** A name
is the thing being aliased, not the thing that decides what it aliases to.

**AND A COLLAPSE MUST NOT DECIDE A SPLIT — §4's RULE, AT THIS LAYER.** An instrument that matches
upstream's names onto ours by agreement is a collapse, and many upstream names landing on one class
of ours is a *hypothesis*, not a verdict. Some are one subject spelled twice; some are distinct
subjects our walk folded, and publishing an alias for each would **republish the duplication
reading 4 exists to remove, under the name "compatibility"**. Every many-to-one target is decided
by reading the bundle first — whether it REFERENCES one node from the others or RESTATES it — and
never by the agreement that found it.

**AND NO ALIAS POINTS AT A NAME THIS COMPILER MINTED FROM STRUCTURE.** §4's derivation ends in a
name taken from the structure where the bundle names nothing, and such a name is *pending* an
upstream title. Publishing an alias onto it makes a placeholder permanent and public, which is the
one thing §4's placeholder rule forbids: a name minted for want of a subject must not become a name
an application depends on.

**AND WHERE UPSTREAM'S NAME MEANS A DIFFERENT SET OF VALUES, AN ALIAS IS A DEFECT AND NOT A
BRIDGE.** Their `TaskStatus` is a transport's five states; the schema's is its own list. An alias
there hands a caller something that silently is not what it asked for, which is worse than an
import error. That name takes a migration note naming both sets.

**BUT A DIFFERING IDENTITY IS NOT YET A DIFFERENT SUBJECT, AND THE DOCUMENT SAYS WHICH.** The
identity key — the field set read by wire alias, or the enum's value list — answers *equal* or
*not equal*, and the sentence above spends that single bit as though it were the whole verdict. It
is not. Two identities disagree in two ways that have opposite consequences, and **the instrument
that cannot tell them apart is the instrument at fault, not the names it is pointed at.**

- **THE DOCUMENT ACCOUNTS FOR THE DIFFERENCE.** Upstream states the same subject and deviates from
  it: a required conjunct dropped, a field the document forbids emitted, one class minted per
  call site where the document states one node. Here **the alias is OWED, and it is owed precisely
  BECAUSE the identities differ** — the caller wrote that name meaning that subject, and what the
  alias hands back is what the document says the subject is. **Aliasing onto our class is not
  conforming to their defect, it is refusing to.** The alternative on offer is never "the caller
  gets upstream's meaning"; it is an import error, or our class widened to readmit the defect,
  and reading 1 forbids the second outright.
- **THE DOCUMENT ACCOUNTS FOR NOTHING.** Upstream's name denotes a referent the bundle does not
  state — a transport's own state machine, a hand-written ergonomic layer's record — which shares
  a word with a schema subject and nothing else. Here the sentence above stands unchanged: no
  alias, a migration note naming both sets.

**AND THE SPLIT IS PROVED PER ELEMENT, NEVER BY A RATIO.** For each element of upstream's identity,
name where the document states it or state that it does not. A count of agreements over a
denominator would let a majority decide a split, and **§4's rule that a collapse must not decide a
split is the same rule at this layer** — a two-thirds overlap is a hypothesis about one subject,
not a finding of one. Zero shared elements is disjoint on its face and needs no further argument;
every other case is argued element by element or not at all.

**AND THE NOTE IS WHAT MAKES THE ALIAS ADMISSIBLE, NOT WHAT ACCOMPANIES IT.** The objection the
sentence above raises against a differing alias — that it hands a caller something which silently
is not what was asked for — is answered by the word *silently* and by nothing else. So a shared-
subject alias is graded as a PAIR: the alias, and a migration-guide entry naming both sets, which
one the document states with its pointer, and what a caller must change. **An alias whose entry is
missing is a reading 10 FAILURE and not partial credit**, because an undisclosed substitution is
the exact defect this reading refused, arriving with our name on it instead of theirs.

**AND THIS PUTS THOSE NAMES IN THE ALIAS LAYER AND THE MIGRATION GUIDE AT ONCE, BY CONSTRUCTION.**
Where an instrument excludes aliased names from the guide on the ground that they are the alias
layer's business, that exclusion now holds only for names whose identity AGREES — those carry
nothing to disclose. A shared-subject alias is in both places because the pair is the unit.

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

**And the comparison is one-directional.** Every name upstream's wheel exposes gets a verdict; the
reverse is not asked. **A smaller count on our side is the expected outcome and not a deficit.**

**THE TARGET IS A NAME AT A CANONICAL MODULE, NEVER A SPELLING.** Upstream's wheel exposes one name
at several modules, and most of its public modules declare no `__all__` at all — so the set of
spellings is several times the set of names. **Reproducing spellings would put one object at several
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

**And decided, for every name whose identity differs, by the per-element split and by the pair.**
Each such name is assigned to the shared-subject bucket or the disjoint-subject bucket **with its
element-by-element reading recorded**, since a differing identity assigned to neither is this
reading's work left undone wearing a measurement's clothes. Every shared-subject name resolves to
our class AND has its migration-guide entry; every disjoint-subject name resolves to nothing and
has its entry. **The grade is over pairs, and an alias counted without its entry is a failure** —
so the two buckets' sizes must sum to the differing-identity count, and neither bucket may be
empty by assumption rather than by measurement.

---

## How to change this file

Change a reading when the **target** changes, not when progress is made against it. If a sentence
here would read differently next week because something landed, it is status and belongs in `bd`.

To add a reading, state the fact about the artifact and name what decides it. If nothing decides it
yet, say so and name what would — a reading whose check is imagined is a wish, and this file holds
the target.
