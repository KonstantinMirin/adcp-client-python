"""§3a's judgement register: the two readings that keep a row from going stale.

``codegen/vocabularies.py`` declares, per value list the bundle titles NOWHERE, which of
§3a's three local states it is.  It is an INPUT to the collection and not an allowlist --
it decides what the compiler emits and has no power over any check, and a wrong row makes
``tests/test_catalogue.py``'s gate red rather than green.  What this file holds is the two
properties that make a row answerable at all:

* **every row names a value list this bundle states at more than one position.**  A row
  for a value list the bundle states once, or states nowhere, decides nothing -- and the
  only way to find out is to range over the bundle's own reading of it.  So a stale row is
  a red here, which is the half a judgement file has no other way of keeping.
* **no row reaches a question a TITLE already answers.**  §3a's naming rule is the
  bundle's and the register is for what it leaves: a row over a titled value list would be
  a second answer to a decided question, and where the two disagreed the row would silently
  win.

**And the four collections are DISJOINT**, because they are §3a's three states and a state
is one of three: "one named type", "separate types, one value list", "separate types
pending a name".  A value list in two of them has no answer.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest
from nodeset import claimed

from codegen import catalogue, vocabularies

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"


@pytest.fixture(scope="module")
def stated() -> dict[catalogue.Vocabulary, list[catalogue.Stated]]:
    """Every value list the bundle states, with the positions that state it."""
    out: dict[catalogue.Vocabulary, list[catalogue.Stated]] = {}
    for position in catalogue.states(BUNDLE):
        out.setdefault(catalogue.value_list(position), []).append(position)
    return out


def every_row() -> dict[catalogue.Vocabulary, str]:
    """Each row of the register, with the collection it is declared in."""
    return {
        **dict.fromkeys(vocabularies.AGREED, "AGREED"),
        **dict.fromkeys(vocabularies.JUDGED, "JUDGED"),
        **dict.fromkeys(vocabularies.PENDING_A_NAME, "PENDING_A_NAME"),
        **dict.fromkeys(vocabularies.DISTINCT, "DISTINCT"),
    }


def test_every_row_names_a_value_list_the_bundle_restates(
    stated: dict[catalogue.Vocabulary, list[catalogue.Stated]],
) -> None:
    """A row decides a question only if the bundle asks it.

    So the row's key is resolved against the bundle's own stating positions: it must name
    a value list stated at more than one position, because that is the population §3a's
    judgement is about -- "a value set stated at more than one position is a defect in the
    SPECIFICATION whatever we do about it locally".
    """
    declared = every_row()
    rows = claimed("judgements the register declares", declared)
    unstated = {
        str(key): declared[key] for key in rows if len(stated.get(key, ())) < 2
    }
    assert not unstated, json.dumps(unstated, indent=2)


def test_no_row_reaches_a_value_list_the_bundle_titles(
    stated: dict[catalogue.Vocabulary, list[catalogue.Stated]],
) -> None:
    """§3a's naming rule is the bundle's, and the register is for what it leaves.

    A title at ANY of a value list's positions answers the question
    ``codegen/catalogue.py`` asks before it consults a row, so a row over a titled value
    list is a second answer nothing would read -- and, were the order ever reversed, one
    that would overrule the bundle.
    """
    rows = claimed("judgements the register declares", every_row())
    titled = {
        str(key): sorted(catalogue.titles(stated[key]))
        for key in rows
        if catalogue.titles(stated.get(key, ()))
    }
    assert not titled, json.dumps(titled, indent=2)


def test_no_row_reaches_a_value_list_one_document_states_alone(
    stated: dict[catalogue.Vocabulary, list[catalogue.Stated]],
) -> None:
    """§4's content dedup owns one module, so a row inside one document decides nothing.

    "Two nodes with identical content emit one class ... declared under the name of the
    position the walk reaches first", and the dedup's key is node EQUALITY -- so within one
    document the answer is already given, by a rule whose scope is the module and which
    ``codegen/catalogue.py`` deliberately does not reach into.  A row there is inert: the
    collection records the group and never consults the judgement, which is a row a reader
    would believe and nothing would read.
    """
    rows = claimed("judgements the register declares", every_row())
    confined = {
        str(key): sorted({p.document for p in stated[key]})
        for key in rows
        if len({p.document for p in stated.get(key, ())}) == 1
    }
    assert not confined, json.dumps(confined, indent=2)


def test_a_value_list_is_in_exactly_one_collection() -> None:
    """§3a's three states, and a value list is in one of them.

    ``AGREED`` and ``JUDGED`` are one state with two evidences and the other two are the
    other two states, so four collections carry three answers -- and a key in two of them
    has none.
    """
    counted = Counter(
        key
        for collection in (
            vocabularies.AGREED,
            vocabularies.JUDGED,
            vocabularies.PENDING_A_NAME,
            vocabularies.DISTINCT,
        )
        for key in collection
    )
    twice = {str(key): n for key, n in counted.items() if n > 1}
    assert not twice, json.dumps(twice, indent=2)
    for key in claimed("judgements the register declares", counted):
        assert vocabularies.one_subject(key) != vocabularies.separate(key), str(key)


def test_a_judged_name_is_an_identifier_and_a_pending_one_is_never_emitted() -> None:
    """The names the register carries, and the two different things they are for.

    :data:`vocabularies.JUDGED`'s name is EMITTED, so it is an identifier in the tree's own
    convention -- §3a: "a title is a human string and the type is an identifier".
    :data:`vocabularies.PENDING_A_NAME`'s is the UPSTREAM ASK's content and is never
    emitted, which is why it is allowed to be prose and why ``catalogue.judged`` reads only
    the first collection.
    """
    for key in claimed("names the register emits", vocabularies.JUDGED):
        name = vocabularies.JUDGED[key]
        assert name.isidentifier(), (str(key), name)
        assert name[:1].isupper(), (str(key), name)
        assert vocabularies.judged(key) == name
    for key in claimed(
        "names the register asks upstream for", vocabularies.PENDING_A_NAME
    ):
        assert vocabularies.judged(key) is None, str(key)
