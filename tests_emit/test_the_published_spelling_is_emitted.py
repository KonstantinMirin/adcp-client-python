"""Upstream's own spelling of a document ROOT resolves, and it is a NAME and not a type.

``codegen.lower.names.UPSTREAM_TITLE_CASE`` is the rule and this file is what grades it.
Its subject is one sentence: this compiler spells a document root by touching each title
word's FIRST letter, so an acronym the bundle writes survives; upstream's generator spelled
the same title with Python's own ``str.title()``, which flattens one.  ``AdCP Async Response
Data`` is ``AdCPAsyncResponseData`` here and was ``AdcpAsyncResponseData`` there.  Ours is
the faithful spelling -- the schema decides, and the schema's title carries the acronym --
so what is owed upstream's published spelling is a NAME, bound in the module the class is
declared in.

**THERE IS NO LIST OF NAMES HERE AND NONE IN THE COMPILER.**  The population is derived
twice over, from two inputs neither of which is a table anybody maintains: the bundle's own
titles give the names the rule mints, and ``survey/upstream-flat-surface-9.6.1.txt`` --
written by ``survey/alias_surface.py`` from upstream's own 9.6.1 wheel, and committed for
the reason ``tests_emit/test_the_alias_layer_is_names.py`` states -- is what the minted
spellings are GRADED against.  A hand list of the twelve names today's census happens to
import would go stale on the first document whose title gains an acronym; the rule covers
that document with nothing regenerated and no row added here.

**THE SCOPE IS THE DOCUMENT ROOT, and it is measured rather than assumed.**  A ``Root`` and
a titled ``Branch`` are the only two positions this compiler names from a phrase the bundle
wrote, so the branch was the natural second arm, and upstream's own emitted tree refutes it:
graded per MODULE against the tree this repository's history holds at ``2954b258b``,

    git archive 2954b258b src/adcp/types/domains | tar -x -C <scratch>

upstream's counterpart module declares or binds the rule's spelling for **101 of the 101**
roots it fires on and for **0 of the 11** titled branches, and OURS for none of either --
because upstream named a nested model from the FIELD PATH it is reached through and not from
its title.  :func:`test_the_rule_reaches_a_root_and_never_a_titled_branch` holds that scope
by construction, over a hop table built here, so the branch arm cannot return unnoticed; the
figures above are the reason the scope is what it is and are not re-derived in this process,
which would make the suite depend on a git object being fetched.

**WHAT IS ASSERTED, AND NONE OF IT READS THE EMITTED TEXT.**  ``X = TheClass`` renders the
class by identity, so the three claims are ``is``, ``isinstance`` and the run's own record:
no second class can satisfy the first two, and a grep for ``=`` would pass on a file full of
``class X: pass``.  The declaration count is held by
``tests_emit/test_one_node_is_one_declaration.py``, whose equality this rule's record is now
a term of -- so an alias that became a second type reddens there, counting OBJECTS.
"""

from __future__ import annotations

import importlib
import pathlib

import pytest
from nodeset import claimed

from adcp.types._base import SchemaRef
from codegen import bundle, emit, patch
from codegen.lower import names as lower_names

#: **The bundle a RUN reads**: the published one with the build's patch sets applied, which
#: is ``./check``'s derivation and ``tests_emit/fresh.py``'s.  Reading the published one
#: here would grade the rule against titles no run compiled -- the override table supplies
#: some of them, and a title is the one thing this rule is entirely a function of.
BUNDLE = patch.for_build(pathlib.Path("schemas/cache/3.2"))

#: The committed record of upstream's own flat surface, 9.6.1 -- the release the drop-in
#: replaces.  Named with its version for the reason the alias layer's table is: a second
#: version is a second file and never a silent overwrite of this one.
UPSTREAM = pathlib.Path(__file__).resolve().parents[1] / "survey/upstream-flat-surface-9.6.1.txt"


