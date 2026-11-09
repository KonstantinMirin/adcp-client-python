"""ONE construction over the whole bundle, derived once and read by every check of it.

``codegen/verify/witness.py`` is keyed on ``(document, pointer, stack)`` and holds its memo
on the instance, so two test modules each building their own :class:`Construction` would
pay the walk twice and -- worse -- would report two readings of one number.
``tests/nodeset.py``'s own rule is the one that applies: *"two derivations of one number is
how a verdict comes to disagree with the gate it cites"*.  So the walk happens here, once
per process, and the modules that grade it read :func:`whole`.

**The records are the BUNDLE A RUN READS**, ``tests.fresh.BUNDLE`` -- the published 3.2
bundle with the build's patch sets applied.  A module naming a bundle path of its own is
the defect ``adcp-client-python-lzzj.11`` swept out of 36 files, and the figures here and
the figures ``./check`` reports have to range over one input.
"""

from __future__ import annotations

import functools

from fresh import BUNDLE

from codegen import bundle
from codegen.verify import witness


@functools.cache
def records() -> dict[str, dict]:
    """Every portable document's RECORD: itself with every cross-document ``$ref`` inlined.

    ``codegen.bundle.record`` is the one reading, and ``known`` is passed rather than found
    for the reason that function's own docstring measures: resolving a reference's head
    against the set of documents that exist is a directory scan, and a callee reached once
    per node would perform it once per node.

    A document the record REFUSES is absent, and its absence is graded:
    ``tests/test_witness_construction.py::test_the_construction_ranges_over_every_portable_document``
    reads this set against ``codegen.bundle.portable`` and names the difference.
    """
    documents = sorted(bundle.portable(BUNDLE))
    known = set(documents)
    out = {}
    for document in documents:
        built = bundle.record(BUNDLE, document, known)
        if isinstance(built, dict):
            out[document] = built
    return out


@functools.cache
def whole() -> witness.Construction:
    """The construction, with every node of every record already asked for.

    Warmed on purpose: the counters are the subject of several checks
    (:class:`codegen.verify.witness.Counters`), and a counter read after a partial walk is a
    figure about the order the tests happened to run in.  So the walk is completed here and
    every reader sees the same totals.
    """
    built = witness.Construction(records())
    for document, record in records().items():
        for pointer, _ in bundle.nodes(record):
            built.value(document, pointer)
    return built


@functools.cache
def pointers() -> dict[str, tuple[str, ...]]:
    """Every schema position of every record, by document, in the walk's own order.

    ``codegen.bundle.nodes`` is the one walk and it descends by the table's descent column,
    so the set of nodes this grades is the set of nodes the compiler's own census reads --
    which is what makes "every node has a value or a named reason" a claim about the same
    nodes both halves see.
    """
    return {
        document: tuple(pointer for pointer, _ in bundle.nodes(record))
        for document, record in records().items()
    }
