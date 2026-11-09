"""A name upstream BINDS rather than DECLARES, bound from upstream's OWN statement.

``survey/adapter_surface.py``'s eleven keys all start from upstream's RUNTIME dump, where a
class answers "which document, which node" with its own ``__module__`` and ``__qualname__``.
A name upstream binds rather than declares answers neither, and that is not a corner:
measured over the demand this branch's census now reads, **122 of the 546 names owed have no
declaration of upstream's behind them at all**, because their type layer binds them -- 283
statements of the form ``X as Y``, 230 ``Y = X`` and 209 ``Y: TypeAlias = <expression>``.
Their ``adcp.types.legacy.LegacyCreateMediaBuyResponse`` is a union alias, so the dump
recorded no module for it and the table's verdict was ``NO-DOCUMENT-NO-SUBJECT``, while
their own ``legacy.py:85`` states the document in one line.

So the twelfth key is upstream's own source (``survey/upstream_aliases.py``), and this file
grades the two things that have to be true of it:

**THE BINDING IS READ AND NEVER GUESSED.**  Every row bound this way carries the chain of
upstream's own statements that produced it (``stated_by``), and the subject is still chosen
by one of the eleven document-bounded keys re-entered at the name UPSTREAM'S STATEMENT
names -- so ``how`` says both halves (``upstream-source -> document+word``) and a row whose
chain is empty is a row no statement of theirs supports.

**AND IT IS A NAME AND NEVER A SECOND TYPE**, which is reading 10 read as behaviour rather
than as text.  ``is``, ``isinstance`` in both directions and ``__adcp_schema__``: no second
class satisfies all three, and a grep for ``import ... as`` would pass on a file full of
``class X: pass``.

**THE POPULATION IS THE COMMITTED TABLE** (``survey/adapter-surface-9.6.1.tsv``), written by
that instrument from upstream's own 9.6.1 wheel, their own tree at the commit the machinery
classification pins, and ours.  No git object is fetched in this process and no upstream
wheel is needed -- the same arrangement
``tests_emit/test_the_alias_layer_is_names.py`` has with its table, and for the same reason.
The PARSE is graded separately, on a fixture tree this file writes, so the reading rules can
redden without a table being regenerated.
"""

from __future__ import annotations

import ast
import csv
import importlib
import json
import sys
from pathlib import Path

import pytest
from nodeset import claimed

from adcp.types._base import SchemaRef

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "survey" / "adapter-surface-9.6.1.tsv"

sys.path.insert(0, str(ROOT / "survey"))

import upstream_aliases as ua  # noqa: E402

#: The prefix every `how` of the twelfth key carries.  One spelling, because a second reader
#: matching on `"upstream"` would also catch `UPSTREAM-AMBIGUOUS`, which is a verdict.
KEY = "upstream-source"


def rows() -> list[dict[str, str]]:
    text = [ln for ln in TABLE.read_text().splitlines() if not ln.startswith("#")]
    return list(csv.DictReader(text, delimiter="\t"))


def stated() -> list[dict[str, str]]:
    """Every BOUND row the twelfth key decided, which this file asserts is not empty."""
    return [r for r in rows() if r["verdict"] == "BOUND" and r["how"].startswith(KEY)]


def test_the_table_carries_rows_upstream_s_own_source_decided() -> None:
    """The fire probe, first: a file of assertions over an empty set asserts nothing.

    Three arms, because the key has three and they fail differently -- a declaration of
    theirs re-entered at their own word, their generator's root-union `TypeAlias`, and a
    plain union they composed by hand.
    """
    bound = {f"{r['module']}.{r['name']}": r["how"] for r in stated()}
    claimed("rows upstream's own source bound", bound)
    assert bound, "no row of the table was decided by upstream's own statements"
    kinds = {r["how"].split(" -> ")[0] for r in stated()}
    assert KEY in {k.split("+")[0] for k in kinds}, kinds
    assert any(r["how"].startswith(f"{KEY} -> ") for r in stated()), (
        "no row re-entered one of the eleven dump keys at the name upstream's statement names"
    )
    assert any(r["how"] == f"{KEY}+document-root" for r in stated()), (
        "no row was bound from their generator's own root-union TypeAlias"
    )


