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

**Decided by three checks and there is no fourth:**

1. **Construct a value from the document's own keywords. The class must admit it.**
2. **Violate one keyword the document states. The class must refuse it, there.**
3. **Instantiate the class, dump it. The document must admit the dump.**

The first says the class is no narrower than its document, the second that it is no wider, the third
that what the class emits is what the document admits. Plus the declared deviations of reading 2 —
widenings, and the narrowings it admits on three conditions — each proved by a value.

**THE VALUE IS CONSTRUCTED, NEVER SEARCHED FOR.** A node's keywords state what it admits, so a value
it admits is read off them: a stated constant, a first enum member, the required keys, exactly as
many characters or items as a bound demands, and for a reference the value already built for its
target. The construction is bottom-up and total, so **a value exists for every node and the cost of
a document is one walk of it.** A sampler is a different instrument answering a different question,
and this reading never asks it.

**THE REFUSING VALUE IS A MUTATION OF THE ADMITTED ONE, AND IT NAMES THE KEYWORD IT VIOLATES.**
Changing exactly one stated fact isolates the keyword under test from every other keyword at the
node, and reading the refusal at its location is what makes check 2 more than a boolean: a class
that refuses for some other reason has not been shown to carry the keyword at all.

**ALL THREE CHECKS ARE A FUNCTION OF (class, document) AND OF NOTHING ELSE.** Point them at another
bundle and they answer for that bundle, because there is nothing to carry over and nothing to
expire. **A stored value, a key over a document's bytes, or any artifact that must be re-derived
when the bundle moves makes an improvement to the schema cost exactly as much as a regression** —
and it makes the instrument answer for the bundle it was built against instead of for the compiler.

**A PAIR THAT CAN ONLY BE GRADED FROM A STORE IS NOT VERIFIED, IT IS REMEMBERED.** Where a store is
load-bearing rather than a saving, the reading does not hold for that pair and the store is hiding
it. Construction is what makes this reading hold without a store: there is no answer expensive
enough to be worth keeping, so **no corpus of values is held, committed or versioned.**

**AND WHERE CONSTRUCTION CANNOT PRODUCE A VALUE, THE DOCUMENT'S OWN `examples` IS THE VALUE.** An
arbitrary `pattern` and a `format` that cannot be generated are the cases: the keyword states a set
the construction cannot enumerate. The document's own stated instance is the schema's statement
about itself, it needs no generator, and it survives any transformation that preserves what the
document admits. A document that states no example and admits no value construction can produce is
an ask over a set of the bundle — not a budget, not an exemption, and not a pair that passes by
leaving the check unexecuted.

**NO CHECK CARRIES A BUDGET, A DEPTH LIMIT OR AN EXAMPLE COUNT.** Each of the three terminates
structurally: one visit per node, one mutation per stated keyword, and a cycle closed by the pointer
already in progress. A parameter that bounds a check is evidence its cost is not understood, and
every pair such a parameter cuts is a check that did not run.

## 2. Every exception to reading 1 is declared and proved by a value

A model may be wider than its document, and **tighter only where the excluded set is declared and
judged unsent**. Each deviation is declared at its own pointer in the emitted module, the declared
set equals the set a run mints in both directions, and **every declaration holds a value that
demonstrates it**. A declaration with no value behind it is an allowlist wearing a measurement.

**AND A NARROWING IS NOT A WIDENING READ BACKWARDS — THE TWO FAIL IN OPPOSITE DIRECTIONS.** A
widening admits what the document forbids, so bad data passes and the caller never learns. A
narrowing refuses what the document admits, so a conforming caller is blocked and **learns
immediately, by an error naming the field.** That asymmetry is why the two take different admission
tests and not one: a widening is dangerous in proportion to what slips through unseen, and a
narrowing in proportion to what a real caller actually sends.

**SO A NARROWING IS ADMISSIBLE ON THREE CONDITIONS, AND THE THIRD IS A JUDGEMENT AND MUST SAY
WHOSE.** It is declared at its own pointer like a widening; it holds a value the document admits and
the class refuses, **with the class's reason named beside the document's sentence**; and the set it
excludes is NAMED and judged one no caller sends. The third condition is not a measurement and must
never be dressed as one — "no caller sends a 4,096-character URL" is a claim about the world that a
person owns, recorded with their name, and revisable when a caller does.

