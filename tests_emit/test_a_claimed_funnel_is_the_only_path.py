"""A docstring claiming "the one funnel X passes through" is CHECKED, not reviewed.

``docs/plan/final-state.md``, the second of the invariants that file says this project
has paid for by not having: "**a claimed funnel is the only path.**  A comment asserting
'the one funnel X passes through' is an invariant written as prose; where a second path
exists it is a defect the comment hides."

This file is that sentence as an instrument, and it is a defect report rather than a
preference.  ``codegen/compiler.py`` asserts that ``declare_object`` is "the one funnel a
class WITH FIELDS passes through", and a reader who goes looking finds **three sites
passing ``fields=``** (``adcp-client-python-fhi``).  Two of the three are not what the
sentence is about, and nothing in the tree said so.

**THE THREE SITES, AND THE VERDICT IS THAT THE SENTENCE NAMES ITS SUBJECT IMPRECISELY
RATHER THAN THAT THE FUNNEL LEAKS.**

* ``codegen/compiler.py``, inside ``declare_object`` -- the funnel itself, constructing
  :class:`codegen.ir.ClassDecl` with a ``ref``.
* ``codegen/lower/names.py``, inside ``_bound`` -- a ``dataclasses.replace``, which is
  not a construction at all.  It rebinds the symbol slots of a declaration that already
  came through the funnel, and mints no class.  A reader counting ``fields=`` cannot tell
  the two apart, which is the whole of why the count misleads.
* ``codegen/lower/envelope.py``, inside ``base`` -- a REAL second construction of a class
  with fields, and it does not pass through the funnel.  It carries ``ref=None``.

That last one is the resolution.  ``ref`` is the document pointer a class names, so a
``ClassDecl`` with no ``ref`` is the one class of the artifact that is not a document's:
the envelope base, which the walk lowers from no node.  Everything ``declare_object``
gives a class is a reading of the document behind it -- D6's rule tuple, the
``__adcp_schema__`` the renderer writes, D8's ``extra``, the :class:`codegen.compiler.Shape`
a later subclass reads -- so there is nothing for the envelope base to pass through and
nothing it is missing.  **The funnel is a funnel.  Its subject is "a class the walk
declares FOR A DOCUMENT NODE", which the tree spells ``ref is not None``, and the prose
says "a class WITH FIELDS", which is a different set by exactly one member.**

So the invariant below is the precise sentence rather than the written one, and it says
what cannot happen: no ``ClassDecl`` carrying a ``ref`` is constructed outside the funnel.
It is not a count -- it does not say how many sites there are, and a row that splits the
funnel into ten helpers or moves it to another module leaves it green.

**THE CHECK DERIVES ITS OWN SUBJECT FROM THE PROSE**, which is what keeps it from being a
pin on a name.  :data:`FUNNEL` harvests the claim, :func:`funnel_claims` resolves the
symbol each claim names, and a construction is required to sit inside a function the
prose named.  The claim is made in FIVE places and every one resolves: ``declare_object``'s
own docstring, two comments in its body, :class:`codegen.compiler.UnionBase`'s docstring,
and ``codegen/lower/objects.py``'s module docstring -- which names the funnel as a PAIR,
``compiler.fields`` and ``compiler.declare_object``, "the one funnel every class with
fields passes through".  The subject set is therefore those two functions, and admitting
both is faithfulness to the prose rather than slack: the field builder and the class
declarer are what the sentence calls the funnel.  ``codegen/lower/objects.py`` is where
``sdk/slice`` is moving both as this lands; the claim travels with the docstring, so the
check follows it rather than reddening on the move.

**THE SUBJECT IS RESOLVED AND NOT GUESSED, and the first attempt at this file got it
wrong in the way that matters.**  Taking "the symbol named nearest the phrase" resolves
``declare_object``'s own sentence to ``AdCPBaseModel``, because that is the last thing
backticked before it.  What works is RESOLUTION: of the symbols a claim sentence names,
keep those that name a function this tree DEFINES, and fall back to the enclosing function
when none does.  Measured, that filter drops ``allOf``, ``not``, ``dependencies``,
``minProperties``, ``extra`` and ``decided`` -- draft-07 keywords and attribute names in
the same backticks as a symbol -- and keeps ``fields`` and ``declare_object``.  A claim
that named only unresolvable things and sat at module scope would resolve to nothing and
is reported by :func:`test_every_funnel_claim_resolves_to_a_function_of_this_tree` rather
than silently dropped.

**WHAT IS DELIBERATELY NOT GRADED, with the measurement that says why.**

``adcp-client-python-fhi`` asks for the general rule -- every "the one X" sentence in the
tree as a derivable invariant.  Harvested over the 120 hand-authored modules:
**1,060 sentences of prose contain "the one"; 462 of those name a backticked or roled
symbol; 25 are in the funnel family** ("the one funnel / path / caller / writer /
producer / call site / entry point"); **and 5 are a funnel claim.**  The remainder are
about a CONCEPT and not a call site -- "the one failure mode", "the one thing that
matters", "the one reading of the hash" -- and a check ranging over them would grade
sentences that assert nothing a call graph can settle.

**The nearest gradeable generalisation was measured and is NOT written here.**  The form
"``<symbol>`` is the one caller" in a function's docstring says the enclosing function has
one call site, which is mechanically decidable.  Its population in this tree is THREE,
and of those only one is a caller claim -- ``codegen/harness.py``'s ``resolve``, whose
docstring says ":func:`check_accepts` is the one caller".  Evaluated by a resolver keyed
on the called NAME, that claim reads FALSE with ten offending sites, because ``resolve``
is a name ``codegen/store.py``, ``codegen/lower/scalars.py``, ``codegen/emit.py`` and five
others also call and none of those is ``harness.resolve``.  The claim's real reading needs
a QUALIFIED call graph this suite does not have.  **A check that reddens on its own
resolver's blind spot is worse than no check** -- ``tests/test_prose_resolves.py``'s own
rule -- so the general form stays unwritten at a population of three, and the funnel
claim, whose subject resolves in all five of its statements, is graded instead.

One real prose defect fell out of that measurement and is NOT repaired here, because the
repair is a judgement about what the sentence meant rather than a resolution:
``harness.resolve``'s only production call site is ``check_pair``, which then hands the
copy to ``check_accepts``.  ``check_accepts`` is the one CONSUMER, not the one caller, and
the sentence is off by one hop.  Filed rather than edited.

Perturbed in :func:`test_the_rule_catches_a_second_path_into_the_funnel`.  A rule nothing
can break is a finding about the rule.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from nodeset import claimed

ROOT = Path(__file__).resolve().parents[1]

#: The two hand-authored trees whose prose makes the claim and whose code must obey it.
#: ``src/adcp/types/_schemas`` is generated per document and is the walk's OUTPUT, so it
#: constructs no declaration and states no claim about one.
SOURCES = ("codegen", "src/adcp")

#: THE CLAIM, as prose spells it.  Matched over whitespace-joined text because the
#: sentence wraps: a line-oriented grep for this phrase finds four of the five statements
#: and misses :class:`codegen.compiler.UnionBase`'s, which breaks across "the one /
#: funnel".
FUNNEL = re.compile(r"the one funnel", re.I)

#: A symbol a claim names, roled or double-backticked, leaf only.  ``compiler.fields`` and
#: :func:`fields` are the same claim about the same function, and the leaf is what an AST
#: reading of a definition site can match.  Both spellings are harvested and the ROLE is
#: not privileged, because the one claim that names its subject in double backticks --
#: ``codegen/lower/objects.py``'s -- is the one that names the funnel as a pair.
SYMBOL = re.compile(r"``([A-Za-z_][\w.]*)``|:(?:func|meth|class|attr|data):`~?([A-Za-z_][\w.]*)`")

#: The declaration type a class IS, and the keyword naming the document pointer it holds.
#: A construction with ``ref`` the literal ``None`` is a class that is NOT a document
#: node's -- the envelope base, the one such class in the artifact -- and the funnel has
#: nothing to give it.  The exclusion is on the ARGUMENT and not on a file or a function
#: name, so a second ref-less class added later is excluded for the same stated reason and
#: a ref-bearing one added anywhere is graded.
DECLARATION = "ClassDecl"
POINTER = "ref"

#: A sentence boundary, as this repository's prose writes one.  A colon is NOT one: the
#: claim in ``declare_object``'s body sits after one.
SENTENCE = re.compile(r"(?<=[.;])\s+")


def _files() -> list[Path]:
    return sorted(
        p
        for source in SOURCES
        for p in (ROOT / source).rglob("*.py")
        if "_schemas" not in p.parts and "__pycache__" not in p.parts
    )


def _functions_this_tree_defines() -> frozenset[str]:
    """Every function name defined anywhere in the graded sources.

    This is the resolver, and it is deliberately the weakest one that works: a claim's
    subject has to be something that IS a function here, which is what separates
    ``declare_object`` and ``fields`` from ``allOf``, ``not`` and ``minProperties`` --
    draft-07 keywords a sentence writes in the same backticks as a symbol.
    """
    out: set[str] = set()
    for path in _files():
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out.add(node.name)
    return frozenset(out)


def _claims(path: Path) -> list[tuple[str, str]]:
    """``(enclosing function, sentence)`` for every place one module makes the claim.

    Docstrings AND comment blocks, because two of the five statements are ``#`` comments
    in ``declare_object``'s body and that is prose a reader reads the same way.  A run of
    consecutive comment lines is joined before the split, so a claim wrapped across two
    of them is one sentence rather than two fragments neither of which matches.
    """
    source = path.read_text()
    tree = ast.parse(source)
    scopes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]

    def enclosing(line: int) -> str:
        inside = [s.name for s in scopes if s.lineno <= line <= (s.end_lineno or s.lineno)]
        return inside[-1] if inside else ""

    out: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ) and (doc := ast.get_docstring(node)):
            for sentence in SENTENCE.split(" ".join(doc.split())):
                if FUNNEL.search(sentence):
                    out.append((getattr(node, "name", ""), sentence))

    block: list[str] = []
    start: int | None = None
    for number, line in enumerate(source.splitlines() + [""], 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            start = number if start is None else start
            block.append(stripped.lstrip("#:").strip())
            continue
        if block:
            for sentence in SENTENCE.split(" ".join(" ".join(block).split())):
                if FUNNEL.search(sentence):
                    out.append((enclosing(start or number), sentence))
        block, start = [], None
    return out


def funnel_claims() -> dict[str, list[str]]:
    """The function each "the one funnel" claim names, mapped to where it is claimed.

    The subject of a claim is the symbol it names that RESOLVES to a function of this
    tree; a claim naming none is about the scope it sits in, and both spellings are here
    ("This is the one funnel ..." inside ``declare_object`` names nothing).  A claim that
    resolves to nothing at all maps under ``""`` and is reported, never dropped.
    """
    defined = _functions_this_tree_defines()
    out: dict[str, list[str]] = {}
    for path in _files():
        where = path.relative_to(ROOT).as_posix()
        for scope, sentence in _claims(path):
            named = {
                (match.group(1) or match.group(2)).rsplit(".", 1)[-1]
                for match in SYMBOL.finditer(sentence)
            }
            subjects = sorted(named & defined) or [scope]
            for subject in subjects:
                out.setdefault(subject, []).append(where)
    return out


def declaration_sites() -> list[tuple[str, int, str, bool]]:
    """Every construction of a class declaration: file, line, enclosing function, has-ref.

    A ``dataclasses.replace`` is not here, and that is the point of resolving the AST
    rather than grepping ``fields=``: ``replace`` names the FUNCTION ``replace`` and not
    the declaration type, so the rebinding site in ``lower/names.py`` is not a
    construction and is not graded as one.
    """
    out: list[tuple[str, int, str, bool]] = []
    for path in _files():
        tree = ast.parse(path.read_text())
        scopes = [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            if name != DECLARATION:
                continue
            pointer = [k.arg and k.value for k in node.keywords if k.arg == POINTER]
            ref_less = bool(pointer) and (
                isinstance(pointer[0], ast.Constant) and pointer[0].value is None
            )
            inside = [
                s.name for s in scopes if s.lineno <= node.lineno <= (s.end_lineno or s.lineno)
            ]
            out.append(
                (
                    path.relative_to(ROOT).as_posix(),
                    node.lineno,
                    inside[-1] if inside else "",
                    not ref_less,
                )
            )
    return out


def test_every_funnel_claim_resolves_to_a_function_of_this_tree() -> None:
    """The prose the invariant is derived FROM, named and resolved before it is relied on.

    If the sentence is reworded away this reddens, rather than the check below silently
    ranging over nothing -- the vacuous pass ``tests/nodeset.claimed`` exists to refuse,
    and the reason the subject is harvested rather than written down.

    A claim resolving to ``""`` is the one failure this can report: a sentence that names
    no function of this tree AND sits at module scope, which asserts a funnel nothing can
    be matched against.  That is a prose defect and is named as one here rather than
    weakening the invariant next door.
    """
    claims = funnel_claims()
    subjects = claimed("functions a 'the one funnel' claim names", claims)
    assert "" not in subjects, (
        "a 'the one funnel' claim names no function of this tree and sits at module "
        f"scope, so its subject cannot be resolved: {claims.get('')}. Name the function "
        "the sentence is about, or say in plain words what the funnel is."
    )
    defined = _functions_this_tree_defines()
    assert subjects <= defined, sorted(subjects - defined)
    sites = claimed("places the funnel claim is made", set().union(*claims.values()))
    assert all(site.endswith(".py") for site in sites), sorted(sites)


def test_no_class_a_document_node_declares_is_constructed_outside_the_funnel() -> None:
    """THE INVARIANT: a claimed funnel is the only path.

    Every :class:`codegen.ir.ClassDecl` carrying a ``ref`` -- the document pointer that
    makes it a class the walk declares FOR A NODE -- is constructed inside a function the
    prose names as the funnel.  A second construction site would get none of what the
    funnel attaches: D6's rule tuple, the ``__adcp_schema__`` the renderer writes, D8's
    ``extra``, the :class:`codegen.compiler.Shape` a later subclass reads.  That is the
    defect the comment would be hiding, and it is what the sentence promises cannot
    happen.

    The ref-less construction is reported as the exclusion it is rather than skipped:
    ``codegen/lower/envelope.py``'s envelope base names no document pointer, so there is
    nothing for the funnel to give it.  It is asserted PRESENT, because the exclusion is
    load-bearing -- if it ever stopped existing, the stated reason for testing ``ref``
    would have gone with it and nobody would know from here.
    """
    funnel = claimed("functions a 'the one funnel' claim names", funnel_claims())
    sites = claimed("constructions of a class declaration", set(declaration_sites()))

    for_a_node = {site for site in sites if site[3]}
    assert for_a_node, (
        "no construction of a class declaration carries a document pointer: the "
        f"invariant over {sorted(funnel)} would hold vacuously"
    )
    outside = sorted(site for site in for_a_node if site[2] not in funnel)
    assert not outside, (
        f"a class a document node declares is constructed outside {sorted(funnel)}: "
        f"{outside}. The prose calls those 'the one funnel' such a class passes through, "
        "so a second path is a defect the comment hides -- it gets no rule tuple, no "
        "``__adcp_schema__``, no ``extra`` and no Shape."
    )

    ref_less = sorted(site for site in sites if not site[3])
    assert ref_less, (
        "no ref-less class declaration exists any more. Testing ``ref`` above is excused "
        "by exactly one such class -- the envelope base, which is no document node's -- "
        "so if it is gone the exclusion should go with it."
    )


def test_the_rule_catches_a_second_path_into_the_funnel(tmp_path: Path) -> None:
    """The rule reddens on a second path, and passes the two shapes that are CORRECT.

    Three fixtures over the resolver itself, because the real tree is green and without
    this nothing says the check could ever be red:

    * a ``ClassDecl`` with a ``ref``, built outside the funnel -- the defect;
    * a ``ClassDecl`` with ``ref=None`` outside it -- the envelope base's shape, which
      must PASS, and which is what stops the rule being "reject every construction";
    * a ``dataclasses.replace`` carrying ``fields=`` outside it -- the ``lower/names.py``
      shape, which must also pass, and which is the site a ``fields=`` count mistook for
      a construction in the first place.

    And the subject resolver is perturbed on the case that defeated the first draft of
    this file: a claim whose nearest backticked symbol is NOT its subject.
    """
    source = tmp_path / "second_path.py"
    source.write_text(
        "def elsewhere():\n"
        '    """A second path, and it names the funnel nowhere."""\n'
        "    bad = ir.ClassDecl(name=p, ref=schema_ref(d, p), fields=())\n"
        "    envelope = ir.ClassDecl(name=B, ref=None, fields=())\n"
        "    rebound = replace(decl, fields=(), ref=decl.ref)\n"
        "    return bad, envelope, rebound\n"
        "\n"
        "def declare_object():\n"
        '    """Assemble one class out of decided properties.\n'
        "\n"
        "    ``bases`` is empty for a node that composes nothing, and then the base is\n"
        "    ``AdCPBaseModel``.  This is the one funnel a class WITH FIELDS passes\n"
        "    through -- the ``allOf`` row gets its root's ``not``/``minProperties`` by\n"
        "    passing through rather than by repeating the object row's call.\n"
        '    """\n'
        "    return ir.ClassDecl(name=p, ref=schema_ref(d, p), fields=())\n"
    )

    #: The subject resolver on the fixture's own claim.  ``AdCPBaseModel`` is the symbol
    #: NEAREST the phrase and is not the subject; ``allOf``, ``not`` and
    #: ``minProperties`` are keywords in the same backticks.  With ``declare_object`` the
    #: only name among them that this tree defines, the resolution is unambiguous -- and
    #: this is the assertion that says the nearest-symbol reading is not what runs.
    defined = _functions_this_tree_defines()
    claims = _claims(source)
    assert claims, "the fixture states no claim"
    resolved = set()
    for scope, sentence in claims:
        named = {
            (m.group(1) or m.group(2)).rsplit(".", 1)[-1] for m in SYMBOL.finditer(sentence)
        }
        resolved |= set(sorted(named & defined) or [scope])
    assert "declare_object" in resolved, (resolved, claims)
    assert "AdCPBaseModel" not in resolved, resolved

    tree = ast.parse(source.read_text())
    scopes = [
        n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    built = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        if name != DECLARATION:
            continue
        pointer = [k.value for k in node.keywords if k.arg == POINTER]
        has_ref = not (
            pointer and isinstance(pointer[0], ast.Constant) and pointer[0].value is None
        )
        inside = [s.name for s in scopes if s.lineno <= node.lineno <= (s.end_lineno or 0)]
        built.append((inside[-1] if inside else "", has_ref))

    graded = claimed("constructions the fixture states", set(built))
    assert ("elsewhere", True) in graded, graded  # the defect IS seen
    assert ("elsewhere", False) in graded, graded  # the envelope shape is seen and excused
    assert ("declare_object", True) in graded, graded  # the funnel's own is seen

    outside = sorted(scope for scope, has_ref in graded if has_ref and scope != "declare_object")
    assert outside == ["elsewhere"], outside
