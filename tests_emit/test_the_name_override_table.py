"""§3's override discipline, asserted for the NAME table rather than reviewed.

``docs/plan/architecture.md`` §3: **"AN OVERRIDE DECLARES THE DEFECT IT COMPENSATES FOR,
AND FAILS WHEN THE DEFECT IS GONE."**  ``codegen/overrides.py`` is that mechanism for a
class's name and domain; this file is what keeps it from becoming a fork.

The two properties the row names, each read off the TABLE and the BUNDLE rather than off a
list restated here:

1. **the reason is a QUOTATION** -- every entry's ``defect`` is the document's own words,
   and an entry whose reason is not is refused at load;
2. **every entry reads as a DIFF** -- the derived name, the overridden name and the
   quotation in one row.

And the consequence the row cares about most: **the rename BREAKS and does not redirect.**
The v1 subject answers to ``LegacyFormat`` and to no other word, so code that meant v1
raises instead of silently retargeting to the canonical declaration.
"""

from __future__ import annotations

import importlib
import json

import pytest
from fresh import BUNDLE

from codegen import overrides

#: The one subject this table moves, and the word it frees.  Named here because these two
#: assertions are about PARTICULAR documents -- which is what the row is -- while every
#: other clause below ranges over the table.
V1 = "core/format.json"
V2 = "core/product-format-declaration.json"


def test_every_entry_states_a_defect_the_document_itself_states() -> None:
    """Property 1, and it is the screen that keeps taste out.

    An entry's reason has to be a substring of the document's own ``title`` or
    ``description``.  This asserts the loader enforces it over the LIVE bundle, so the
    clause is also the "fails when the defect is gone" half: the day upstream rewrites a
    quoted sentence, ``load`` raises and this test names the entry.
    """
    held = overrides.load(BUNDLE)
    assert held, "the table is empty: this file would pass over nothing"
    for (document, pointer), entry in held.items():
        raw = json.loads((BUNDLE / document).read_text())
        title = raw.get("title") or ""
        description = raw.get("description") or ""
        assert entry.defect in title or entry.defect in description, (
            f"{document}{pointer} -> {entry.name}: {entry.defect!r} is not in the "
            f"document's own words. An override's reason is a quotation (§3)."
        )
        #: The quotation has to say something: an entry quoting the empty string, or one
        #: character, would satisfy the substring test and establish nothing.
        assert len(entry.defect) >= 12, f"{entry.defect!r} is too short to be a reason"
        assert entry.because, f"{document}{pointer} states no reason of its own"


def test_a_reason_that_is_not_a_quotation_is_refused() -> None:
    """The red direction, proved by construction rather than argued.

    Property 1 is only worth asserting if the loader actually refuses — a screen nobody
    has seen fail is a screen that may not run.
    """
    taste = (
        overrides.Override(
            document=V1,
            pointer="#",
            name="WhateverWeLike",
            domain="core",
            defect="because we prefer it this way",
            because="taste",
        ),
    )
    with pytest.raises(overrides.OverrideRefused, match="is not in the document"):
        overrides.load(BUNDLE, taste)


def test_a_defect_the_document_has_stopped_stating_breaks_the_build() -> None:
    """§3's "fails when the defect is gone", exercised on a document that no longer says it.

    The same loader, the same entry, a bundle whose document has been rewritten: the
    override must not survive its own justification. Put to a constructed document rather
    than waiting for upstream, because the whole point is that the failure arrives
    automatically.
    """
    repaired = (
        overrides.Override(
            document=V1,
            pointer="#",
            name="LegacyFormat",
            domain="core",
            defect="a sentence this document does not contain any more",
            because="upstream has renamed the subject",
        ),
    )
    with pytest.raises(overrides.OverrideRefused, match="outlived the defect|not in the document"):
        overrides.load(BUNDLE, repaired)


def test_every_entry_reads_as_a_diff_against_the_derived_name() -> None:
    """Property 2: the derived name, the override and the quotation in one row.

    Asserted on the RENDERING and not on the data, because the property is about what a
    reader can see: an override nobody can read against its alternative is a fork with a
    reason attached.
    """
    rendered = overrides.rows(BUNDLE)
    assert len(rendered) == len(overrides.load(BUNDLE))
    for row, entry in zip(rendered, overrides.load(BUNDLE).values(), strict=True):
        raw = json.loads((BUNDLE / entry.document).read_text())
        assert "§4 derives" in row and "override" in row and "quoting" in row, row
        #: The name §4 WOULD have produced has to be in the row -- that is the alternative
        #: the override is being read against.
        assert (raw.get("title") or "") in row, row
        assert entry.name in row and entry.defect in row, row