**AND THE REPAIR FOR A NARROWING IS NEVER TO DELETE THE TYPE THAT CAUSES IT, WHERE THE TYPE IS
RULED RIGHT.** Where a URL is to be a URL, widening it to the document's own `str` to clear a
length finding discards every other fact the type carries — scheme, host, parseability — to settle
a bound nobody reaches. **That trade is the instrument steering the artifact**, which is the one
direction this file forbids throughout. The finding is answered by the declaration, not by the type
it indicts.

**AN UNDECLARED NARROWING IS STILL A READING 1 FAILURE**, exactly as an undeclared widening is. The
default is refusal; this clause opens a door and does not remove the wall.

**AND THE DEMAND IS OVER FACTS, PROVED AT THE INNERMOST POSITION THAT CARRIES ONE.** A fact stated
at a node and re-declared at every position composing that node is **one** fact, and the value
proving it is constructed where the value can compose. A carrying position inherits that proof; it does
not owe a second one. **The condition is that the innermost carrier is itself graded and passing**
— inheritance from an ungraded position proves nothing, and that is the only way this clause could
be read as a weakening.

**BECAUSE A PRESENCE-TRIGGERED CONDITIONAL AT A CARRYING POSITION ADMITS NO VALUE AT ALL.** The
document there refuses the pair (value, its siblings) rather than the value, so no payload composes
and the demand is not merely expensive but unsatisfiable. **A reading that asks for a value which
cannot exist is not strict, it is wrong** — and its cost is paid in instruments that look like
rigour while measuring nothing.

**Decided by** the set equality in both directions, and by a proving value existing for each FACT —
constructed on the run that reports it, never held between runs, and where a count over carrying
positions is not the count this reading names.

**And decided, for a narrowing, by all three conditions at once.** The declaration, the value with
both reasons named, and the excluded set with the judgement's owner beside it. **A narrowing
carrying two of the three is undeclared**, because the missing one is always the one that would have
made it reviewable: a declaration with no value is an allowlist, a value with no named owner is a
preference, and an excluded set left unnamed cannot be checked against a caller who turns up
sending it.

## 3. Every union root dispatches

A payload offered to a union base resolves to its branch, for every payload the document admits.
The dispatch key is one that **determines** the branch, which requires the document to guarantee
its presence in every instance it admits — pinning a key is not determining it.

**AND EVERY REFUSAL NAMES WHERE.** A union is emitted as a base and one class per branch precisely
so that a caller learns *which field* was wrong — so a refusal that reports the combinator at the
root and discards the path has thrown away the thing the structure was built to carry. **The
location is not diagnostics, it is the wire**: it becomes the `field` of the error the SDK hands
back, and a caller who receives `loc=()` is told only that something, somewhere, did not match.

**AND IT IS THE WHOLE PATH, THROUGH EVERY HOP.** `('packages', 0, 'targeting_overlay',
'geo_countries', 0)` crosses a list index, a nested model and a second list. A dispatch that
prepends its own position while losing the branch's inner path satisfies a one-level union and
fails the only case anyone meets. **The branch's own error is the answer; the dispatch's job is to
carry it outward, never to replace it with one of its own.**

**AND THE "NO BRANCH DETERMINED" REFUSAL OWES A LOCATION TOO.** The clause below gives that refusal
a good sentence — the branch it would have chosen, the absent discriminator, the document's own
words — and a good sentence at no position is still a caller who cannot find the field. The
message and the location are separate obligations and neither excuses the other.

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
the pointer is what names a node to every reader of the record, and a respelling renames what no
reader asked to have renamed.

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

**AND AN UNTITLED INNER NODE IS EXPORTED UNDER ITS PARENT'S NAME AND ITS KEY, ALWAYS — NEVER ONLY
WHEN THE KEY COLLIDES.** A domain carries many a `method`, a `target`, an `items`, so the key alone
cannot be the export for all of them. The tempting rule is to export the key alone where it happens
to be unique in its domain and to prefix only the rest; measured, that would be 1,066 bare and 314
prefixed across 121 colliding words. **REFUSE IT, because such a name is not stable under the
bundle's own growth:** a document arriving later with a colliding key would RENAME an export an
application already imports, and a public name that changes because something unrelated was added
is worse than a long one. The uniform rule costs verbosity; the conditional rule costs a name's
meaning, and only one of those is recoverable.