def published() -> dict[str, str]:
    """Every public name of upstream's flat surface, keyed by its case-folded spelling.

    Keyed that way because the question this file asks is about CASE and nothing else: the
    rule claims our spelling and upstream's are one name under two casings, so the record
    has to be reachable by the half the two agree on.
    """
    return {name.lower(): name for name in UPSTREAM.read_text().split()}


def minted() -> dict[str, tuple[str, str]]:
    """Upstream's spelling -> ``(our symbol, the document)``, over the whole run.

    Read off the RUN's own record (``Emitted.recased``) and not re-derived from the
    bundle, so what this file grades is what the compiler decided rather than a second
    opinion about it -- the arrangement ``Emitted.surface`` already has with §1's export
    set, and for the same reason: a second derivation is how two readings of one rule come
    to disagree.
    """
    out = emit.emit(BUNDLE, sorted(bundle.portable(BUNDLE)))
    at = {emit.module_path(document): document for document in out.emitted}
    return {
        word: (symbol, at[module])
        for module, words in out.recased.items()
        for word, symbol in words.items()
        if module in at
    }


@pytest.fixture(scope="module")
def rule() -> dict[str, tuple[str, str]]:
    return minted()


def test_every_spelling_the_rule_mints_is_the_one_upstream_published(
    rule: dict[str, tuple[str, str]],
) -> None:
    """Where upstream's own surface carries the name, it carries UPSTREAM's spelling.

    The equality is stated in both directions over one record, because the rule can be
    wrong in two ways and they are different defects: it can mint a spelling upstream never
    used, and it can mint one for a title whose name upstream published exactly as ours.
    The second is the one that makes the rule a claim about the artifact rather than a
    re-casing hobby, and it is what rules the single-word titles out -- ``AssetVariant`` is
    a class name the document STATES, and ``str.title()`` would make it ``Assetvariant``.

    ``not contradicted`` rather than a count, so no tree's reading of a quantity three lanes
    are moving is pinned here: the claim is that the set is empty.
    """
    surface = published()
    corroborated = {
        word: ours for word, (ours, _) in rule.items() if ours.lower() in surface
    }
    claimed("minted spellings upstream's own surface corroborates", corroborated)
    contradicted = sorted(
        (word, ours, surface[ours.lower()])
        for word, ours in corroborated.items()
        if surface[ours.lower()] != word
    )
    assert not contradicted, (
        "the rule minted a spelling upstream's own surface does not carry, with ours "
        f"beside it: {contradicted}\n{lower_names.UPSTREAM_TITLE_CASE}"
    )


def test_every_minted_name_resolves_at_the_module_the_class_is_declared_in(
    rule: dict[str, tuple[str, str]],
) -> None:
    """``from adcp.types.domains.<domain>.<document> import <upstream's spelling>`` works.

    The module is the one the DOCUMENT compiles to, which is where upstream's machinery
    imports it from: its own layout put a document at ``adcp.types.domains.<path>``, and
    ``adcp.types.domains`` is this tree's ``_schemas`` under the name v9.6 published.  So
    the subject is the private module -- a name here is not on §1's domain surface and is
    not meant to be, because an application that already imports upstream's spelling
    imports it from upstream's path.
    """
    at = {}
    for word, (ours, document) in rule.items():
        at.setdefault(emit.module_name(document), {})[word] = ours
    claimed("modules owed an upstream spelling", at)
    absent = []
    for module, words in sorted(at.items()):
        carried = importlib.import_module(module)
        absent += [f"{module}.{word}" for word in sorted(words) if not hasattr(carried, word)]
    assert not absent, f"the run recorded these and the module does not carry them: {absent}"


