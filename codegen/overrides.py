"""§3's override discipline applied to the NAME and the DOMAIN rather than to the node.

``docs/plan/architecture.md`` §3: **"AN OVERRIDE DECLARES THE DEFECT IT COMPENSATES FOR,
AND FAILS WHEN THE DEFECT IS GONE."**  ``codegen/patch.py`` is that mechanism for a schema
overlay -- a table of node edits, each stating what upstream gets wrong and each refusing
to load once upstream has fixed it.  This is the same mechanism one layer over: the name a
class is emitted under, and the domain it is emitted into, keyed on ``(document,
pointer)``.

**WHY IT HAS TO EXIST AT ALL, which is a statement about the DOCUMENTS and not about our
taste.**  §4 derives a class's name from the document's own ``title``, and that is right
almost everywhere.  It is wrong exactly where the documents give one word to two subjects
and the one that needs it is not the one titled with it.  There is no reading of §4 that
repairs that, because §4's input is the title and the title is what is wrong -- so the
repair is a declared exception that cites the document, not a cleverer rule.

**TWO PROPERTIES KEEP IT FROM BECOMING A FORK, and both are asserted by
``tests_emit/test_the_name_override_table.py`` rather than reviewed:**

1. **THE REASON IS A QUOTATION.**  :attr:`Override.defect` must be a substring of the
   document's own ``title`` or ``description``.  An entry whose reason is not the
   document's own words is REFUSED at load (:func:`load`), because a table that admits
   taste drifts into taste and there is no later point at which that is caught.
2. **EVERY ENTRY READS AS A DIFF.**  :func:`rows` renders the name §4 WOULD have derived
   beside the name the entry gives and the quotation that justifies it, in one row. An
   override nobody can read against its alternative is a fork with a reason attached.

**AND IT FAILS WHEN THE DEFECT IS GONE.**  The quotation is checked against the live
bundle, so the day upstream rewrites the description the entry cites, the build breaks and
names the entry.  That is the whole of what makes this an override rather than a rename:
it cannot outlive the thing it compensates for.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class OverrideRefused(Exception):
    """An entry whose reason is not the document's own words, or whose document moved."""


@dataclass(frozen=True)
class Override:
    """One entry: where it applies, what it gives, and the document's own words for why.

    ``pointer`` is spelled as the document writes it -- ``#`` for a root -- which is
    ``adcp.types._base.SchemaRef``'s spelling and the one a reader of a verdict table
    already knows.

    ``domain`` is the package the class is emitted into, and it is stated even when it is
    unchanged: an entry that silently kept a domain would make the table's answer depend
    on which fields it omits.
    """

    document: str
    pointer: str
    name: str
    domain: str
    #: The document's own words, VERBATIM, that establish the defect.  Checked against the
    #: live bundle at load: not a label, not a paraphrase, not a justification of ours.
    defect: str
    #: What the entry is for, in our words.  Never the authority -- :attr:`defect` is.
    because: str


#: **THE TABLE.  One entry, and the case that forced it.**
#:
#: ``core/format.json`` is titled "Format" and its own description calls it a *"Legacy
#: named-format definition"* in the same breath as *"DEPRECATED in 3.2."* and *"New
#: products and creative agents author ProductFormatDeclaration canonical contracts
#: instead"*.  So the deprecated v1 definition holds the word the canonical declaration
#: needs, and the document names itself.  ``CLAUDE.md``'s format section carries the
#: measurements and the decision; neither is re-derived here.
#:
#: The word this frees is served by the ALIAS layer and never by a class name:
#: ``Format`` -> ``ProductFormatDeclaration``.  That document is titled "Product Format
#: Declaration", §4 forbids minting a public name no document states, and upstream's own
#: public ``Format`` already means that subject.
OVERRIDES: tuple[Override, ...] = (
    Override(
        document="core/format.json",
        pointer="#",
        name="LegacyFormat",
        domain="core",
        defect="Legacy named-format definition",
        because=(
            "the document's title is 'Format', so §4 derives Format for the DEPRECATED v1 "
            "named-format definition -- and the canonical declaration that needs the word "
            "is titled 'Product Format Declaration'. The document names itself in its own "
            "description, so the override takes the document's word for its own subject."
        ),
    ),
)