**AND "THE PARENT'S NAME" IS THE PARENT'S OWN EXPORT WORD, READ TRANSITIVELY TO THE NEAREST TITLED
ANCESTOR** — so the word is the node's whole chain and not its last two links. The sentence above
admits three readings and only this one leaves no collision: the literal depth-2 reading leaves
words that two positions of one domain both want, and keying on the parent's *post-collision*
symbol cannot answer at all for a node whose parent is itself unnamed. **This reading is also the
only one that is a function of the document's path alone**, which is the stability the clause is
argued from — so it is not a third rule added to rescue the second, it is what the argument already
required and the sentence failed to say.

**AND A NAME THIS RULE MINTS IS STILL PENDING AN UPSTREAM TITLE**, because the bundle titled nothing
here — so it is a §4 placeholder with every consequence §4 attaches, and reading 10's prohibition on
aliasing onto a minted name applies to it unchanged except where that reading's own deprecation
clause admits one.

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

**UNLESS THE ALIAS IS UPSTREAM'S OWN PUBLISHED WORD, DECLARED DEPRECATED AND PENDING.** The
sentence above guards against *creating* a permanent public commitment to a placeholder. Where
upstream's wheel already ships that spelling, the commitment exists and is theirs; an alias
**records** it rather than minting it, and refusing one withholds a name a caller has already
written while changing nothing about what the bundle titles. So the alias is admissible **and the
migration entry must say the word is PROVISIONAL** — naming the untitled node by pointer and the
upstream ask that would title it. **A deprecated alias is the one kind of public name an
application can be told to stop depending on**, which is exactly what a placeholder needs and what
a surface name cannot offer.

**AND THIS IS NOT A LICENCE TO MINT: THE EXPORT COMES FIRST, AND READING 6 OWES IT.** An inner node
we declare privately is invisible to any join over public names, and the row then reads *absent*
although we state the subject and the value lists agree. The repair is the one §4 already names —
**an EXPORT or a NAME, never a split.** A property key is NOT a type name: the bundle calling a
field `method` does not title the enum behind it, and `Method` alone cannot be the export because a
domain carries many. So the export's word is minted from the parent class and the key together,
and **the fact that upstream's derivation lands on the same word is evidence the derivation is the
natural one, not a concession to their spelling.**

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

**AND THE READING IS STATED AT ATTRIBUTE GRANULARITY WHEREVER THE DOCUMENT DECIDES NO IDENTIFIER.**
An enum member is a spelling an application writes, and the table cannot reach it because the table
ranges over names. `core/error.json` states the value list `transient|correctable|terminal` and says
**nothing** about the attribute a caller types — so `TRANSIENT` is OUR convention and the value
verbatim is theirs, and **neither is the document's.** Refusing the alias there defends the schema
from nothing: both enums admit exactly the same set, so it is not a wire difference and not a
reading 1 failure. **The emitted enum carries upstream's derived spelling as an alias member**, and
one member spelling blocked more of upstream's behavioural tests than any class name.

**AND OURS IS UPPER_SNAKE BECAUSE THAT IS PYTHON'S, NOT BECAUSE IT IS OURS.** An enum member is a
constant, and the standard library is uniform about it — `HTTPStatus.CONTINUE`, `Signals.SIGHUP`,
`AddressFamily.AF_UNSPEC`. Upstream's member is the value pushed through its generator's identifier
sanitiser, which is a tool's artefact and no convention at all. **So this is not a tie between two
house styles: one side is the language's and the other is a mangling.** Ours is canonical, theirs is
the alias, and the migration note says deprecated.

**AND "THE DERIVED SPELLING" IS NOT "THE VALUE VERBATIM", WHICH IS THE WORD THAT COST 159 FILES.**
Where the value is already an identifier the two coincide and the distinction is invisible; where it
is not — a kebab value like `media-buy` — upstream does not refuse it, it **SANITISES** it to
`media_buy` and ships that. A rule phrased as *verbatim* therefore reads the unsanitisable case as a
REFUSAL, and the alias never appears. **The refusal classes below are over what the sanitiser cannot
rescue, never over what it was built to handle** — and the derivation is upstream's own, read off
their installed wheel rather than guessed from their output.

