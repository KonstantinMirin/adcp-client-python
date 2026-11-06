"""The digest over a bundle's document set, and the record that is compared against it.

``docs/plan/architecture.md``, under "AN OVERRIDE DECLARES THE DEFECT IT COMPENSATES FOR,
AND FAILS WHEN THE DEFECT IS GONE":

    **A BUNDLE GROUNDS US ONLY WHILE ITS UPSTREAM STATE IS RECORDED BESIDE IT** -- the
    upstream commit, the command that built it, and a digest over the document set.  The
    digest is not redundant with the commit: a commit identifier nothing checks is a
    decoration, and the comparison between digest and documents is what turns the record
    from a claim into a fact.

This module is the comparison's one spelling.  ``tests/test_a_bundle_states_which_upstream
_it_is.py`` is the gate that runs it.

**WHY THE RECORD IS NOT INSIDE THE BUNDLE.**  ``codegen.bundle.portable`` enumerates
``bundle.rglob("*.json")``, so a provenance file written under ``schemas/cache/3.2/`` would
be a DOCUMENT -- compiled, graded, and counted among the 1,625.  The record therefore sits
beside the directory as ``schemas/cache/3.2.provenance.json``: inside ``schemas/cache/`` so
it is impossible to miss, outside the walk so it is impossible to confuse with a schema.

**WHY THIS MODULE IS NOT UNDER ``codegen/``, which is where the bundle's other readers are.**
``codegen.store.compiler_digest`` hashes every ``codegen/**/*.py`` -- it is the key the
compile is held under -- so a module added there costs every lane a cold compile, and every
later edit to a provenance record would cost another.  The record's only reader is the gate,
so the cost would buy nothing.  ``codegen/held.py``'s own comment states the neighbouring
rule from the other side -- *"A compiler edit moves no key"* about the accepts corpus -- and
the two together are the shape: a derived artifact's key must move on its INPUT and on
nothing else.

**AND A BYTE DIGEST IS RIGHT HERE AND WAS WRONG THERE, which is the distinction worth
stating because the two look identical.**  ``adcp-client-python-lzzj.8`` measured that keying
the accepts corpus on a document's raw bytes made an acceptance-preserving rewrite of the
bundle cost exactly what a regression cost: 1,054 of 1,054 identities moved on 22,338
differences a validator cannot see, 854 of them a trailing newline.  That is a defect
because the question there is *"does this document admit the same instances?"* -- a question
about MEANING, which bytes over-answer.  The question HERE is *"are these the bytes the 90
approximated facts in 57 documents were measured against?"*, which is a question about
IDENTITY, and for that nothing weaker than bytes is an answer: a reformatting of the bundle
is precisely an event that should redden this gate and ask for a re-measurement, because
``codegen.patch.load``'s refusals are comparisons against these bytes.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]

#: Where the bundles live.  A directory here is a bundle and must have a record.
CACHE = REPO / "schemas" / "cache"

#: The prefix of the ``digest`` field, so the record says which function produced it and a
#: later change of function is a visible edit rather than a silent one.
ALGORITHM = "sha256:"


def bundles() -> list[Path]:
    """Every bundle under :data:`CACHE`, which is every DIRECTORY in it.

    Discovered rather than listed, because a listing is the thing that goes stale: the
    defect this gate exists for is a bundle with no record, and a gate that iterates a
    hard-coded pair of names is green the day a third bundle is copied in.
    """
    return sorted(p for p in CACHE.iterdir() if p.is_dir())


def record_path(bundle: Path) -> Path:
    """The record that stands beside ``bundle``: ``<bundle>.provenance.json``."""
    return bundle.with_name(f"{bundle.name}.provenance.json")


def read(bundle: Path) -> dict[str, Any]:
    """The record beside ``bundle``, parsed.  Raises where there is none."""
    return json.loads(record_path(bundle).read_text())


def files(bundle: Path) -> list[str]:
    """Every regular file under ``bundle``, bundle-relative and POSIX, in digest order.

    **Every FILE and not every ``*.json``.**  The two sets are equal today -- measured on
    both bundles, 1,625 of 1,625 and 1,141 of 1,141 files end in ``.json`` -- and the
    equality is worth grading rather than assuming, because a stray file under a bundle root
    is either a document the walk will compile or a note nobody reads, and the record cannot
    tell which.  Digesting all of them makes the arrival of one a RED rather than a silence.

    Sorted by the path's UTF-8 bytes, which is ``LC_ALL=C sort``'s order and not Python's
    default string order -- the two differ once a path holds a non-ASCII byte, and the point
    of the digest is that a reader with ``find``, ``sort`` and ``sha256sum`` gets the same
    answer as this function.
    """
    return sorted(
        (p.relative_to(bundle).as_posix() for p in bundle.rglob("*") if p.is_file()),
        key=lambda name: name.encode(),
    )


def digest(bundle: Path) -> str:
    """The digest over ``bundle``'s document set, with :data:`ALGORITHM` in front.

    The hashed stream is one line per file -- ``<sha256 hex of its bytes>  <path>\\n`` -- in
    :func:`files` order.  Three properties are deliberate and each answers a way a digest
    like this goes wrong:

    * **The order is stated, not inherited.**  A digest that folded files in the order a
      filesystem walk returned them would answer differently on two machines holding the
      same bytes, which makes a red unreadable.
    * **The path is in the stream beside the content**, so moving a document reddens.  A
      digest over contents alone calls a rename no change, and a renamed document is a
      different bundle to every ``$ref`` that names it.
    * **The two fields cannot bleed into one another.**  ``codegen.patch._patch_set_digest``
      concatenates path and bytes with no delimiter, which is sound for its input and not in
      general: an edit that moves bytes from the end of a name to the start of a body is
      invisible to it.  Here the hex digest is fixed-width and the separator literal.

    The format is ``sha256sum``'s own, so the answer is checkable with no Python at all::

        cd <bundle> && find . -type f | sed 's|^\\./||' | LC_ALL=C sort \\
            | tr '\\n' '\\0' | xargs -0 sha256sum | sha256sum

    which is the property that keeps the record from being a decoration this repository
    alone can read.
    """
    h = hashlib.sha256()
    for name in files(bundle):
        line = f"{hashlib.sha256((bundle / name).read_bytes()).hexdigest()}  {name}\n"
        h.update(line.encode())
    return ALGORITHM + h.hexdigest()