def test_every_row_the_key_bound_names_the_statements_that_bound_it() -> None:
    """``stated_by`` is the evidence, and a binding with no evidence is not a reading.

    The chain is upstream's own files and lines, so what the table records can be read back
    against their tree rather than trusted.  Asserted as SHAPE -- a non-empty chain whose
    last statement names the terminal the row was resolved from -- and never by re-parsing
    their tree here, which would make this process depend on a git object being fetched.
    """
    missing = [
        f"{r['module']}.{r['name']}"
        for r in stated()
        if not r["stated_by"] or not r["stated_terminal"]
    ]
    assert not missing, f"bound by upstream's source with no statement recorded: {missing}"
    for row in stated():
        chain = row["stated_by"].split(" ;; ")
        assert chain and all(".py:" in link for link in chain), row
        kind, _, where = row["stated_terminal"].partition(" ")
        assert kind in ("declared-class", "declared-function", "expression"), row
        assert where.startswith("adcp.types."), row


def test_a_name_the_key_bound_is_the_object_our_walk_emitted() -> None:
    """``is``, ``isinstance`` both ways, and ``__adcp_schema__``: one object, two names.

    Reading 10's clause as behaviour.  The target column names the declaration our compiler
    wrote, so the comparison is against the module the class is DECLARED in and not against
    another alias layer -- which is what makes this an identity claim rather than two
    adapters agreeing with each other.
    """
    checked = {}
    for row in stated():
        targets = ast.literal_eval(row["target"])
        if len(targets) != 1:
            continue  # a union alias is graded by its arms below
        module, _, word = targets[0].rpartition(".")
        try:
            carried = importlib.import_module(row["module"])
            declared = importlib.import_module(module)
        except ImportError as exc:  # pragma: no cover -- a missing module is the failure
            pytest.fail(f"{row['module']} / {module}: {exc}")
        theirs = getattr(carried, row["name"])
        mine = getattr(declared, word)
        assert theirs is mine, f"{row['module']}.{row['name']} is not {targets[0]}"
        ref = getattr(mine, "__adcp_schema__", None)
        assert getattr(theirs, "__adcp_schema__", None) is ref
        if isinstance(ref, SchemaRef) and isinstance(mine, type):
            assert isinstance(theirs, type) and issubclass(theirs, mine)
            assert issubclass(mine, theirs)
        checked[f"{row['module']}.{row['name']}"] = targets[0]
    claimed("names the key bound, asserted identical to our declaration", checked)
    assert checked


def test_no_module_of_the_adapter_declares_a_name_the_key_bound() -> None:
    """The count of declarations does not move, which is the arithmetic half of reading 10.

    Counted over OBJECTS: a class whose ``__module__`` is the adapter's own name is a second
    type, whatever the statement that produced it looked like.
    """
    declared = []
    for row in stated():
        carried = importlib.import_module(row["module"])
        held = getattr(carried, row["name"])
        if isinstance(held, type) and held.__module__ == row["module"]:
            declared.append(f"{row['module']}.{row['name']}")
    assert not declared, f"the adapter declares these rather than naming them: {declared}"


def test_what_the_key_refuses_is_refused_with_its_reason() -> None:
    """A name upstream's statement cannot be followed to a subject of ours stays UNBOUND.

    Reading 10's "a name with no schema subject gets a report and never a class", said about
    an EXPRESSION rather than about a name.  The largest reason is the one that matters
    most: their ``aliases.py:361`` pins ``Discriminator("asset_type")`` on a twenty-arm
    union, and the bare union under that metadata admits a different set of documents -- so
    porting the arms and dropping the discriminator would publish their name over a type
    they did not write.  Asserted non-empty, so the day the set empties this line reddens
    instead of leaving a stale sentence above it.
    """
    refused = {
        f"{r['module']}.{r['name']}": r["stated_refused"] for r in rows() if r["stated_refused"]
    }
    claimed("names upstream's own source names and this key will not bind", refused)
    assert refused
    for spelling, why in refused.items():
        module, _, name = spelling.rpartition(".")
        row = next(r for r in rows() if r["module"] == module and r["name"] == name)
        assert row["verdict"] != "BOUND", f"{spelling} is refused and bound at once: {row}"
        assert why.strip(), spelling
    assert any("iscriminator" in why for why in refused.values()), (
        "no row was refused for the discriminator its expression pins"
    )


