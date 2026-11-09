"""The COMPATIBILITY MIRROR of the emitted tree, as the text ``emit.write`` puts beside it.

**WHAT IS MIRRORED AND WHY.**  §1 writes a document's module to
``adcp.types._schemas.<domain>.<document>`` and gives each class one public path, the domain
surface.  v9.6 published the generated tree itself at
``adcp.types.domains.<domain>.<document>``, and the machinery this release KEEPS is written
against that layout -- 1,423 module-scope ``(module, name)`` imports from ``adcp.types*``
over ``src/adcp/`` less ``src/adcp/types/``, of which 92 distinct pairs are blocked because
91 modules under ``adcp.types.domains.*`` do not exist.  Module scope is what makes it
fatal rather than inconvenient: one absent module takes the whole importing file and every
name it carried.  :mod:`codegen.mirror.domains` is the answer and carries the reading; this
module is where the answer joins the run.

**IT IS A COMPATIBILITY SURFACE AND NOT A SECOND PUBLIC PATH**, in the sense
``adcp.types.compat`` is one.  ``final-state.md`` reading 6 counts
``adcp.types.<domain>.<Name>`` paths, over a population the gate derives from the
compiler's own export record (``emit.surface``), so the mirror is outside what that gate
ranges over and the gate is not widened to tolerate it.  The mirror declares nothing: a
mirror module IS the private module, bound under a second name.

**WHY THE TEXT IS A VERBATIM FILE AND NOT A TEMPLATE.**  Every other artifact beside the
tree is a function of the run -- the alias module holds the shapes a run resolved, a domain
module holds the names §1's export set holds -- and ``codegen/render.py`` writes each one
from a decided IR.  The mirror is a function of the run only in the sense that it resolves
against whatever tree is there: its mapping is one prefix substitution evaluated at import
time, so **there is no list in it and there is nothing in it to template**.  A rendering
pass over a fixed file would be a layer that decides nothing, and §7's rule that "nothing
before ``render.py`` holds a string of Python" is the same judgement from the other side.
So :data:`SOURCE` is read and copied, which also keeps it real, parseable, reviewable
Python where it is authored rather than a string literal inside a module of the compiler.

**AND IT IS STILL EMITTED, which is the half that matters for staleness.**  ``emit.write``
writes it on every whole-population run, so ``tests_emit/test_emit.py``'s byte-compare of
the committed tree against a fresh run covers it and a hand edit to the shipped file
reddens.  The mirror itself cannot go stale in the way a hand-maintained one would -- a
document added upstream is mirrored with nothing regenerated, because the mapping names no
document.
"""

from __future__ import annotations

from pathlib import Path

#: The mirror package's own name under ``adcp.types``, which is v9.6's own word for it.
PACKAGE = "domains"

#: The artifact, verbatim.  A sibling module of this one, inert where it sits: its
#: self-installation is guarded on a private tree existing beside it, which is false under
#: ``codegen/`` and true under ``adcp/types/`` (``domains.there_is_a_tree_to_mirror``).
SOURCE = Path(__file__).resolve().parent / f"{PACKAGE}.py"


def beside() -> dict[str, str]:
    """The mirror's files, keyed relative to the PACKAGE directory ``emit.write`` is passed.

    One entry: the mirror is a package whose ``__init__`` installs a finder, so a module
    per mirrored document would be a file per document for no answer the finder does not
    already give -- and 1,059 of them that ``emit.write``'s prune does not range over,
    since the prune is bounded to the tree and this sits beside it.

    Keyed relative to the package directory for ``Emitted.beside``'s own reason: no caller
    of :func:`codegen.emit.write` can be handed a path that escapes the directory it
    passed.
    """
    return {f"{PACKAGE}/__init__.py": SOURCE.read_text()}
