"""Two words for two subjects must not resolve to ONE class of ours.

**THE DEFECT THIS GRADES HANDS A CONSUMER THE WRONG TYPE, SILENTLY**
(``adcp-client-python-6ry8``, P0). ``adcp/types/capabilities.py`` binds both ``Features``
and ``SignalsFeatures`` to ``GetAdCPCapabilitiesResponseSignalsFeatures`` -- one object of
ours where ``protocol/get-adcp-capabilities-response.json`` states two subjects, at
``#/properties/signals/properties/features`` and ``#/properties/media_buy/properties/
features``. So the module whose whole job is "re-exports ``get_adcp_capabilities_response``
sub-models with disambiguated names" (``CLAUDE.md``) has NO name for the media-buy one, and
a caller writing the obvious thing builds the signals class, has its field dropped by
``extra=ignore``, and learns about it only when the assignment raises somewhere else.

**IT WAS CAUGHT BY ONE EXAMPLE AND IS NOW CAUGHT BY NOTHING.**
``examples/v3_reference_seller/src/platform.py`` was the single site in the tree that
constructed the word and assigned it, which is how the misbinding surfaced at all; that
example now names the document's class at its own domain path, so the symptom cannot come
back there. This file is the replacement, and it grades the CLAIM rather than those two
words -- a second misbinding is the thing worth catching.

**THE CLAIM, and why each half of it is needed.** A finding is a module that restates
upstream's words where BOTH:

1. two or more of its words resolve to ONE class, AND
2. a class the SAME document states at a sibling PROPERTY position is named by no word of
   that module.

Half 1 alone is not a defect and measuring it says so: 83 collapses exist across the nine
adapter modules, and almost all are deliberate -- ``LegacyProduct``/``Product``,
``BrandRef``/``BrandReference``, ``UIDType``/``UidType``. Reading 10's own words: "AN ALIAS
IS A NAME AND NEVER A SECOND TYPE". So a collapse is only a defect where a subject beside
it is thereby UNREACHABLE, which is half 2.

**AND A SIBLING IS A PROPERTY, NEVER A UNION BRANCH.** ``#/oneOf/0`` beside ``#/oneOf/3``
is one subject's alternatives (the index's "One class per SUBJECT, not per position"), and
a module restating UPSTREAM's words cannot be faulted for a branch upstream never
published. Measured: without that screen this check reports 7 findings, six of them
``oneOf`` branch positions of ``preview_creative`` and ``sync_creatives`` responses, which
are upstream's surface being short rather than our words colliding. With it, it reports
exactly one -- the one above.

**THE ORACLE IS THE DOCUMENT AND NOT UPSTREAM'S WHEEL, which is what makes this runnable.**
The bead asks for "no two distinct words of upstream's resolve to one object of ours where
upstream's own two are distinct", and upstream's wheel is not installed here. The committed
reading of it cannot stand in either: ``survey/adapter-surface-9.6.1.tsv`` records
``their_declaring`` for BOTH these words as upstream's own ``Features``, which is the very
cross-product defect ``survey/adapter_surface.py``'s ``denoted`` docstring measures ("33 of
the 94 were decided WRONG"). The document states both subjects at their own pointers, and
``__adcp_schema__`` carries the pointer on every emitted class, so the question is asked
where the answer is.
"""

from __future__ import annotations

import collections
import importlib
import pkgutil
import sys
from typing import Any

import adcp.types

#: A pointer segment that names a position inside ONE subject rather than a second subject.
#: The differing segment of a sibling pair may not be one of these, nor an index beneath
#: one: a union's branches are branches, and the file's own docstring carries the
#: measurement that says why.
POSITION_SEGMENTS = frozenset(
    {"oneOf", "anyOf", "allOf", "not", "then", "else", "items", "prefixItems", "additionalItems"}
)

#: **THE MISBINDINGS THAT ARE KNOWN, WITH THE ROW THAT OWNS EACH.**  A ratchet, and it may
#: only SHRINK: a finding not named here fails
#: :func:`test_two_words_for_two_subjects_do_not_resolve_to_one_class`, and a row that stops
#: reproducing fails :func:`test_every_known_misbinding_still_reproduces` rather than
#: sitting here as folklore.  The fix for this one is ``survey/adapter_surface.py``'s, which
#: another lane owns, so the row is the hand-off and not an exemption.
KNOWN_MISBINDINGS: dict[tuple[str, tuple[str, ...]], str] = {
    ("adcp.types.capabilities", ("Features", "SignalsFeatures")): (
        "adcp-client-python-6ry8: upstream's two are distinct and their `Features` is the "
        "MEDIA_BUY one, so the word must resolve to "
        "`#/properties/media_buy/properties/features`"
    ),
}


