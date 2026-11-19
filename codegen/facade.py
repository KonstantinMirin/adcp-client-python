"""``adcp/types/__init__.py``: the lazy compatibility facade, with its ``__all__`` WRITTEN.

**THE RULING THIS MODULE IS (the owner, 2026-11-19): "generate, don't derive".**
``adcp.types.__all__`` was a branch of that package's ``__getattr__`` that unioned six
layers' advertisements on every read -- 4,358 names, measured at **4.88 s on the first
access and 0.065 s on every one after**.  Neither number is the reason it moved.  **No
static analyser can evaluate a ``__getattr__`` branch**: an IDE, a linter, mypy, a doc
generator and ``from adcp.types import *`` resolution all read ``__all__`` expecting a
LITERAL, and none of them runs the module.  So the 108 words added on 2026-11-18 to stop
that surface being folklore were bound, were advertised to anything that executed the
branch, and were still invisible to every reader -- the computation was widened and
nothing became discoverable.  A declaration belongs in the module's text, and this is the
generator that puts it there.

**THE SET DOES NOT MOVE, which is the one thing this module may not do.**  :func:`words`
is the SAME union the branch computed, over the same six layers and through the same
``getattr`` screen, asked once per build instead of once per access.  A name added or lost
here is a public-surface change and is not this generator's to take.

**WHY IT IS A GENERATOR OF ITS OWN AND NOT ``codegen/emit.py``'s, which is the structural
half.**  ``emit`` writes ``f(bundle, emitter, compiler)`` and nothing else -- that is what
``tests_emit/test_emit.py::test_the_committed_tree_is_what_a_fresh_run_emits`` ranges over,
byte for byte, and what ``emit.domain_modules``' own clause about this file already said in
its weaker form.  This file's ``__all__`` is not such a function.  Six layers bind a flat
word at ``adcp.types`` and only ONE of them is the compiler's:

====================================  ======  ==========================================
layer                                  words  whose output
====================================  ======  ==========================================
``_surface._flat.__all__``             3,942  ``codegen/emit.py``'s cross-domain union
``compat.__all__``                       988  ``survey/alias_surface.py``
``_adapter.__all__``                     446  ``survey/adapter_surface.py``
``_restored.__all__``                    176  hand-written, DERIVED at import from the
                                              twelve restored modules' own declarations
``_advertised_layers()``                 148  ``aliases.py`` plus ``adcp/core.py``'s own
                                              words, each screened by ``getattr`` here
``compat.__adcp_flat_only__``             79  ``survey/alias_surface.py``
====================================  ======  ==========================================

-- 4,358 unioned, measured on this tree.  Five of the six are not functions of the bundle
at all, so the facade's text is a function of the committed package BESIDE the emitted
tree.  Writing it out of ``emit`` would put a committed artifact on the emission's input
side, which §9 forbids and which the emit gate would then be comparing against itself.
**So the honest arrangement is the one here: the run writes the facade AFTER it writes the
tree, from a reading of the package it just wrote beside, and the emission's byte compare
is left ranging over exactly what it says it does.**

**AND THAT IS WHY THIS FILE IS NOT IN THAT BYTE COMPARE, stated rather than left to be
found.**  ``test_the_committed_tree_is_what_a_fresh_run_emits`` asserts ``sorted(out.beside)``
against a DERIVED set -- the domains, ``constraints.py``, ``envelopes.py`` and the mirror --
so a file this module writes is not in it and could not be added without that test's own
derivation changing.  The check that stands over the facade instead is **re-emission**:
``words()`` is the derivation, the literal is its answer, and
``sorted(set(adcp.types.__all__)) == codegen.facade.words()`` is the one line that says
they agree.  The layer-shaped halves of it are already graded --
``tests_emit/test_the_restored_flat_surface.py`` asserts the restored layer's words are a
SUBSET of ``adcp.types.__all__``, ``tests_emit/test_the_surface_exports_something.py``
asserts every advertised word RESOLVES, and four files under ``tests/`` assert named words
are advertised -- so a short literal and an over-long one both redden somewhere today.
A single whole-set compare is owed and belongs under ``tests/``.

**THE SCOPE GATE IS ``--package``, for ``emit.write``'s reason exactly.**  The facade is ONE
file over the WHOLE run: ``_surface/_flat.py`` is rewritten by ``write`` from whatever
documents a run named, so a one-document run leaves a SHORT ``_flat`` behind and
:func:`words` would read it.  That is the same hazard ``emit.write`` gates D5's alias module
and the prune on, so it is gated the same way and by the same flag -- a whole-population run
passes ``--package`` and nothing else may.

**THE TEMPLATE IS THE FILE, with one line replaced.**  :data:`TEMPLATE` is
``adcp/types/__init__.py`` verbatim except for :data:`SENTINEL`, which the rendered list
takes the place of.  The facade's prose and its lookup chain are the SUBJECT of that file
rather than a rendering of anything, so there is nothing for a renderer to derive them from
and no reading that would make them shorter -- the same arrangement ``render.flat_surface``
has for the 8,800 lines it writes.  What is derived is the one list, and the one thing a
reader has to be able to trust is that the committed file is this template's output, which
a re-emission answers.
"""

from __future__ import annotations

import importlib
from collections.abc import Iterable

#: The package the facade IS.  Its own ``__init__`` is the file this module writes, so the
#: name is the package's and never the file's -- ``adcp.types.__init__`` imports a SECOND
#: module object for one file, which is the defect ``codegen/__main__.py``'s docstring
#: records at the ``runpy`` boundary and which clause 4 of ``test_emit.py``'s
#: ``test_a_document_whose_path_is_also_a_directorys_is_that_packages_root`` holds over the
#: emitted tree.
PACKAGE = "adcp.types"

#: Where the text is written, relative to the ``--package`` directory the run was handed --
#: which is ``emit.write``'s own keying for everything beside the tree, so no caller of this
#: module can be given a path that escapes the directory it passed.
MODULE = "__init__.py"

#: The one line of :data:`TEMPLATE` the rendered list replaces.  Spelled in CAPITALS so it
#: cannot collide with the ``__all__`` the template's own prose discusses a dozen times, and
#: asserted to appear exactly once by :func:`module` -- a template that stopped carrying it
#: would otherwise emit a facade with no ``__all__`` at all, which is the whole of what this
#: generator exists to put there.
SENTINEL = "__ALL__"


