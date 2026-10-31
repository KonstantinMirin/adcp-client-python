"""THE PAIRING: every class and alias the fresh tree carries, with the schema it names.

**ONE WALK, and it is here rather than in ``tests/test_emit.py`` for the reason that file
already gives about two populations**: a reader with a pairing of its own would range over
however many pairs that second walk turned out to find, and the two would disagree
silently the moment either moved.  :func:`pairs` is therefore the suite's only pairing of
the fresh tree -- ``test_emit.graded()`` reads it and wraps each row in its own ``Graded``
-- so "the 2,793 pairs" means one thing in both files.

**What a pairing is FOR.**  The round trip needs to know which emitted class answers which
document and pointer: ``harness.check_pair`` is handed a node, the model that names it,
and the entry point an instance is offered through, and it draws an instance the document
admits, offers it to that class, dumps what the class built and hands the dump back to the
document.  Without the pairing there is no "that class" -- the draw would have a document
and nothing to offer it to.

**The TREE is the one a FRESH run emits**, which ``tests/fresh.py`` both decides and
performs: it writes the emission and binds ``adcp.types``'s generated half to it, so the
import in :func:`pairs` reaches this compiler's output and its aliases resolve through
this compiler's ``constraints`` module.  A fresh ``_schemas`` imported beside the
COMMITTED alias module would resolve its aliases through that one, and an alias this run
mints that the committed module lacks is exactly a defect the pairing is meant to find.

Cached, because the walk imports the whole emitted tree and a union root's
``model_rebuild(force=True)`` is not cheap.
"""

from __future__ import annotations

import functools

from codegen import harness
from codegen.harness import Paired

import fresh

#: The four fields ``tests/test_emit.py``'s ``Graded`` carries, in its order, because that
#: file wraps these rows in it.  **``codegen.harness``'s and not this module's**, because
#: the WALK is the verifier's (``harness.pairs``) and a row type stated twice would be two
#: types one reader has to tell apart.  Re-exported under this name so every reader that
#: already says ``compared.Paired`` still reads the one it always did.
__all__ = ["Paired", "UNIMPORTABLE", "pairs"]


#: Modules of the fresh tree that did not import, as ``name -> the tail of the traceback``.
#:
#: **:func:`pairs` records an unimportable module and does not raise.**  It is read at
#: PARAMETRIZE time by ``tests/test_emit.py``, where a raise is not a red test -- it errors
#: the COLLECTION of that file, and the measurement is that one module which did not import
#: collected ZERO tests there: every pair and the import obligation itself, gone, with
#: the reader left holding a traceback instead of a named failure.
#: ``docs/plan/architecture.md``'s rule for it is "a tree that does not build fails one
#: named test instead of disabling the file", and
#: ``test_emit.test_no_module_of_the_graded_tree_failed_to_import`` is the test that reads
#: this.  It is the SAME dict object that file exposes, so either name reports the same
#: walk.
UNIMPORTABLE: dict[str, str] = {}


@functools.cache
def pairs() -> list[Paired]:
    """Every class and alias the FRESH tree carries, with the schema each one names.

    The whole of the pairing, and the suite's only one.  A class is taken from the module
    that DEFINES it (``__module__``) and ONCE per module whatever names it is bound under
    (by ``id``), because D3's content dedup gives one class a name at every position its
    node occupies -- keyed on names the pair count read 1,085 where 1,079 pairs existed.

    **``SchemaBound`` and not ``AdCPBaseModel`` is the predicate, because §8 of the
    architecture document requires a ROOT MODEL to be paired exactly as a class is**:
    "each must carry ``__adcp_schema__``, ``strict_validate`` and a rule tuple exactly as
    a class does, or a root model and a class disagree about what their document accepts."
    ``SchemaBound`` is the mixin that carries those two, so it is the predicate that says
    "this object is a pair"; ``AdCPBaseModel`` says "this object is a class", which is a
    narrower question and the wrong one here.  Measured at §14 step 9: the six root models
    the step's three producers declare -- ``core/acceptance-policy-profile-ids.json``,
    ``core/forecast-point-dimensions.json``,
    ``core/reporting-verification-profile-set.json``, ``media-buy/product-fields.json``
    and the two ``core/targeting-*-age-*-constraint.json`` -- emitted into the tree and
    reached NO pair, which
    ``test_emit.test_the_pairing_is_intrinsic_to_every_class_the_tree_carries`` reports as
    a document that emits and is not graded.

    An ALIAS is D2's root-scalar row -- not a class, so its MODULE carries
    ``__adcp_schema__`` and ``strict_validate``, and the model is the one name the module
    exports.  ``test_emit``'s own checks assert both cases non-empty, so neither is graded
    by an empty loop.

    **The TREE is the one a FRESH run emits**, which ``tests/fresh.py`` both decides and
    performs: it writes the emission and binds ``adcp.types``'s generated half to it, so
    the import below reaches this compiler's output and its aliases resolve through this
    compiler's ``constraints`` module.  A fresh ``_schemas`` imported beside the COMMITTED
    alias module would resolve its aliases through that one, and an alias this run mints
    that the committed module lacks is exactly a defect the pairing is meant to find.

    **Nothing it reads can take a caller's collection down**: no tree at all is an empty
    list (``fresh.schemas()`` answers ``None`` and a named test reads the reason), and a
    module that does not import is recorded in :data:`UNIMPORTABLE` and skipped.

    Cached because it imports the whole emitted tree and a union root's
    ``model_rebuild(force=True)`` is not cheap.  The returned list is SHARED: read it, do
    not mutate it.

    **THE WALK ITSELF IS ``codegen.harness.pairs`` AND THIS FUNCTION IS WHICH TREE.**  The
    pairing is a reading of an emitted tree, which is the verifier's own business (§9), and
    there are now TWO readers of it: this one, over the fresh tree, and
    ``codegen/__main__.py``, over the tree the run just wrote.  The paragraphs above are
    this module's half of that -- which tree, bound how, and what a caller may do with the
    result -- and they are the half a second walk would have had no opinion about.  Stated
    twice the two walks would disagree the moment either moved, which is the defect the
    first paragraph of this docstring already names.
    """
    found, unimportable = harness.pairs(fresh.schemas())
    #: Updated in place and never rebound, because this dict IS
    #: ``test_emit.UNIMPORTABLE``: that module takes an alias at import time, and a
    #: rebinding here would leave it holding the empty dict for ever.
    UNIMPORTABLE.update(unimportable)
    return found