def _words(bundle_dir: Path, document: str) -> tuple[str, str]:
    """The document's own ``title`` and ``description``, read from the bundle.

    Read off the RAW document and not off a record: the words an entry quotes are the
    words upstream wrote, and a record is our rendering of them.
    """
    try:
        held = json.loads((Path(bundle_dir) / document).read_text())
    except (OSError, ValueError) as e:
        raise OverrideRefused(f"{document} cannot be read: {e}") from e
    if not isinstance(held, dict):
        raise OverrideRefused(f"{document} is not an object")
    title = held.get("title")
    description = held.get("description")
    return (
        title if isinstance(title, str) else "",
        description if isinstance(description, str) else "",
    )


def load(
    bundle_dir: Path, table: tuple[Override, ...] = OVERRIDES
) -> dict[tuple[str, str], Override]:
    """The table as a lookup, with every entry's reason CHECKED against its document.

    **THIS IS WHERE THE OVERRIDE FAILS WHEN THE DEFECT IS GONE** (§3).  Each entry's
    :attr:`Override.defect` has to appear in the document's own ``title`` or
    ``description``, so the day upstream rewrites the sentence the entry cites, this
    raises and names the entry rather than silently continuing to rename a subject whose
    document no longer says what the rename was for.

    It is also the property-1 screen: an entry whose reason is not a quotation never
    loads, so the table cannot come to hold a preference.  Both are the same check,
    because "the reason is the document's words" and "the entry dies with the words" are
    one condition read at two times.
    """
    out: dict[tuple[str, str], Override] = {}
    for entry in table:
        title, description = _words(bundle_dir, entry.document)
        if entry.defect not in title and entry.defect not in description:
            raise OverrideRefused(
                f"{entry.document}{entry.pointer} -> {entry.name}: the stated defect "
                f"{entry.defect!r} is not in the document's own title {title!r} or "
                f"description. An override's reason is a QUOTATION (§3), so either the "
                f"document changed and this entry has outlived the defect it compensates "
                f"for, or the entry was never a quotation."
            )
        key = (entry.document, entry.pointer)
        if key in out:
            raise OverrideRefused(f"two entries for {entry.document}{entry.pointer}")
        out[key] = entry
    return out


def for_document(
    bundle_dir: Path, document: str, table: tuple[Override, ...] = OVERRIDES
) -> dict[str, Override]:
    """This document's entries by POINTER, for the one lowering that reads them.

    Keyed on the pointer alone because a module is one document: the walk already knows
    which, so handing it the whole table would make every lowering able to rename any
    document's class.
    """
    return {
        entry.pointer: entry
        for (doc, _pointer), entry in load(bundle_dir, table).items()
        if doc == document
    }


def rows(
    bundle_dir: Path, derived: Any = None, table: tuple[Override, ...] = OVERRIDES
) -> list[str]:
    """Property 2: every entry as a DIFF against what §4 would have produced.

    ``derived`` answers ``(document, pointer) -> the name §4 derives`` where a caller has
    the naming pass to hand; without it the document's own ``title`` stands in, which is
    §4's input for a root and is what makes the row readable with nothing but the bundle.

    One row per entry, and the quotation is IN the row: a reader comparing the override to
    its alternative must not have to go and find the reason.
    """
    out = []
    for entry in load(bundle_dir, table).values():
        title, _description = _words(bundle_dir, entry.document)
        would = None
        if derived is not None:
            would = derived(entry.document, entry.pointer)
        out.append(
            f"{entry.document}{entry.pointer}\n"
            f"    §4 derives : {would or title or '(no title)'}\n"
            f"    override   : {entry.name}  (domain {entry.domain})\n"
            f"    quoting    : {entry.defect!r}\n"
            f"    because    : {entry.because}"
        )
    return out


def census(bundle_dir: Path) -> str:
    """One line a run can print, so the table's size is visible without reading it."""
    held = load(bundle_dir)
    return f"name overrides {len(held)}: " + ", ".join(
        f"{e.document}{e.pointer} -> {e.name}" for e in held.values()
    )


__all__ = [
    "OVERRIDES",
    "Override",
    "OverrideRefused",
    "census",
    "for_document",
    "load",
    "rows",
]