def words() -> list[str]:
    """Every word ``adcp.types`` binds, unioned over the six layers that bind one.

    **THIS IS THE DERIVATION THE DELETED ``__getattr__`` BRANCH WAS**, moved from an access
    to a build and otherwise unchanged: the same five module advertisements and the same
    ``_advertised_layers`` screen, sorted into the same set.  The branch's own comment is
    the reason the cost is acceptable here and was acceptable there -- ``compat`` imports
    all 23 domain aggregators, so by the time any of these lists can be read the tree
    ``_flat`` names is already in ``sys.modules``, and the union itself is a set operation
    over 5,779 strings.

    **ASKED OF THE PACKAGE AND NEVER RE-IMPLEMENTED.**  :func:`adcp.types._advertised_layers`
    screens each late word with ``getattr`` on the package, which is a fact about what THIS
    namespace resolves and is decided by a chain of nine consults in that module.  A copy of
    it here would be a second reading of the facade's own answer, and the two would drift the
    first time a layer was added.  So the generator asks and the facade answers.

    **IT READS THE COMMITTED PACKAGE, which is what makes the ORDER in
    ``codegen/__main__.py`` part of the contract**: the run writes the tree and everything
    beside it FIRST, so ``_surface/_flat.py`` on disk is this run's output before this
    function imports it.  A reader who calls this with a stale tree beside it gets the stale
    tree's words, and that is "regenerate, then grade" (``docs/plan/architecture.md`` §5)
    rather than a hole -- there is no bundle reading that could answer for five layers the
    bundle does not state.
    """
    facade = importlib.import_module(PACKAGE)
    compat = importlib.import_module(f"{PACKAGE}.compat")
    adapter = importlib.import_module(f"{PACKAGE}._adapter")
    restored = importlib.import_module(f"{PACKAGE}._restored")
    flat = importlib.import_module(f"{PACKAGE}._surface._flat")
    return sorted(
        {
            *compat.__all__,
            *compat.__adcp_flat_only__,
            *adapter.__all__,
            *restored.__all__,
            *flat.__all__,
            # **AND WHAT THE NAMESPACE BINDS AND USED NOT TO ADVERTISE** (the owner's ruling
            # of 2026-11-18, the facade's own docstring).  Two layers, 148 words, of which
            # 108 were served silently.  The advertisement is of the WORD and never of a
            # subject: ``TaskStatus`` is in here and resolves to the DOCUMENT's enumeration,
            # because the consult that binds it is reached last.
            *facade._advertised_layers(),
        }
    )


def literal(names: Iterable[str]) -> str:
    """``names`` as the ``__all__`` statement, one string per line.

    One per line with a trailing comma, which is black's own "magic trailing comma": the
    list stays exploded, so a word added or removed is ONE line of a diff rather than a
    reflowed paragraph nobody can read.  ``make format`` runs black over ``src/`` and this
    file is not excluded, so a shape black would rewrite is a shape the next formatting run
    would take out of agreement with this generator.

    **EVERY WORD IS CHECKED TO BE AN IDENTIFIER rather than escaped**, which is the one
    place CLAUDE.md's escaping order does not apply because nothing here may need escaping:
    a word on this surface is a name ``getattr`` resolved, so a value carrying a quote, a
    backslash or a newline is a layer having gone wrong upstream and not a string to quote
    correctly.  Refusing it names the layer while the answer is still recoverable; emitting
    it writes a facade that does not parse, and the package then does not import at all.
    """
    out = sorted(names)
    unnameable = [name for name in out if not name.isidentifier()]
    if unnameable:
        raise ValueError(
            f"{len(unnameable)} of the {len(out)} words a layer advertises are not Python "
            f"identifiers and cannot be a name this surface exports: {unnameable[:5]}"
        )
    if not out:
        # A tree whose layers are all absent advertises nothing, and the ANNOTATION is what
        # keeps that importable under mypy: a bare ``[]`` is ``list[Unknown]``.
        return "__all__: list[str] = []"
    return "\n".join(["__all__ = [", *(f'    "{name}",' for name in out), "]"])


def module(names: Iterable[str]) -> str:
    """The text of ``adcp/types/__init__.py``: :data:`TEMPLATE` with the list written in."""
    if TEMPLATE.count(SENTINEL) != 1:
        raise ValueError(
            f"the facade template names {SENTINEL} {TEMPLATE.count(SENTINEL)} times and the "
            "list is written at exactly one place; a template carrying none would emit a "
            "surface with no __all__ at all, which is what this generator is for"
        )
    return TEMPLATE.replace(SENTINEL, literal(names))