**AN ENUM ALIAS IS A NAME AND NEVER A SECOND MEMBER.** `Recovery.transient` **is**
`Recovery.TRANSIENT`: `__members__` unchanged, no value set widened, no approximated fact arising.
That is the same sentence as the one below it, read one level down.

**AND IT IS EMITTED IN THE CLASS BODY, NEVER INSTALLED AT RUNTIME.** Reading 8 says the wheel is
the artifact, and an alias that exists because an import had a side effect is not in the artifact —
it is a property of having run. One line per member, no import and no walk. **The runtime form
already proved itself wrong rather than merely inelegant:** installing the members eagerly bound
the private tree before the suite's own fixtures and brought down the collector, which is what a
layer that must run before being true looks like when it is late.

**THE ALIAS IS REFUSED WHERE THE SPELLING CANNOT BE ONE *AFTER* SANITISING**: where no identifier
can be derived at all, where two values sanitise onto one attribute, and where the derived spelling
collides with a canonical member. Those are reported with their counts, not silently skipped — a member
upstream spells and we cannot is a migration-guide entry, by the pair rule above.

**AND THE FIRST CLASS IS SMALLER THAN THIS READING FIRST NAMED IT, WHICH IS THE DERIVATION
CORRECTING THE RULE RATHER THAN THE RULE BEING APPROXIMATED.** This clause named a leading digit,
the empty string and pure punctuation as cases where no identifier derives. Read off upstream's
wheel, all three ARE derivable: the sanitiser prefixes them, so `1.0` becomes `field_1_0` and
`3d_render` becomes `field_3d_render`, and a value made only of punctuation derives the prefix
alone. The class holds what has no spelling on *either* package — a non-string value — and the
implementation is where the measured partition is read (`codegen.lower.enum.ALIAS_REFUSALS`). **A
refusal class named from the outside and not measured is the same mistake as the word *verbatim*
above, one level down**: it describes what a rule-writer expects a sanitiser to fail at instead of
what it does.

**AND A FOURTH REASON, WHICH THE IMPLEMENTATION MEASURED AND THESE THREE DID NOT NAME**: where the
value verbatim is a name the **enumeration itself already resolves**. `"name"` and `"value"` are
live enum values of this bundle, so the first tree emitted under this clause carried
`name = MemberAlias('NAME')` and `Kind.NAME.name` returned the MEMBER — `enum.Enum.name`'s own
descriptor shadowed by a class-body line, the enum protocol broken on a class whose document says
nothing about Python attributes. `pass` and `global` are live values too, and their verbatim
spellings are KEYWORDS: four modules that do not parse. The three above are collisions with
something a *document* put in the class; this one is a collision with the *language*, and it is
counted on its own terms rather than folded into one of them
(`codegen.lower.enum.ALIAS_REFUSALS`, `adcp.types._base.MEMBER_NAMES_TAKEN`).

**AND THE FOUR REASONS PARTITION THE MEMBER SPELLINGS, WHICH IS THE CLAUSE THAT MAKES THEM
CHECKABLE.** Aliased plus the four refusals equals every spelling the bundle states, asserted as a
partition — so **a fifth reason BREAKS the gate instead of hiding inside it**, which is the only
form in which "we counted the exceptions" is a statement about the artifact rather than about who
was looking. **The re-casing reason is expected empty and that expectation is MEASURED, not proved —
and I first wrote it the other way.** §5's `enum` row sends a node whose two values spell one member
name to a `Literal` with no class and no member names at all, so a collision there is a
migration-guide entry at the NODE, where both spellings are gone. That is a strong reason to expect
emptiness and it is **not** a construction: the canonical namer keeps any character `str.isalnum`
admits, the sanitiser keeps only ASCII, **so the two can disagree and the class can fill.** Calling
it empty by construction asserted a theorem over two functions that were never shown to agree —
which is the same error as the word *verbatim* and the leading-digit list above, for the third time
in one clause. **An expected-empty count with no mechanism behind it is a coincidence waiting to be
reported as a property**, so the count is read from the implementation and the gate's partition is
what would catch it filling.

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