def _adapter_modules() -> list[Any]:
    """Every module that restates upstream's words, read off its own declaration.

    Derived and never listed: ``__adcp_restates_upstream__`` is the marker
    ``survey/adapter_surface.py`` writes, and a tenth module it starts writing is graded
    here with nothing edited. Nine today -- ``_adapter``, ``_generated``, ``aliases``,
    ``buyer``, ``capabilities``, ``compat``, ``guards``, ``legacy``, ``v32``.
    """
    found = []
    for module in pkgutil.iter_modules(adcp.types.__path__):
        held = importlib.import_module(f"adcp.types.{module.name}")
        if getattr(held, "__adcp_restates_upstream__", None):
            found.append(held)
    return found


def _emitted_by_pointer() -> dict[tuple[str, str], type]:
    """Every class the compiler emitted, keyed on the (document, pointer) it carries.

    Keyed on ``__adcp_schema__`` because that is the class's own statement of which node of
    which document it is, and taken only where the class was DEFINED in the module being
    read -- a re-export is the same class at a second path and must not key a second entry.
    """
    importlib.import_module("adcp.types._surface._flat")
    emitted: dict[tuple[str, str], type] = {}
    for name, module in list(sys.modules.items()):
        if module is None or not name.startswith("adcp.types._schemas"):
            continue
        for value in list(vars(module).values()):
            ref = getattr(value, "__adcp_schema__", None)
            if isinstance(value, type) and ref is not None and value.__module__ == name:
                emitted[(ref.document, ref.pointer)] = value
    return emitted


def _property_siblings(
    emitted: dict[tuple[str, str], type], document: str, pointer: str
) -> list[tuple[str, type]]:
    """The classes the same document states at a sibling PROPERTY position of ``pointer``."""
    here = pointer.split("/")
    out = []
    for (other_document, other), value in emitted.items():
        if other_document != document or other == pointer:
            continue
        there = other.split("/")
        if len(there) != len(here):
            continue
        differing = [i for i, (a, b) in enumerate(zip(here, there)) if a != b]
        if len(differing) != 1:
            continue
        at = differing[0]
        if at == 0 or here[at - 1] != "properties":
            continue
        if here[at] in POSITION_SEGMENTS or there[at] in POSITION_SEGMENTS:
            continue
        out.append((other, value))
    return sorted(out)


def _findings() -> dict[tuple[str, tuple[str, ...]], str]:
    """Every (module, words) whose collapse leaves a sibling subject unreachable."""
    emitted = _emitted_by_pointer()
    findings: dict[tuple[str, tuple[str, ...]], str] = {}
    for module in _adapter_modules():
        words = list(getattr(module, "__all__", ()) or ())
        bound = {word: getattr(module, word) for word in words}
        named = {id(value) for value in bound.values()}
        by_object: dict[int, list[str]] = collections.defaultdict(list)
        for word, value in bound.items():
            by_object[id(value)].append(word)
        for group in by_object.values():
            if len(group) < 2:
                continue
            held = bound[group[0]]
            ref = getattr(held, "__adcp_schema__", None)
            if ref is None:
                continue
            unreachable = [
                f"{value.__name__} at {pointer}"
                for pointer, value in _property_siblings(emitted, ref.document, ref.pointer)
                if id(value) not in named
            ]
            if unreachable:
                findings[(module.__name__, tuple(sorted(group)))] = (
                    f"all name {held.__name__} at {ref.document}{ref.pointer}, and no word "
                    f"of that module names {', '.join(unreachable)}"
                )
    return findings


def test_two_words_for_two_subjects_do_not_resolve_to_one_class() -> None:
    """A collapse that leaves a sibling subject unnamed is a wrong type with no error.

    What a failure here means: a module restating upstream's words gave two words one class
    of ours, and a subject the same document states beside it is now reachable under no word
    of that module. The repair is in the generator that wrote the module
    (``survey/adapter_surface.py``), never in this file and never by adding a row below --
    :data:`KNOWN_MISBINDINGS` may only shrink.
    """
    findings = _findings()
    unknown = {key: why for key, why in findings.items() if key not in KNOWN_MISBINDINGS}
    assert not unknown, "\n".join(
        [f"{len(unknown)} word group(s) collapse two subjects into one class:"]
        + [f"  {module}: {', '.join(words)} -- {why}" for (module, words), why in unknown.items()]
    )


def test_every_known_misbinding_still_reproduces() -> None:
    """A row that has been fixed leaves this table, which is how a ratchet shrinks.

    The failure a stale row would otherwise cause is the one this project calls folklore: a
    reader finds the word named here, believes the defect is open, and cannot tell from the
    table that it is not.
    """
    findings = _findings()
    stale = sorted(key for key in KNOWN_MISBINDINGS if key not in findings)
    assert not stale, "\n".join(
        ["these rows no longer reproduce and are owed a deletion, not a re-measurement:"]
        + [f"  {module}: {', '.join(words)}" for module, words in stale]
    )