#: ``adcp/types/__init__.py``, verbatim but for :data:`SENTINEL`.  The facade's prose and its
#: lookup chain are that file's SUBJECT and are not derived from anything, so the template is
#: the file; what is generated is the one list.  This module's own docstring carries the
#: reading.
TEMPLATE = '''"""The generated types.

**One import path per class, and it is a DOMAIN module.**  ``docs/plan/rebuild-plan.md``
§1: a document compiles to a module at its own path under a private tree --
``core/pagination-request.json`` -> ``adcp.types._schemas.core.pagination_request`` -- and
is re-exported from a module named for its DOMAIN, which is the first segment of the
document's own path.  That module is the path a consumer uses::

    from adcp.types.core import PaginationRequest, AssetRequirements
    from adcp.types.core import AssetRequirementsJavaScript
    from adcp.types.enums import MatchType

    req = PaginationRequest.strict_validate(payload)   # the schema decides
    req = PaginationRequest(max_results=50)            # pydantic constructs
    isinstance(held, AssetRequirementsJavaScript)      # a union hands a branch back

**THE SCHEMA-DERIVED SURFACE HAS NO FLAT ROOT AND NO SECOND SPELLING.**  This module
declares no type of its own: a ``from adcp.types import PaginationRequest`` reaching a
class §1 placed at a domain would be the second path §1 forbids, and the domain in the
import is what tells a reader of application code which document a class came from
without looking it up.

**WHAT IT DOES CARRY IS READING 10's ALIAS LAYER, AND THAT IS AN EXPERIMENT ON THIS
BRANCH** (``adcp-client-python-2m5.6``, measured and not decided).  ``final-state.md``
reading 10 says "``adcp.types`` flat -- the compatibility surface: an alias for every name
an application actually imports today", and the owner's goal calls the layer a DROP-IN for
the v9.6 classes -- which is defined by the import an application has already written.
The aliases are declared at ``adcp.types.compat`` and were reachable from here at none of
their upstream spellings, so ``from adcp.types import <UpstreamName>`` raised.

:func:`__getattr__` is how they are reached, and it is **LAZY by necessity and not by
taste**: an eager ``from adcp.types.compat import *`` here would import every domain
module -- and through them ``adcp.types._schemas`` -- while this package's own body runs,
which is before ``tests/conftest.py`` can put a fresh tree in front of ``__path__``.
Measured: the suite then reports "the generated half of adcp.types is already bound
outside the fresh tree" and grades the committed artifact instead
(``tests/fresh.py::_bound``).  So nothing is imported until a name is asked for, and the
name list is ``adcp.types.compat.__all__`` read at that moment rather than a second copy
of it written here.

**AND IT IS A NAME AND NEVER A SECOND TYPE.**  ``getattr`` over the alias module returns
the object the alias module itself re-exported, so the flat spelling, the alias module's
and the domain module's own are ONE object --
``adcp.types.BrandRef is adcp.types.compat.BrandRef is adcp.types.core.BrandReference`` --
and ``isinstance`` holds across all three spellings.  Nothing is declared here, so reading
6's count of declarations does not move.

**The example is a NAMED triple and not a template, which is the sentence obeying its own
clause**: a path a consumer can type is a claim about the artifact, so only a path that
RESOLVES can be checked, and a ``<placeholder>`` segment is the one spelling no import can
grade (``tests/test_prose_resolves.py``).  ``BrandRef`` is the case worth stating, too --
it is a name upstream spells differently from ours, so the triple shows the flat surface
carrying upstream's word onto our class rather than restating one name three times.

**The re-export is the class, not a copy of it.**  A domain module binds
``from ._schemas... import X as X``, so the object a consumer imports IS the one the
private module built and the one ``strict_validate`` validates into -- ``isinstance``
against a branch imported from here is true, and there is no second ``__adcp_schema__``
to keep in agreement.

**WHAT IS EXPORTED, which §1 fixes and the compiler derives**: every document ROOT, every
union BRANCH and every type ALIAS.  Not every class the tree declares -- an inner shape
stated once by one document is reached through the field whose annotation names it, and a
surface exporting all of them would make ``core.Status`` mean one of fourteen things.  Not
the per-module ``strict_validate`` helper either; a caller reaches one through its class.

**The reading a consumer can re-derive, so none of the above has to be trusted**:
``pkgutil.iter_modules`` over ``adcp.types`` returns the private children ``_base``,
``_runtime`` and ``_schemas``, the two public modules named below, and one module per
domain -- and each domain module's own ``__all__`` is its names as a literal list.  Over
bundle 3.2 that is 23 domains carrying 1,951 names, each resolving at exactly one of them.

**The domain modules are GENERATED from the same walk as the classes**
(``codegen/emit.py``'s ``domain_modules``, from the compiler's own record of what it
exported), so a document added upstream appears in its domain with nothing edited.  **AND
SO IS THIS FILE, WHICH IS WHAT CHANGED ON 2026-11-19** (``codegen/facade.py``): it still
names no type, and the one list it carries -- ``__all__`` -- is written by a generator and
never by hand.

**What it is NOT is part of the EMISSION's byte compare, and that is a fact about the
inputs rather than a gap.**  ``codegen/emit.py``'s own ``domain_modules`` already says a
package's ``__init__`` is the package, so it is bound before ``__path__`` is consulted and
no fresh copy of it could be the one ``tests/fresh.py`` grades.  The stronger reason is
what ``__all__`` is a function of: five of the six layers it unions are ``survey/``'s
output and not the compiler's, so this file's text is a function of the committed package
BESIDE the tree rather than of the bundle -- and ``f(bundle, emitter, compiler)`` is the
whole of what
``tests_emit/test_emit.py::test_the_committed_tree_is_what_a_fresh_run_emits`` ranges over.
``codegen/facade.py``'s own docstring carries that reading and names the layers.

**AND A DOMAIN'S AGGREGATOR IS AT A PATH THE COMPILER OWNS OUTRIGHT, WITH THE PUBLIC PATH
COMPOSING IT IN ONE LINE** (``codegen/emit.py``'s ``SURFACE``, 2026-11-09).  Named at the
one domain the split exists for: what the compiler writes is
``adcp.types._surface.core``, and ``adcp.types.core`` is a short hand-written module whose
whole body is ``from ._surface.core import *`` and that aggregator's own ``__all__``.
Three things decide the split and none of them is taste:

* **A public domain path is also a path upstream kept hand-written machinery at.**
  ``adcp.types.core`` is the one genuine case -- 444 lines of the SDK's own ``TaskResult``,
  ``AgentConfig``, ``Protocol`` and ``TaskStatus``, no bundle document states any of them,
  and they are restored at ``adcp.core``.  The two name sets may share a module
  PATH; they must not share one FILE.
* **The gate is what rules out one file.**  ``emit.write`` is handed a FRESH EMPTY
  directory, so a read-modify-write emitter's output can never equal the committed file,
  and a marked region would force the whole-file byte compare down to a region compare --
  which cannot see a hand edit outside the markers nor a marker moved inward.  Two files
  composed at the import path cost the compare nothing: the aggregator stays 100 % the
  compiler's and is compared byte for byte, and
  ``tests_emit/test_the_public_domain_path.py`` compares the composition's whole text
  against the one it is derived from.
* **The EMITTED half is the eager one, and that is measured.**  Under mypy ``--strict`` a
  star import re-exported through a module reveals the real class even with
  ``--no-implicit-reexport``, where a module-level ``__getattr__`` reveals ``Any``.  The
  surface is 3,221 emitted names against upstream's 21, so the star import carries the
  3,221 and the 21 are written in the ``X as X`` form, which a checker reads the same way.

Nothing about this is visible at the import a consumer writes: ``adcp.types.core.Account``
is still the one path for that class and still the object the runtime validates into --
``adcp.types.core.Account is adcp.types._schemas.core.account.Account``.

Two modules are public and are not domains, because what they hold has no document to
bind -- so neither has a domain a surface could give it, and neither waits on one.

``adcp.types.constraints`` names a constrained type once (D5): a type derived from a
CONSTRAINT belongs to no document.

**AND ONE WORD NAMES ONE SUBJECT, WHICH IS THE CLAUSE §1 LEAVES UNSAID** (the owner's
ruling of 2026-11-18, ``FINDINGS-sixwords.md``).  ``docs/plan/rebuild-plan.md`` §1 forbids
one CLASS reached at two paths and says nothing about one WORD standing for two subjects --
so the rule this namespace needs is its converse: **where two subjects answer to one word,
the SCHEMA subject owns the short flat name and the OpenAPI-derived one is reachable only at
its own module path.**  ``adcp.types.registry`` is that module and the only one behind this
namespace whose classes no bundle document states: it is generated from an OpenAPI spec by
``make regenerate-registry``, so it is VENDORED rather than compiled, and it does not
compete for a word a document's class or the SDK's own ``adcp.core`` already carries.
Measured on bundle 3.2, ten words had two subjects and this facade bound the vendored one at
all ten -- ``adcp.types.Policy`` was a different class from the ``adcp.types.core.Policy``
the protocol documentation names, so ``isinstance`` against the documented class was False.
:func:`_decided` is the screen, and it is said at EVERY layer rather than at one: a fix that
depends on the order the layers are consulted in is undone by the next layer that is added.
``adcp.types.registry.<word>`` still resolves, which is what makes the screen a loss of a
SPELLING and never of a type.

**AND THE SDK'S OWN 21 WORDS ARE ON THIS SURFACE AND ADVERTISED, WHICH IS THE OTHER HALF OF
THAT RULING** (the owner, 2026-11-18, on ``Protocol``): *"it just doesn't belong to types as
that is not a type.  It kinda is, but... not from the emitted surface... or should we just
blend it in?  It kinda belongs there, it is being used, and the fact that the schema doesn't
say it doesn't mean that we shouldn't use the enum in the SDK."*  **Blend it in.**  The line
this turns on is not "does a document state it" but WHOSE OUTPUT it is: ``adcp.types`` may
hold a hand-written type the SDK needs, and what it may not hold is **another generator's
output** -- which is the whole of why ``adcp.types.registry``'s words lose a contested
spelling above and these 21 do not.

:func:`_sdk_words` is the set, DERIVED from ``adcp/types/core.py``'s ``X as X`` block and
never listed: a word is one of these where ``adcp.types.core`` re-exports the very object
``adcp.core`` binds.  Two consequences, and the second is what was open:

* ``Protocol`` resolves flat.  It is ``Enum('Protocol', ['a2a', 'mcp'])``, the TRANSPORT
  selector ``adcp/server/translate.py`` and ``adcp/testing/test_helpers.py`` import, and it
  is neither ``enums/adcp-protocol.json``'s domain enumeration nor ``typing.Protocol``.
  Measured before: 19 of the 21 resolved flat through the generated ``legacy_names`` rows
  and ``Protocol`` -- which that generator does not carry -- raised ``AttributeError`` at
  ``adcp.types.Protocol`` while resolving at ``adcp.core.Protocol`` and
  ``adcp.types.core.Protocol``.  One surface answering two ways.
* they are in ``__all__`` and in ``__dir__``.  They were advertised by NOBODY before, which
  is what made a word served here folklore -- a consumer reading ``__all__``, running
  ``from adcp.types import *`` or pressing tab found no trace of a name the namespace
  answers.  ``FINDINGS-sixwords.md`` recorded the union as open rather than doing it,
  because a blanket union would have advertised ``Protocol``, which then resolved to
  nothing, and ``tests/test_public_words_resolve.py`` grades an advertised word that does
  not resolve as an outage.  Binding it is what makes the advertisement true.

**AND THE 21 WERE ONE SLICE OF IT.  ``__all__`` SAYS WHAT THIS NAMESPACE BINDS, WHICH IS
148 WORDS OVER TWO LATE LAYERS AND WAS SHORT BY 108** (:func:`_advertised_layers`, which
carries the measurement).  ``adcp.types.aliases`` is the bigger half: 127 words, all 127
resolving here, and only 39 advertised.  ``VerifyBrandClaimsPayload`` is the case a test
already named -- that module's short word for
``adcp.types.brand.VerifyBrandClaimsResponseBulkSignedResponsePayload``.  Every word of
both layers is screened by ``getattr`` on this package before it is advertised, so what
``__all__`` offers is what RESOLVES and the two cannot drift apart.

**AND ``__all__`` IS A LITERAL LIST, WRITTEN AT BUILD TIME AND NOT REBUILT ON ACCESS**
(the owner's ruling of 2026-11-19, "generate, don't derive"; ``codegen/facade.py``).  It
was a branch of :func:`__getattr__` that unioned six layers' advertisements on every read,
measured at **4.88 s on the first access and 0.065 s on every one after** -- and the cost
that decided this is neither of those numbers.  **NO STATIC ANALYSER CAN EVALUATE A
``__getattr__`` BRANCH.**  An IDE, a linter, mypy, a doc generator and ``from adcp.types
import *`` resolution all read ``__all__`` expecting a literal; none of them runs the
module.  So the 108 words the paragraph above added to stop this surface being folklore
were bound, were advertised to anything that executed the branch, and were **still
invisible to every reader** -- the computation was widened and nothing became
discoverable.  That is the harm, and a declaration belongs in the module's TEXT.

The union itself did not move and nothing about the SET changed: ``codegen/facade.py``
computes exactly what the branch computed -- the same six layers, the same ``getattr``
screen through :func:`_advertised_layers` -- and writes the answer here as a literal.  So
the derivation is still stated in one place, it is stated once per BUILD rather than once
per access, and the two cannot disagree without a re-emission saying so.  :func:`__getattr__`
stays for what it is for, which is VALUE lookups.

**AND THE SAVING THE FACADE EXISTS FOR SURVIVES, WHICH IS THE OTHER THING THIS COULD HAVE
COST.**  Binding the list realises nothing under it -- neither ``compat`` nor
``_surface._flat`` is in ``sys.modules`` after ``import adcp.types``, and the 1,051
``_schemas`` modules and 381 MiB they pull are still paid at the first VALUE lookup and
nowhere else.  Measured over five runs each: ``import adcp.types`` goes from **0.0050 s and
13.4 MiB peak RSS to 0.0069 s and 14.7 MiB** -- +1.9 ms and +1.35 MiB for 4,358 strings --
and the ``__all__`` access it replaces goes from **4.88 s to 0.000002 s**, which is an
attribute that is simply bound.

**CONSULTED LAST, so a late layer can only ADD a spelling and never change one.**
``TaskStatus`` is the word that proves it: upstream's has five members and ours, from
``enums/task-status.json``, has nine, and ``_flat`` is reached first, so the flat word stays
the DOCUMENT's enumeration and upstream's stays at ``adcp.types.core.TaskStatus``.
Advertising a word changes nothing about which subject it names -- ``__all__`` is a
statement that the spelling resolves.

``adcp.types.envelopes`` carries a base for a repeated envelope the bundle spells
more than one way (``codegen/lower/envelope.py``).  A base there is a type to
PROGRAM AGAINST and not an authority on acceptance: it carries no
``__adcp_schema__``, nothing grades it, and the concrete class for a document -- the
one ``strict_validate`` runs -- is what decides whether a payload is valid.  The
documents of such a family do not agree about that, which is why no single schema
reference could stand for all of them.
"""

#: **EVERY WORD THIS NAMESPACE BINDS, AS A LITERAL** -- this module's own docstring for the
#: ruling, ``codegen/facade.py`` for the generator.  Six layers bind a flat word here and
#: the generator unions their advertisements at BUILD time: ``compat.__all__``,
#: ``compat.__adcp_flat_only__``, ``_adapter.__all__``, ``_restored.__all__``,
#: ``_surface._flat.__all__``, and :func:`_advertised_layers` for the two late ones.  It is
#: written out rather than computed on access because a ``__getattr__`` branch is invisible
#: to every reader that does not run the module, which is the whole of why this list exists
#: in text.
__ALL__


def __getattr__(name: str) -> object:
    """Reading 10's flat compatibility surface, resolved through the alias module.

    A name this package does not itself bind is looked for in ``adcp.types.compat``, the
    one module ``adcp-client-python-2m5.2`` declares every alias at.  What is returned is
    whatever that module holds, which is whatever the domain module holds, which is the
    class the walk emitted -- three spellings, one object.

    **AND THE FLAT SURFACE IS LARGER THAN THAT MODULE'S ``__all__``, which is reading 10's
    amendment of 2026-11-06**: "'already resolves' is measured at the SPELLING A CONSUMER
    WRITES, never at the module that declares it ... a name counted present because its
    domain path matches owes a flat alias exactly as a relocated one does."  So a name the
    alias module declines to bind -- because ours already carries it at
    its own DOMAIN module under upstream's own word -- is resolved HERE through
    ``compat.__adcp_flat_only__``, which names that module.  It gains the one path a
    consumer writes and no path at ``compat``.

    ``AttributeError`` for anything the alias layer does not decide, because that is what
    ``from adcp.types import X`` must raise for a name with no subject: reading 10's "a
    name with no schema subject gets a migration note and never a class", and an
    ``ImportError`` a reader can act on rather than a class that silently is not theirs.
    """
    if name in _NOT_ROUTED or name.startswith("__"):
        # Not routed through the alias module.  A dunder probe (``__path__`` during a
        # partial import, ``__wrapped__``, ``__bases__``) must stay an ``AttributeError``
        # and must not import a thousand names to answer one -- and ``compat`` itself must
        # stay one so that the import system goes on to import the SUBMODULE.
        #
        # **AND ``__all__`` IS NO LONGER THE EXCEPTION TO THIS LINE**, which is the ruling
        # of 2026-11-19 arriving here: it is a literal above, so the attribute is BOUND and
        # this function is never asked for it.  What stood here was a branch that rebuilt
        # the union of six layers per access -- 4.88 s cold, 0.065 s warm -- and what the
        # ruling turns on is that no static analyser can evaluate a branch at all.  The
        # union is ``codegen/facade.py``'s now, read once per build.
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    compat = _alias_module()
    adapter = _adapter_module()
    # **AND UPSTREAM'S OWN STATEMENT IS ASKED BEFORE THE TABLE, WHICH IS THE ONE PLACE THE
    # ORDER BELOW IS NOT PRECEDENCE** (`adcp-client-python-y34k`).  Where upstream's own
    # `_eager.py` binds a flat word to one of the RESTORED files, that word denotes their
    # declaration and not the document's class the alias table binds -- two subjects behind
    # one word, both right about different questions, and a lookup that simply consulted the
    # table first answered the flat one wrongly.
    #
    # **AND IT NOW DECIDES NOTHING, which is measured** (`adcp-client-python-2f52`).  y34k's
    # whole subject was `canonical_creative` -- `Format = _canonical_creative.Format`, 25
    # bindings over 14 words, 262 of upstream's remaining `ValidationError` tests -- and that
    # file is deleted, so `STATED` derives to 8 words of which exactly one (`SchemaVariant`)
    # is bound by a layer below at all, and that one is bound to the same object.  The clause
    # stays because `STATED`'s membership is DERIVED: a thirteenth module restored, or
    # upstream moving a word into one of the twelve, puts a deciding word back with nothing
    # edited here.  `adcp.types._restored`'s own docstring carries the measurement.
    #
    # So a word upstream's own chain terminates in a RESTORED module is answered from that
    # module here, ahead of the four layers below, and precedence decides every word upstream
    # says nothing about -- `adcp.types._restored.STATED`, derived from upstream's own
    # statements by `survey/upstream_aliases.flat_statements` and held in both directions.
    #
    # It costs no import to ASK: `_restored`'s body binds `STATED` and imports nothing but
    # `importlib` and `types`, so a word upstream does not state pays a dict lookup and goes
    # on to the table exactly as before.
    restored = _restored_module()
    if name in restored.STATED:
        return _decided(name, getattr(restored, name))
    try:
        found = getattr(compat, name)
    except AttributeError:
        pass
    else:
        return _decided(name, found)
    where = compat.__adcp_flat_only__.get(name)
    if where is not None:
        import importlib

        return _decided(name, getattr(importlib.import_module(where), name))
    # **AND THE FLAT SURFACE OWES WHAT UPSTREAM'S OWN MACHINERY IMPORTS FROM IT, which the
    # alias table could not see**: `survey/alias_surface.py` ranges over upstream's public
    # type surface, and 171 of the pairs upstream's kept code writes at module scope are
    # flat names it does not reach -- their generator's union-branch disambiguations, the
    # inner nodes of a document, a union they flattened.  `_adapter` is
    # `survey/adapter_surface.py`'s output for those, keyed on the DOCUMENT and the word the
    # document gives, and it is consulted after the table so no name the table decided can
    # be overridden here.
    try:
        found = getattr(adapter, name)
    except AttributeError:
        pass
    else:
        return _decided(name, found)
    # **AND THE FLAT SURFACE OWES WHAT UPSTREAM'S RESTORED MACHINERY DECLARES, which no
    # table over the bundle could reach**: ``adcp.types._restored`` is the flat spelling of
    # the names upstream's own hand-written files declare -- ``MEDIA_BUY_LEGACY_STATUS_VALUES``
    # is the measured case, a ``frozenset`` upstream derives by SUBTRACTION from the
    # lifecycle enumeration and no document states.  Upstream serves these from their own
    # ``_eager``, which is not restorable here -- 16 imports of the generated aggregator
    # this branch deleted -- so the module names the restored MODULES and derives the names
    # from each one's own ``__all__`` or declarations.  CONSULTED HERE for every word
    # upstream states nothing about, so nothing the alias table or the adapter decided is
    # overridden -- and ABOVE, before the table, for the words upstream's own ``_eager``
    # binds to one of these files.  Two questions, asked in the order the ruling gives them.
    try:
        found = getattr(restored, name)
    except AttributeError:
        pass
    else:
        return _decided(name, found)
    # **AND THE FLAT SURFACE OWES EVERY WORD THIS COMPILER ITSELF EMITTED, which is the
    # layer that was deleted and not replaced** (``adcp-client-python-qpo4``, 2026-11-09).
    # ``adcp.types._surface._flat`` is ``codegen/emit.py``'s CROSS-DOMAIN consolidation --
    # the union of the 23 per-domain aggregators, emitted from the same ``Emitted.surface``
    # record they are and compared byte for byte like them.  Without it a name our own walk
    # exported raised here unless some table happened to mention it: measured on bundle
    # 3.2, the aggregators publish 3,220 words and the four layers above served 1,183.
    #
    # CONSULTED LAST, after the table, the adapter and the restored modules, so nothing any
    # of them decided is overridden -- an upstream spelling the alias table points at one
    # class keeps that class even where our walk emits the same word elsewhere.  And it is
    # the one layer that can be reached WITHOUT a table, which is why it is also the one
    # that must not be reached first.
    #
    # **A word two domains publish is NOT here**, and that is the module declining rather
    # than this line choosing: ``_flat.__adcp_ambiguous__`` names it and its domains, and
    # the error below -- which says the generated surface is ``adcp.types.<domain>`` -- is
    # the true answer for a word whose document the caller has not named.
    try:
        found = getattr(_flat_module(), name)
    except AttributeError:
        pass
    else:
        return _decided(name, found)
    # **AND LAST, UPSTREAM'S PUBLISHED WORD FOR A CLASS OUR WALK NAMES DIFFERENTLY.**
    # ``adcp.types.legacy_names`` is ``survey/emit_legacy_names.py``'s output: upstream's
    # 9.6.1 wheel published a word, our compiler names the same subject from its document and
    # arrives at another, and the module binds theirs to ours. Every row is resolved by the
    # pointer both sides carry, else the field-and-required signature, else the probe in
    # ``survey/name-decisions-9.6.1.json`` -- never by spelling.
    #
    # CONSULTED LAST, after every layer above, so no name any of them decided is overridden.
    # It declares no class and changes no accepted set: an alias is a second spelling of one
    # object, which is why it can be reached last and still be correct.
    try:
        found = getattr(_legacy_names_module(), name)
    except AttributeError:
        pass
    else:
        return _decided(name, found)
    # **AND AFTER ALL OF THEM, UPSTREAM'S OWN MODULE PATH, BECAUSE A WORD BOUND THERE AND
    # NOT HERE IS THE SAME SURFACE ANSWERING TWO WAYS.**  ``adcp.types.aliases`` exists at
    # upstream's path so their kept machinery's module-scope ``from adcp.types.aliases
    # import <Name>`` resolves, and the words it binds are decided by the pointer their
    # subject carries.  It was not in this chain, so 23 of them resolved at ``adcp`` and at
    # ``adcp.types.aliases`` and RAISED at ``adcp.types`` -- and the one place that bit was
    # a FUNCTION-scope ``from adcp.types import SyncCreativeResult`` in
    # ``adcp/server/_creative_batch.py``, which no import and no collection error can show
    # you because it waits for a caller.  One layer closes the class of it rather than the
    # two instances.
    #
    # **CONSULTED LAST, AND THAT IS WHAT MAKES IT SAFE RATHER THAN TIDY.**  Measured over
    # the module's 127 words against the chain above: 103 already resolve here to the SAME
    # object, 23 resolve nowhere and are what this line adds, and exactly ONE --
    # ``AuthorizedAgent`` -- resolves here to a different subject, ``adcp.types.registry``'s
    # restored model that ``legacy_names`` binds flat.  Reached last, that word keeps the
    # class it already had: a public word changing meaning while staying importable is the
    # outcome ``docs/plan/rebuild-plan.md`` §4 calls the worst available, and a layer that
    # can only ADD a spelling cannot cause it.  (``adcp``'s own ``AuthorizedAgent`` is the
    # union, which is upstream's binding for the flat word; the two subjects under one word
    # are recorded in ``FINDINGS-rootnames.md`` as a question for the owner.)
    #
    # It is NOT in ``_NOT_ROUTED``: asking for the attribute ``aliases`` reaches this line,
    # finds no ``aliases`` attribute ON the aliases module, and falls through to the
    # submodule import below, which is where that name has always been answered.
    try:
        found = getattr(_alias_path_module(), name)
    except AttributeError:
        pass
    else:
        return _decided(name, found)
    # **AND THE SDK'S OWN HAND-WRITTEN WORDS, WHICH NO GENERATOR CAN REACH AND WHICH THE
    # ONE THAT DID REACHED BY ACCIDENT** (the owner's ruling of 2026-11-18, this module's
    # own docstring).  ``adcp.core`` is upstream's 444 lines of SDK types, re-exported at
    # the ``core`` domain path in the ``X as X`` form and deliberately out of that module's
    # ``__all__`` -- which is the COMPILER's export set and no place for a name with no
    # document.  So nothing above was asking this namespace's own question, and the 19 that
    # resolved did so because ``survey/emit_legacy_names.py`` happened to emit a row for
    # each: ``Protocol``, which it does not carry, resolved at ``adcp.core`` and at
    # ``adcp.types.core`` and raised here.
    #
    # CONSULTED LAST, after every layer above, for the reason the aliases consult is: it can
    # only ADD a spelling, so ``TaskStatus`` keeps the DOCUMENT's nine-member enumeration
    # that ``_flat`` answered with and upstream's five-member one stays at
    # ``adcp.types.core.TaskStatus``.  A word changing subject is what §4 calls the worst
    # available outcome, and a layer reached last cannot cause one.
    # Membership and not ``.get() is not None``: one of the 21 is DATA
    # (``DEFAULT_MAX_RESPONSE_BYTES``, an ``int``), and a lookup that reads a value to decide
    # whether a word is bound answers wrongly for whichever datum is falsy next.
    sdk = _sdk_words()
    if name in sdk:
        return _decided(name, sdk[name])

    # **AND A SUBMODULE OF OURS IS THE IMPORT SYSTEM'S OWN THIRD STEP, which a lazy facade
    # is the one kind of package that has to perform for itself.**  ``from M import N``
    # imports ``M``, takes ``N`` as an attribute, and FAILING THAT imports the submodule
    # ``M.N``.  On an ordinary package the third step is reached because the first two
    # raise; here :func:`__getattr__` answers in their place, so an unqualified
    # ``adcp.types.aliases`` raised although ``import adcp.types.aliases`` resolves -- the
    # module is on disk and nothing but this function stood between them.  Measured: it is
    # what fails ``test_canonical_creatives_rc3.py`` one line ABOVE the three assertions
    # that grade the ``Format`` binding, so the fix those assertions exist for was landing
    # ungraded.
    #
    # ``_NOT_ROUTED`` is excluded and keeps its own reason: those three decline so the
    # import system goes on to import them, and answering here would re-enter this function
    # through the fromlist ``hasattr`` and recurse until the stack ends.
    if not name.startswith("_") and name not in _NOT_ROUTED:
        import importlib

        try:
            return importlib.import_module(f"{__name__}.{name}")
        except ImportError:
            pass

    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}; the generated surface is "
        f"adcp.types.<domain> and the upstream spellings are this namespace's -- see "
        f"docs/migration-from-upstream.md for a name with no document behind it"
    )


#: The one module behind this namespace whose classes no bundle document states:
#: ``adcp.types.registry`` is generated from an OPENAPI spec by ``make regenerate-registry``,
#: which is why it is VENDORED rather than compiled and why the owner's ruling of 2026-11-18
#: keeps it out of the competition for a short word.  Written as the module a class was
#: DEFINED in and never as the layer that handed the class over: ``registry`` itself imports
#: ``RegistryBaseModel`` from ``adcp.types.base``, so the word that reaches this namespace
#: through ``registry`` is not thereby the vendored module's subject.
_VENDORED = f"{__name__}.registry"


def _decided(name: str, value: object) -> object:
    """``value``, unless it is the VENDORED module's class for a word a DOMAIN path owns.

    **ONE WORD, ONE SUBJECT, AND THE SCHEMA'S OWNS IT** -- the owner's ruling of 2026-11-18,
    stated in full in this module's own docstring and measured in ``FINDINGS-sixwords.md``.
    Where ``adcp.types.registry`` and a document's class (or the SDK's own ``adcp.core``,
    re-exported at the ``core`` domain path) answer to one word, the flat spelling is the
    schema subject's and the vendored class keeps ``adcp.types.registry.<word>``.

    **SAID AT EVERY LAYER AND NOT AT ONE, WHICH IS WHY IT IS NOT AN ORDERING.**  The ten
    contested words entered this namespace at TWO layers -- ``adcp.types._restored`` offers
    150 of ``registry``'s words, and the generated ``adcp.types.legacy_names`` binds 148 of
    them -- so moving one consult ahead of another fixed three words and left seven, and a
    later layer would have re-opened whichever three it fixed.  Screening what a layer
    ANSWERS covers every layer that exists and every one that is added.

    It costs nothing for a word nothing vendored answers: the first line is a ``__module__``
    comparison, and :func:`_domain_subjects` is reached only for a word this module is about
    to answer with the vendored module's own class.
    """
    if getattr(value, "__module__", None) != _VENDORED:
        return value
    owned = _domain_subjects((name,)).get(name)
    return value if owned is None else owned


def _domain_paths() -> tuple[str, ...]:
    """The DOMAIN names, read off the compiler's own ``_surface`` package.

    Derived and never listed: a domain added upstream is a directory the compiler writes, and
    the public path for it is ``adcp.types.<domain>`` (this module's own docstring).  The
    private children of that package -- ``_flat`` above all -- are excluded by their leading
    underscore.

    **ITS ABSENCE IS NOT AN ERROR ON THIS PACKAGE**, for :func:`_flat_module`'s reason: a tree
    that has not run the compiler must still import, and the degradation that is correct is
    "no word has a domain owner", which leaves every flat answer exactly as it was.
    """
    import importlib
    import pkgutil

    try:
        surface = importlib.import_module(f"{__name__}._surface")
    except ModuleNotFoundError:
        return ()
    return tuple(
        sorted(
            found.name
            for found in pkgutil.iter_modules(surface.__path__)
            if not found.name.startswith("_")
        )
    )


def _domain_subjects(names: tuple[str, ...]) -> dict[str, object]:
    """The subject a DOMAIN path gives each of ``names``, by word, where one does.

    §1's one import path for a document's class is its domain module, so that is where the
    question "does another subject already carry this word" is asked.  Two readings, because
    a domain module publishes in two ways:

    * ``adcp.types._surface._flat.__all__`` is the compiler's own cross-domain consolidation
      of what the 23 domains ADVERTISE -- the fast and total answer for an emitted word, and
      the one that already declines a word two domains publish (``__adcp_ambiguous__``);
    * a domain module's own namespace, for a word it re-exports WITHOUT advertising.  The one
      measured case is the ``core`` domain: upstream's 444 lines of hand-written SDK types are
      restored at ``adcp.core`` and re-exported at ``adcp.types.core`` in the ``X as X`` form,
      and deliberately not in its ``__all__`` -- which is the compiler's export set and no
      place for a name with no document (``adcp/types/core.py``).  Seven of the ten contested
      words are that case, so a reading of ``_flat`` alone would have answered three.

    **AND IT NEVER RE-DECIDES AN AMBIGUITY.**  A word two domain paths bind to DIFFERENT
    objects is dropped rather than resolved by scan order -- ``_flat.__adcp_ambiguous__``
    declines such a word on purpose and "the first domain this loop reached" is not a subject.
    The vendored answer then stands, which is the only outcome that adds no new binding.
    """
    import importlib

    owned: dict[str, object] = {}
    flat = _flat_module()
    advertised = set(flat.__all__)
    for name in names:
        if name not in advertised:
            continue
        value = getattr(flat, name, None)
        if value is not None and getattr(value, "__module__", None) != _VENDORED:
            owned[name] = value
    wanted = tuple(name for name in names if name not in owned)
    if not wanted:
        return owned
    contested: set[str] = set()
    for domain in _domain_paths():
        try:
            held = importlib.import_module(f"{__name__}.{domain}")
        except ImportError:
            continue
        for name in wanted:
            value = getattr(held, name, None)
            if value is None or getattr(value, "__module__", None) == _VENDORED:
                continue
            if owned.setdefault(name, value) is not value:
                contested.add(name)
    for name in contested:
        del owned[name]
    return owned


def _advertised_layers() -> tuple[str, ...]:
    """The words two LATE layers bind that the four module advertisements do not carry.

    **CALLED BY THE GENERATOR AND NOT BY AN ACCESS, since 2026-11-19.**  ``__all__`` is a
    literal above, so nothing at runtime unions anything: ``codegen/facade.py`` calls this
    function once per build, together with the four module ``__all__``s, and writes the
    union out.  It stays HERE because the screen below is a fact about what THIS namespace
    resolves -- the chain that decides it is :func:`__getattr__`, three functions down --
    and a copy of it in the generator would be a second reading of this module's own
    answer.  So the generator asks and this module answers, which is the arrangement every
    other layer of the surface already has.

    **``__all__`` SHOULD SAY WHAT THIS NAMESPACE BINDS, AND IT WAS SHORT BY 108 WORDS.**
    The union ``codegen/facade.py`` writes is four module advertisements -- ``compat``, its
    ``__adcp_flat_only__``, ``_adapter`` and ``_restored``, plus the compiler's own
    ``_flat`` -- and :func:`__getattr__` consults three more layers after them.  Every word
    those three bind resolved at
    ``from adcp.types import X`` and NONE of them reached ``from adcp.types import *``,
    ``dir()``, tab completion or a doc generator.  Measured before this change:

    | layer | words | resolve | advertised |
    |---|---|---|---|
    | ``adcp.types.aliases`` | 127 | 127 | 39 |
    | ``adcp.core``, via :func:`_sdk_words` | 21 | 20 | 1 |

    -- so 108 words of the 148 were bound and undiscoverable, which is what makes a public
    surface folklore: the one spelling a consumer can find is the one they already knew to
    type.  ``VerifyBrandClaimsPayload`` is the measured case, ``aliases``' short word for
    ``adcp.types.brand.VerifyBrandClaimsResponseBulkSignedResponsePayload``, which
    ``tests/test_adcp_31_rc4_surface.py::test_rc4_symbols_are_publicly_exported`` asserts
    is advertised and which reddened on exactly that.

    **AND A BLANKET UNION WAS REFUSED ONCE FOR A REASON THAT HAD TO BE RE-MEASURED, NOT
    ASSUMED.**  ``FINDINGS-sixwords.md`` left this open because unioning would advertise
    ``Protocol``, which resolved to nothing, and ``tests/test_public_words_resolve.py``
    grades an advertised word that does not resolve as an outage -- a name in ``__all__``
    that raises is worse than one that is merely undiscoverable.  So every word of both
    layers was offered to ``getattr`` before being advertised: of the 148, **147 resolved
    and exactly one did not, ``Protocol``**, which this same change binds
    (:func:`_sdk_words`).  There is no second such name.  ``aliases.__adcp_refused__`` is
    ``{}``, so that module declines nothing today, and a word it starts declining leaves
    this union by the same ``getattr`` below rather than by an edit here.

    **``legacy_names`` IS A THIRD SLICE AND IS DELIBERATELY NOT HERE.**  It binds 3,520
    words of which 1,726 are unadvertised -- 16 times this change -- and it is
    ``survey/emit_legacy_names.py``'s GENERATED output, whose rows
    ``FINDINGS-sixwords.md`` open question 3 already records as decided by a rule the
    owner's ruling overrode.  Advertising 1,726 generated spellings is a surface decision
    of its own size and is not this job's to take.  Measured and named so it is not
    rediscovered.

    Each word is screened by ``getattr`` on this package, so what is advertised is what
    RESOLVES -- the two can no longer disagree, whichever layer answers.  Through
    ``sys.modules`` and never ``globals()``: the screen has to go through
    :func:`__getattr__`, which is the chain that decides whether a word resolves, and a
    lookup in this module's own namespace would answer for the handful of names bound here
    and ``AttributeError`` for every word a layer serves.
    """
    import importlib
    import sys

    offered = list(_sdk_words())
    try:
        aliases = importlib.import_module(f"{__name__}.aliases")
    except ModuleNotFoundError:  # pragma: no cover -- a tree without the alias layer
        pass
    else:
        offered.extend(getattr(aliases, "__all__", ()))
    here = sys.modules[__name__]
    out: list[str] = []
    for name in dict.fromkeys(offered):
        try:
            getattr(here, name)
        except AttributeError:
            continue
        out.append(name)
    return tuple(out)


def _sdk_words() -> dict[str, object]:
    """The SDK's OWN hand-written words this namespace serves, by word.

    **DERIVED FROM ``adcp/types/core.py``'s ``X as X`` BLOCK AND NEVER LISTED.**  A word is
    one of these where ``adcp.types.core`` re-exports the very object ``adcp.core`` binds --
    identity and not spelling, which is what makes the set exactly the re-export block and
    what makes a word that moves out of ``adcp.core`` leave this surface with nothing edited
    here.  Measured on this tree: **21** words, of ``adcp.core``'s 36 public names.  The 15
    it leaves are not SDK surface and the predicate says so without naming them -- ``Enum``,
    ``BaseModel``, ``Field`` and the rest are imports the module needs, ``T`` is its
    ``TypeVar``, and ``validate_max_response_bytes`` is ``adcp._response_limit``'s and is not
    re-exported at the domain path.

    **IDENTITY ALSO DECIDES THE ONE CONTESTED WORD WITHOUT A CLAUSE FOR IT.**  ``adcp/types/
    core.py`` ends with ``from ._surface.core import *``, so a word the compiler emits into
    the ``core`` domain SHADOWS the re-export above it, the identity against ``adcp.core``
    fails, and the word is not offered here.  None does today; the reading is why no list of
    exclusions is needed when one does.

    Reached only on a miss, and it costs no import the chain has not already paid:
    :func:`_alias_module` imports all 23 domain aggregators at the top of
    :func:`__getattr__`, and :func:`_domain_subjects` imports each public domain module
    including this one.
    """
    import importlib

    core = importlib.import_module(f"{__name__}.core")
    sdk = importlib.import_module("adcp.core")
    held = vars(sdk)
    return {
        name: value
        for name, value in vars(core).items()
        if not name.startswith("_") and name in held and held[name] is value
    }


def _alias_module():
    """``adcp.types.compat``, reached WITHOUT a ``getattr`` on this package.

    ``from adcp.types import compat`` would not do: the import system answers a fromlist
    entry by asking ``hasattr`` on the parent first, which re-enters
    :func:`__getattr__` and recurses until the stack ends.  ``import_module`` returns the
    entry in ``sys.modules`` and never consults this package's attributes.
    """
    import importlib

    return importlib.import_module("adcp.types.compat")


#: The submodules :func:`__getattr__` must NOT answer, so the import system goes on to
#: import them.  All three are compatibility layers of this package and each is reached by
#: ``import_module`` below rather than by an attribute.
_NOT_ROUTED = ("compat", "_adapter", "_restored", "legacy_names")


def _alias_path_module():
    """``adcp.types.aliases``, reached by ``import_module`` like every other layer.

    Upstream's own module path, served from our surface.  ``import_module`` and never
    ``from adcp.types import aliases``, for :func:`_alias_module`'s measured reason: the
    import system answers a fromlist entry by asking ``hasattr`` on the parent first, which
    re-enters :func:`__getattr__` and recurses until the stack ends.
    """
    import importlib

    return importlib.import_module("adcp.types.aliases")


def _legacy_names_module():
    """``adcp.types.legacy_names``, reached lazily like every other layer of the facade.

    Imported on first miss rather than at module scope, for :func:`_restored_module`'s reason:
    ``import adcp.types`` stays cheap, and a word served by any layer above never pays for
    this one.
    """
    import importlib

    return importlib.import_module("adcp.types.legacy_names")


def _restored_module():
    """``adcp.types._restored``, reached the same way and for the same reason.

    The flat spelling of what upstream's own restored files declare.  Imported on the FIRST
    attribute miss and never while this package's body runs: the module's own body binds
    ``MODULES`` and ``STATED`` and imports nothing but ``importlib`` and ``types``, so
    asking whether upstream states a word costs a dict lookup, and the thirteen restored
    files are imported only when one of them ANSWERS -- at the moment a name is asked for
    rather than at this package's own import, which is what keeps ``tests/fresh.py``'s
    binding ahead of it.
    """
    import importlib

    return importlib.import_module("adcp.types._restored")


def _flat_module():
    """``adcp.types._surface._flat``, reached the same way and for the same reason.

    The compiler's own cross-domain consolidation of the per-domain aggregators.  Imported
    on a MISS of all four layers above and **never while this package's body runs**, which
    is the whole of why the facade can carry 3,220 names at no import cost: this module
    DOES pull the generated graph -- it names every word the walk exported, so importing it
    imports all 23 aggregators and through them ``adcp.types._schemas`` -- and the
    emitted tree holds 146 ``model_rebuild(force=True)`` calls that cost nothing only
    because nothing is built until a name is asked for (CLAUDE.md #1694).

    So the import is on the attribute and not on the package, exactly as
    :func:`_restored_module`'s is, and for the stronger version of the same reason:
    ``tests/fresh.py`` grades a fresh tree by putting its directory in front of
    ``adcp.types.__path__``, and a star import here would bind the COMMITTED tree's
    classes while this package's body ran -- before ``tests/conftest.py`` could put the
    fresh one there.  Measured before the facade was lazy: the suite reports "the generated
    half of adcp.types is already bound outside the fresh tree" and grades the artifact.

    **ITS ABSENCE IS NOT AN ERROR ON THIS PACKAGE**, for :func:`_adapter_module`'s reason:
    it is generated, and a tree that has not run the compiler must still import.  The
    degradation that is correct is "no extra flat name", never "``adcp.types`` raises".
    """
    import importlib
    import types as _types

    try:
        return importlib.import_module("adcp.types._surface._flat")
    except ModuleNotFoundError as absent:
        # **ONLY THIS MODULE'S OWN ABSENCE IS TOLERATED, AND THE NAME IS WHAT SAYS SO.**
        # ``ModuleNotFoundError`` is raised BOTH when ``_flat`` is absent and when something
        # ``_flat`` itself imports is absent, so a bare ``except`` here answers a broken
        # inner import with ``__all__ = []`` -- the whole flat surface degraded to nothing,
        # with no error anywhere. Measured: a wrong relative prefix inside ``_flat`` silently
        # took all 738 upstream-word bindings and the 3,699-name surface with it, and it was
        # found by reading this clause rather than by any failure
        # (``adcp-client-python-3wbx``).
        #
        # ``absent.name`` is the module the import system could not find. Where that is not
        # the one this shim stands in for, the failure is real and belongs to the caller.
        if absent.name not in ("adcp.types._surface._flat", "adcp.types._surface"):
            raise
        shim = _types.ModuleType("adcp.types._surface._flat")
        shim.__all__ = []
        shim.__adcp_ambiguous__ = {}
        return shim


def _adapter_module():
    """``adcp.types._adapter``, reached the same way and for the same reason.

    **AND ITS ABSENCE IS NOT AN ERROR ON THIS PACKAGE.**  The adapter is generated, from a
    run that has upstream's wheel to measure against; a tree that has emitted its classes
    and not yet generated it must still import, and the degradation that is correct is "no
    extra flat name", never "``adcp.types`` raises".  Measured: without this, the generating
    run's own census cannot resolve a single flat name -- every pair reports
    ``ModuleNotFoundError`` instead of ``AttributeError``, the demand reads EMPTY, and the
    instrument writes an empty adapter over a full one.
    """
    import importlib
    import types as _types

    try:
        return importlib.import_module("adcp.types._adapter")
    except ModuleNotFoundError as absent:
        # The same hole as :func:`_flat_module`'s, for the same reason: this module imports
        # from every domain aggregator, so a missing name there raises
        # ``ModuleNotFoundError`` for THAT module and a bare ``except`` would answer with an
        # empty adapter -- silently dropping every upstream spelling the adapter serves.
        if absent.name != "adcp.types._adapter":
            raise
        shim = _types.ModuleType("adcp.types._adapter")
        shim.__all__ = []
        return shim


def __dir__() -> list[str]:
    """This package's own names plus every word :data:`__all__` advertises.

    **READ OFF ``__all__`` AND NOT RE-DERIVED, WHICH IS THE OTHER HALF OF THE 2026-11-19
    RULING.**  This function used to union the same six layers the ``__all__`` branch of
    :func:`__getattr__` did, from the same modules, in the same shape -- so with one of the
    two written out and the other still computing, the only thing keeping them equal would
    have been that the two expressions happened to stay the same.  A namespace that
    advertises one set to ``dir()`` and another to ``__all__`` is the defect one level up
    from the one that ruling fixes, and it would be silent.  One statement, two readers.

    ``set(globals())`` is the half ``__all__`` does not carry and must not: these are this
    module's OWN names -- the lazy facade's helpers and its dunders -- and they are what
    ``dir()`` owes a reader of this module while ``__all__`` is the compatibility surface's
    export set.  Tab completion wants both; ``from adcp.types import *`` wants only the
    second.
    """
    return sorted(set(globals()) | set(__all__))
'''