# --------------------------------------------------------------------------- #
# the PARSE, graded on a fixture tree so the reading rules redden on their own
# --------------------------------------------------------------------------- #
def _oracle(tmp_path: Path, files: dict[str, str]) -> ua.Oracle:
    root = tmp_path / "types"
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    out = ua.Oracle(rev="fixture", root=root)
    out.read()
    return out


def test_a_rename_is_followed_to_the_declaration_it_names(tmp_path: Path) -> None:
    """``from M import X as Y`` -- the mechanical case, and the chain is both statements."""
    oracle = _oracle(
        tmp_path,
        {
            "legacy.py": "from adcp.types.domains.media_buy.m import Thing as LegacyThing\n",
            "domains/media_buy/m.py": "class Thing:\n    pass\n",
        },
    )
    terminal, chain = oracle.trace("adcp.types.legacy", "LegacyThing")
    assert terminal.kind == "declared-class"
    assert terminal.module == "adcp.types.domains.media_buy.m"
    assert terminal.name == "Thing"
    assert terminal.document == "media_buy.m"
    assert [s.kind for s in chain] == ["import-as", "class"]


def test_the_flat_namespace_is_three_statements_of_theirs(tmp_path: Path) -> None:
    """``from adcp.types import X`` is their facade, their ``_eager`` and their ``_generated``.

    Measured on their 9.6.1 tree: 48 of the names their own suite imports flatly are bound
    nowhere but at the end of that chain, so a lookup stopping at ``__init__`` reports them
    absent when their tree states every one.
    """
    oracle = _oracle(
        tmp_path,
        {
            "__init__.py": "from adcp.types._eager import *  # noqa\n",
            "_eager.py": "from adcp.types._generated import Word\n",
            "_generated.py": "from adcp.types.domains.core.d import Word\n",
            "domains/core/d.py": "class Word:\n    pass\n",
        },
    )
    terminal, chain = oracle.trace("adcp.types", "Word")
    assert terminal.kind == "declared-class", terminal
    assert terminal.document == "core.d"
    assert len(chain) == 3, [str(s) for s in chain]


def test_a_root_union_reports_its_arms_and_its_stem(tmp_path: Path) -> None:
    """Their generator's own spelling of a document ROOT: ``R = R1 | R2 | R3``."""
    oracle = _oracle(
        tmp_path,
        {
            "domains/media_buy/r.py": (
                "R = R1 | R2 | R3\nclass R1: pass\nclass R2: pass\nclass R3: pass\n"
            )
        },
    )
    terminal, _ = oracle.trace("adcp.types.domains.media_buy.r", "R")
    assert terminal.kind == "expression"
    assert terminal.arms == ("R1", "R2", "R3")
    assert terminal.family_stem == "R"
    assert terminal.document == "media_buy.r"
    assert not terminal.discriminator and not terminal.annotated


def test_a_positional_discriminator_is_read_and_not_skipped(tmp_path: Path) -> None:
    """``Discriminator("asset_type")`` is a POSITIONAL call, and that is the whole hazard.

    A reader that looked only at ``Field(discriminator=...)`` keywords reported their
    ``AssetInstance`` as a plain twenty-arm union when ``aliases.py:361`` pins a
    discriminator on it -- which would have ported a different admissible set under their
    name.  Both spellings are read, and ``annotated`` says "there was metadata here" even
    where neither form is recognised, so the screen a port applies is "upstream wrote a bare
    union" rather than "I found nothing I understood".
    """
    oracle = _oracle(
        tmp_path,
        {
            "aliases.py": (
                "A = _Annotated[One | Two, Discriminator('asset_type')]\n"
                "B = Annotated[Three | Four, Field(discriminator='scope')]\n"
                "C = Annotated[Five | Six, SomeUnreadThing()]\n"
                "D = Seven | Eight\n"
            )
        },
    )
    a, _ = oracle.trace("adcp.types.aliases", "A")
    assert a.discriminator == "asset_type" and a.annotated, a
    b, _ = oracle.trace("adcp.types.aliases", "B")
    assert b.discriminator == "scope" and b.annotated, b
    c, _ = oracle.trace("adcp.types.aliases", "C")
    assert not c.discriminator and c.annotated, c
    d, _ = oracle.trace("adcp.types.aliases", "D")
    assert not d.discriminator and not d.annotated and d.arms == ("Seven", "Eight"), d