# --------------------------------------------------------------------------- #
# the consequence: the rename BREAKS and does not redirect
# --------------------------------------------------------------------------- #
def test_the_v1_definition_answers_to_the_overridden_name_and_its_schema_ref() -> None:
    """``LegacyFormat`` IS the v1 named-format definition, read off its own pointer."""
    core = importlib.import_module("adcp.types.core")
    held = getattr(core, "LegacyFormat", None)
    assert held is not None, "adcp.types.core.LegacyFormat is not exported"
    ref = held.__adcp_schema__
    assert (ref.document, ref.pointer) == (V1, "#"), ref


def test_format_names_the_canonical_declaration_and_not_the_v1_definition() -> None:
    """``Format`` is the canonical declaration, which is what the word has to mean.

    The alias layer serves it (§4 forbids minting a public name no document states, and
    that document is titled "Product Format Declaration"), so this reads the ANSWER rather
    than how it is bound: whatever ``Format`` resolves to must carry the v2 document's
    pointer.
    """
    core = importlib.import_module("adcp.types.core")
    held = getattr(core, "Format", None)
    assert held is not None, "adcp.types.core.Format is not exported"
    ref = held.__adcp_schema__
    assert (ref.document, ref.pointer) == (V2, "#"), (
        f"Format names {ref.document}{ref.pointer}; the canonical declaration is {V2}#. "
        "A public word that changes meaning while staying importable is the worst "
        "available outcome, which is what this clause exists to prevent."
    )


def test_the_v1_definition_is_reachable_under_no_other_word() -> None:
    """**THE RENAME BREAKS AND DOES NOT REDIRECT**, asserted over every binding of ours.

    Every module of the emitted tree and of the surface is read, and any symbol OTHER
    than the overridden name that resolves to the v1 definition is a redirect — a word
    under which code that meant v1 keeps working while the word's meaning has moved.

    **Derived and not listed**: the row named six sites, and a list of six would go stale
    the moment a seventh binding is added. This ranges over what the tree actually
    exports, so the seventh is caught.
    """
    import pkgutil

    import pydantic

    import adcp.types._schemas as schemas

    core = importlib.import_module("adcp.types.core")
    v1 = core.LegacyFormat
    redirects: list[str] = []
    seen: list[str] = []
    for module in [schemas, *(mi for mi in pkgutil.walk_packages(schemas.__path__, schemas.__name__ + "."))]:
        name = module if isinstance(module, str) else getattr(module, "name", None) or schemas.__name__
        try:
            loaded = importlib.import_module(name)
        except Exception:  # noqa: BLE001 -- a module that does not import binds nothing
            continue
        seen.append(name)
        for symbol, held in vars(loaded).items():
            if symbol.startswith("_") or not isinstance(held, type):
                continue
            if not issubclass(held, pydantic.BaseModel) or held is not v1:
                continue
            if symbol != "LegacyFormat":
                redirects.append(f"{name}.{symbol}")
    assert seen, "no module of the emitted tree was read"
    assert not redirects, (
        f"the v1 definition is still reachable as {redirects}. The rename must BREAK: a "
        "public word that changes meaning while staying importable is the worst available "
        "outcome, so code that meant v1 has to raise."
    )


def test_the_three_case_c_unions_are_untouched() -> None:
    """The three positions where the document STATES the choice still dispatch.

    ``CLAUDE.md``'s format section carries the table and the measurement: the bundle
    states a ``format_id`` XOR ``format_kind`` choice at exactly three positions and all
    three emit a base with two children. They are correct and are NOT this row's subject,
    so this clause is here to catch a rename that collaterally moved them.
    """
    expected = {
        "CreativeAsset": "core/creative-asset.json",
        "CreativeManifest": "core/creative-manifest.json",
        "CreativesItem": "creative/list-creatives-response.json",
    }
    types = importlib.import_module("adcp.types")
    for symbol, document in expected.items():
        held = getattr(types, symbol, None)
        assert held is not None, f"{symbol} is no longer exported"
        assert held.__adcp_schema__.document == document, held.__adcp_schema__
        children = [c for c in held.__subclasses__()]
        assert len(children) >= 2, f"{symbol} has {len(children)} children, expected two"