def test_an_upstream_spelling_is_a_name_and_never_a_second_type(
    rule: dict[str, tuple[str, str]],
) -> None:
    """``is``, ``isinstance`` and ``__adcp_schema__``: one object under two names.

    Reading 10's clause at this rule -- *"an alias is a NAME and never a second type"* --
    read as BEHAVIOUR and not as text.  A re-export written per name could still have been
    a second class per name, and these three assertions are what no second class satisfies:
    identity, the subclass relation in both directions, and the schema reference, which is
    the thing a class's identity actually IS in this compiler.
    """
    at = {}
    for word, (ours, document) in rule.items():
        at.setdefault(emit.module_name(document), {})[word] = ours
    claimed("modules owed an upstream spelling", at)
    for module, words in sorted(at.items()):
        carried = importlib.import_module(module)
        for word, ours in sorted(words.items()):
            theirs, mine = getattr(carried, word), getattr(carried, ours)
            assert theirs is mine, f"{module}: {word} is not {ours}"
            ref = getattr(mine, "__adcp_schema__", None)
            assert getattr(theirs, "__adcp_schema__", None) is ref
            if isinstance(ref, SchemaRef) and isinstance(mine, type):
                assert isinstance(theirs, type) and issubclass(theirs, mine)
                assert issubclass(mine, theirs)


def test_the_rule_reaches_a_root_and_never_a_titled_branch() -> None:
    """The scope, by construction: a ``Root`` is reached and a titled ``Branch`` is not.

    The measurement in this file's docstring is the REASON for the scope and this is the
    scope itself, stated where a widening goes red: upstream named a nested model from the
    field path, so a branch's title is a claim about a name that generator never minted.
    Both directions on one hop table, so neither arm can be read as the other's.
    """
    hops = {
        "": lower_names.Root(title="SI Get Offering Request"),
        "/oneOf/0": lower_names.Branch(parent="", title="SI Get Offering Success", index=0),
    }
    symbols = {"": "SIGetOfferingRequest", "/oneOf/0": "SIGetOfferingSuccess"}
    out = lower_names.the_published_spellings(hops, symbols, symbols[""], frozenset())
    assert out == {"SiGetOfferingRequest": "SIGetOfferingRequest"}, out


def test_the_rule_is_silent_where_it_has_nothing_to_say() -> None:
    """The four screens, each on its own fixture, because each refuses a different defect.

    A root whose SYMBOL is no longer the title's own name -- §4's collision rule lengthened
    it -- is not a position either compiler named from that title.  A title of one WORD
    states a class name rather than a phrase.  A title upstream's normalisation spells
    exactly as ours earns no second name.  And a word the module's namespace already holds
    is not shadowed, because the name already resolves there to something else.
    """
    def over(title: str, symbol: str, occupied: frozenset[str] = frozenset()) -> dict[str, str]:
        return lower_names.the_published_spellings(
            {"": lower_names.Root(title=title)}, {"": symbol}, symbol, occupied
        )

    assert over("SI Get Offering Request", "SIGetOfferingRequest") == {
        "SiGetOfferingRequest": "SIGetOfferingRequest"
    }
    assert over("SI Get Offering Request", "ProtocolSIGetOfferingRequest") == {}
    assert over("AssetVariant", "AssetVariant") == {}
    assert over("Pagination Request", "PaginationRequest") == {}
    assert over(
        "SI Get Offering Request", "SIGetOfferingRequest", frozenset({"SiGetOfferingRequest"})
    ) == {}


def test_the_reading_catches_a_rule_that_stopped_firing() -> None:
    """The fire probe: the two halves of :func:`lower_names.upstream_class_name` redden.

    Without it this file would be a set of assertions over a record that could go empty and
    take every one of them with it.  So the function is exercised on a title whose spelling
    upstream's own surface carries -- ``MCP Webhook Payload`` -- and on one it spells as we
    do, and the two answers are asserted apart.
    """
    surface = published()
    acronym = "MCP Webhook Payload"
    theirs = lower_names.upstream_class_name(acronym)
    assert theirs == "McpWebhookPayload", theirs
    assert surface.get(lower_names.class_name(acronym).lower()) == theirs
    assert lower_names.upstream_class_name("Pagination Request") is None
    assert lower_names.class_name(acronym) == "MCPWebhookPayload"