def test_a_name_their_tree_does_not_bind_is_reported_absent(tmp_path: Path) -> None:
    """The honest remainder, and it is reported as two different facts.

    ``absent`` is "their module exists and binds no such name"; ``no-such-module`` is "their
    tree holds no such module".  Different answers, so they are different kinds -- the first
    says the name is not theirs, the second says the whole import is.
    """
    oracle = _oracle(tmp_path, {"legacy.py": "class Held: pass\n"})
    assert oracle.trace("adcp.types.legacy", "Held")[0].kind == "declared-class"
    assert oracle.trace("adcp.types.legacy", "Absent")[0].kind == "absent"
    assert oracle.trace("adcp.types.nowhere", "Absent")[0].kind == "no-such-module"


def test_the_oracle_and_the_structural_index_agree_about_upstream_s_generated_tree() -> None:
    """Two readings of ONE tree of upstream's, asserted to agree rather than assumed to.

    ``codegen/published.json`` is §4's index of upstream's generated tree, written by
    ``survey/published_structures.py`` from ``2954b258b:src/adcp/types/domains`` and keyed
    on STRUCTURE; this oracle parses ``src/adcp/types`` at the commit the machinery
    classification pins and is keyed on the STATEMENT that binds a name.  Different facts,
    so neither is the other's duplicate -- the index has no alias statements and the oracle
    has no element sets -- but they overlap on one claim: WHICH WORDS upstream's generated
    module declares.  That overlap is corroboration here instead of a second predicate
    nobody compares.

    **AND THE TWO REVISIONS ARE ONE TREE, which is measured and not hoped for.**
    ``git rev-parse 4ed0bce87:src/adcp/types`` and ``2954b258b:src/adcp/types`` are both
    ``bd0a9197``, so the two instruments pin different commits of this repository's history
    and read the same bytes.  The reading below is what would redden if a future pair of
    revisions stopped agreeing: it compares the WORDS, which is the overlap, and says which
    module and which word if they diverge.
    """
    index = json.loads((ROOT / "codegen" / "published.json").read_text())
    oracle = ua.Oracle.at()
    claimed("published modules the structural index holds", set(index["modules"]))
    missing: list[str] = []
    checked = 0
    for module, words in sorted(index["modules"].items()):
        dotted = f"{ua.THEIR_GEN}.{module.replace('/', '.')}"
        if dotted not in oracle.modules:
            missing.append(f"{dotted}: the oracle's extraction holds no such module")
            continue
        for word in sorted(words):
            checked += 1
            if oracle.statement(dotted, word) is None:
                missing.append(f"{dotted}.{word}: the index holds it and the oracle does not")
    assert checked > 3000, checked
    assert not missing[:20], missing[:20]


def test_a_binding_inside_a_guarded_block_is_still_a_binding(tmp_path: Path) -> None:
    """A top-level ``if TYPE_CHECKING:`` or ``try:`` RUNS as the module body runs.

    Their ``_eager.py`` keeps 19 of its renames inside a guarded block, so a reader of
    ``tree.body`` alone would report every one of them as a name their tree does not bind.
    """
    oracle = _oracle(
        tmp_path,
        {
            "guarded.py": (
                "if TYPE_CHECKING:\n"
                "    from adcp.types.domains.core.d import Word as Guarded\n"
                "try:\n"
                "    from adcp.types.domains.core.d import Word as Tried\n"
                "except ImportError:\n"
                "    from adcp.types.domains.core.d import Word as Fallback\n"
            ),
            "domains/core/d.py": "class Word: pass\n",
        },
    )
    for name in ("Guarded", "Tried", "Fallback"):
        terminal, chain = oracle.trace("adcp.types.guarded", name)
        assert terminal.kind == "declared-class", (name, terminal)
        assert chain[0].kind == "import-as", (name, chain)
