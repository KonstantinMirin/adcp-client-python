"""The STRUCTURAL IDENTITY of a declaration, and the join that reads upstream's words off it.

**WHAT THIS IS FOR.**  ``codegen/lower/names.py``'s :data:`~codegen.lower.names.UPSTREAM_TITLE_CASE`
is a RULE: upstream's generator spelled a document ROOT's name with ``str.title()`` over the
title's words, so their spelling is derivable from the title and nothing has to be read off
their artifact.  Measured against upstream's own emitted tree, that rule reaches the roots
and only the roots -- 101 of 101, and 0 of the 11 titled ``oneOf`` branches.  **This module
is the complement: the positions a title's normalisation cannot reach at all**, because
upstream's generator did not name them from a title.  It named them from the FIELD PATH it
reached them through and numbered the siblings it met on the way: ``Assets``, ``Assets9`` ...
``Assets28`` for the twenty-one branches of one union, ``Fields`` and ``Field1`` for two
documents' nested enumerations, ``AcceptancePolicyProfileId`` for an array's element.

**AND NO NAMING RULE IS AVAILABLE FOR THEM, WHICH IS MEASURED AND NOT ASSUMED**
(``adcp-client-python-zwqa``).  The derivable rule for a nested name is "name it after the
nearest ancestor property key, first taker unnumbered".  Read against upstream's own emitted
tree it mints 482 bindings, of which that tree carries the word 150 times and NOT 332; and
at the one name it is wanted for, its first taker is the discriminator BRANCH
(``AssetsItemIndividual``) and not the branch LEAF the application constructs.  A rule that
is wrong two times in three is not a rule, and a hand-bound list per name is the artifact
the title rule exists to avoid committing.

**SO THE WORD IS READ AND NOT DERIVED, AND THE KEY IS STRUCTURE.**  Upstream's entire 9.6.1
emitted tree is in this repository's history::

    git archive 2954b258b src/adcp/types/domains | tar -t
    git show 2954b258b:src/adcp/types/domains/core/format.py

so their words do not have to be guessed from a title: they can be READ from the tree that
published them, and the question becomes a JOIN.  :data:`STRUCTURAL_IDENTITY` is the join
key, :func:`from_source` reads it off their published module, :func:`from_declarations`
reads the same key off this compiler's own IR, and :func:`bind` is the join -- which binds
only where the match is UNIQUE and reports every other outcome by name.

**AN ALIAS IS A NAME AND NEVER A SECOND TYPE.**  What a binding emits is
``ir.AliasDecl(word, TypeRef(symbol, local=True))``, which the renderer writes as
``Assets = IndividualImageAsset`` -- the class by IDENTITY.  No declaration is added, no
``__adcp_schema__`` is minted, ``isinstance`` is unaffected, and ``./check``'s emitted and
refused counts cannot move.
"""

from __future__ import annotations

import ast
import hashlib
import json
from collections.abc import Collection, Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from codegen import ir

#: **THE JOIN KEY, quoted by the checks that grade it**
#: (``tests_emit/test_the_published_structure_is_bound.py``), for the reason
#: ``lower/names.UPSTREAM_TITLE_CASE`` is quoted by its own: the sentence the code states and
#: the sentence a failure reports against are one string.
#:
#: **THE CONST VALUES ARE PART OF THE KEY AND THAT IS THE WHOLE OF WHY THIS WORKS.**
#: Upstream's ``Assets`` and ``Assets9`` differ in ONE element -- ``asset_type`` pinned to
#: ``'image'`` against ``'video'`` -- and in nothing else.  Measured over upstream's own tree
#: at ``2954b258b`` against this compiler's: with the const values in the key the join is
#: unique for 917 words and ambiguous for 57; with them dropped it is unique for 783 and
#: ambiguous for 277, and ``Assets`` itself reaches THIRTEEN declarations of ours at once --
#: the whole individual-asset union collapsed onto one key.
#:
#: **THE FIELD SET IS THE RESOLVED ONE, INHERITED FIELDS INCLUDED**, because each generator
#: split the same subject across bases differently and the split is not the subject:
#: upstream's ``Assets(BaseIndividualAsset)`` states three fields of its own and inherits
#: six, ours is ``IndividualImageAsset(AssetsItemIndividual, BaseIndividualAsset)`` and
#: states three and inherits six from TWO bases.  One base against two is a fact about the
#: generators; the eight wire names and the two pinned values are the fact about the wire.
STRUCTURAL_IDENTITY = (
    "a declaration's structural identity is its RESOLVED element set and nothing a "
    "generator chose: for a model, the wire name of every field it declares or inherits, "
    "each beside the SHAPE of its type (a list, a mapping, a union, a generic alias, or "
    "none of those), the VALUE it pins where the node pins one, and whether it is required "
    "-- asked only of a field that pins no value, because a pinned field is required here "
    "and defaulted to its own constant there, and the pinned value already says everything "
    "requiredness could.  For an enumeration it is the member VALUE LIST read as a set, "
    "which is the identity reading 10 already fixes for one.  A declaration with no "
    "elements -- a root model, a constrained scalar, an alias, a field-free class -- has NO "
    "structural identity and is reported as having none rather than given a key its "
    "contents cannot distinguish: a `root` field is carried by every root model in either "
    "tree, so a key that counted it would make 11 declarations of ours one subject"
)

#: Where upstream's published structures are held: the index :func:`published` reads and
#: ``python -m survey published`` writes.  **A COMMITTED ARTIFACT OF THE REPOSITORY, and the
#: run is a reader of it** -- the same arrangement ``codegen/held.py`` states for the drawn
#: corpus, and for the same reason: the artifact is derived from an input the run cannot
#: reach (a revision of this repository's own history), so a run that re-derived it would
#: need git.  The revision and the release it was read from are IN the file, so no version
#: literal enters this package (D9).
PUBLISHED = Path(__file__).resolve().parent / "published.json"

#: The shapes a type can have, as the one vocabulary both readers answer in.  ``""`` is a
#: scalar or a reference to another declaration: the two generators spell those differently
#: (``StrictBool`` against ``bool``, ``WireAnyUrl`` against ``str``) and the spelling is a
#: fact about which library wrote the annotation, so it is not in the key.  ``ir.TypeRef``
#: already names four of these, and :func:`_shape` is the same four read off an annotation.
SHAPES = ("", "list", "dict", "union", "alias", "literal")

#: The bases that make a class a ROOT MODEL rather than a model with a field called ``root``.
#: Both trees spell it the same way because both parametrize the SDK's own base, and
#: :data:`STRUCTURAL_IDENTITY` says why it matters: eleven declarations of ours carry
#: ``root`` and nothing else.
ROOT_BASES = ("AdCPRootModel", "RootModel", "AdCPBaseRootModel")

#: One ELEMENT of a model's identity as both readers hand it to :func:`model`:
#: ``(wire name, shape, the value it pins as a 0- or 1-tuple, required)``.  Named because
#: four readers spell it and a tuple written out four times is four places it can drift.
Element = tuple[str, str, tuple[Any, ...], bool]


def digest(structure: Mapping[str, Any] | None) -> str:
    """One structure's canonical digest, or ``""`` where it has no structural identity."""
    if not structure:
        return ""
    canonical = json.dumps(structure, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()[:20]


def model(fields: Iterable[tuple[str, str, tuple[Any, ...], bool]]) -> dict[str, Any] | None:
    """:data:`STRUCTURAL_IDENTITY` for a model, from ``(wire, shape, pinned, required)``.

    **ONE CONSTRUCTOR FOR BOTH READERS, so the two cannot disagree about the FORM of the
    key** -- they disagree only about what they read, which is what the gate compares.  The
    elements are sorted here rather than by the caller: a field order is a document's own and
    a key is a set.

    ``pinned`` is a tuple because ``const: null`` is a pinnable value, so a bare ``None``
    could not be told from an absent one -- :attr:`ir.TypeRef.literals`' own reason, and the
    reader for the other side unwraps a ``Literal`` into the same 1-tuple.  Requiredness
    rides only on an unpinned field, for the reason :data:`STRUCTURAL_IDENTITY` states.
    """
    elements = sorted(
        [
            wire,
            shape,
            json.dumps(pinned[0], sort_keys=True, default=str) if len(pinned) == 1 else "",
            "" if pinned else ("req" if required else "opt"),
        ]
        for wire, shape, pinned, required in fields
    )
    return {"kind": "model", "elements": elements} if elements else None


def enumeration(values: Iterable[Any]) -> dict[str, Any] | None:
    """:data:`STRUCTURAL_IDENTITY` for an enumeration: the member value list, as a set."""
    members = sorted(json.dumps(v, sort_keys=True, default=str) for v in values)
    return {"kind": "enum", "members": members} if members else None


# --------------------------------------------------------------------------- their reader


def _head(node: ast.expr) -> str:
    """The leading NAME of an annotation or a base expression, qualifier dropped."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _head(node.value)
    return ""


def _arms(node: ast.expr) -> list[ast.expr]:
    """``X | Y | None`` flattened; anything else is its own single arm."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _arms(node.left) + _arms(node.right)
    return [node]


def _unwrap(ann: ast.expr) -> tuple[ast.expr | None, bool]:
    """``Annotated[X, …]`` and ``X | None`` stripped: ``(X, admits null)``.

    A ``None`` arm is dropped and reported as the second half, for the reason
    ``survey/structural_signature.RELAXATIONS`` measured on this very pair of trees: the
    arm is on one side alone at hundreds of nodes, because one generator spells an optional
    field ``X | None = None`` and the other states the default alone.  What survives is the
    REQUIREDNESS, which both generators do agree about and which is read off the default.
    """
    if isinstance(ann, ast.Subscript) and _head(ann) == "Annotated":
        inner = ann.slice.elts[0] if isinstance(ann.slice, ast.Tuple) else ann.slice
        return _unwrap(inner)
    arms = _arms(ann)
    rest = [a for a in arms if not (isinstance(a, ast.Constant) and a.value is None)]
    nullable = len(rest) != len(arms)
    if not rest:
        return None, True
    # **ONLY RECURSE WHERE SOMETHING WAS STRIPPED**, or a scalar annotation unwraps to
    # itself forever: ``_arms`` returns a non-union node as its own single arm, so the
    # one-arm case is both "a union with its null arm dropped" and "not a union at all".
    if len(rest) == 1 and rest[0] is not ann:
        stripped, deeper = _unwrap(rest[0])
        return stripped, nullable or deeper
    if len(arms) > 1:
        return ann, nullable
    return rest[0], nullable


def _shape_and_pin(ann: ast.expr) -> tuple[str, tuple[Any, ...]]:
    """One annotation's :data:`SHAPES` entry and the value it pins, if it pins one."""
    inner, _ = _unwrap(ann)
    if inner is None:
        return "", ()
    if isinstance(inner, ast.BinOp):
        return "union", ()
    head = _head(inner)
    if head == "Literal" and isinstance(inner, ast.Subscript):
        elts = inner.slice.elts if isinstance(inner.slice, ast.Tuple) else [inner.slice]
        if len(elts) == 1 and isinstance(elts[0], ast.Constant):
            return "", (elts[0].value,)
        return "literal", ()
    if head in ("list", "List", "Sequence", "tuple", "Tuple", "set", "Set"):
        return "list", ()
    if head in ("dict", "Dict", "Mapping"):
        return "dict", ()
    if head in ("Union", "Optional"):
        return "union", ()
    if isinstance(inner, ast.Subscript):
        return "alias", ()
    return "", ()


def _alias_of(*nodes: ast.expr | None) -> str | None:
    """``Field(alias='$schema')`` anywhere in a field's annotation or default."""
    for node in nodes:
        for found in ast.walk(node) if node is not None else ():
            if (
                isinstance(found, ast.keyword)
                and found.arg == "alias"
                and isinstance(found.value, ast.Constant)
            ):
                return str(found.value.value)
    return None


def value_lists(texts: Iterable[str]) -> dict[str, list[Any]]:
    """Every ``_VALUES_A_B = ('a', 'b')`` constant a set of rendered modules declares.

    **§3a PUTS A SHARED VALUE LIST IN ITS OWN MODULE AND THE MEMBERS IMPORT IT**, so
    ``core/vendor_metric_optimization_supported_metric.py`` reads
    ``from ..common._vocabularies import _VALUES_COST_PER_THRESHOLD_RATE`` and spells its
    members as indexes into it.  A reader of ONE module's text therefore cannot resolve the
    values from that text alone, and this is how it is told them: the caller that holds the
    whole run's files computes the mapping once and hands it to :func:`from_source`.
    Measured: without it, 8 modules' enumerations read as structureless on the AST side and
    the two readers disagreed about 8 bindings.

    A name collision is harmless and is not guarded against: the constant is NAMED FROM ITS
    OWN MEMBERS (``lower/names.the_value_lists``), so two modules spelling one name are two
    modules holding one value list.
    """
    out: dict[str, list[Any]] = {}
    for text in texts:
        out.update(_value_lists(ast.parse(text)))
    return out


def _value_lists(module: ast.Module) -> dict[str, list[Any]]:
    """§3a's shared VALUE-LIST constants of one module: ``_VALUES_A_B = ('a', 'b')``.

    **AN ENUMERATION'S MEMBERS ARE NOT ALWAYS LITERALS IN THE TEXT, which is this
    compiler's own output and not upstream's.**  §3a writes one value list for the several
    types of a module that share it (``lower/names.the_value_lists``), so a member reads
    ``COST_PER = _VALUES_COST_PER_THRESHOLD_RATE[0]`` -- and a reader that took only an
    ``ast.Constant`` would answer "no members" for it, call the class structureless, and
    silently disagree with the IR reader about 7 modules.  Measured: that is exactly the
    disagreement ``tests_emit/test_the_published_structure_is_bound.py`` caught.
    """
    out: dict[str, list[Any]] = {}
    for node in module.body:
        # **BOTH SPELLINGS OF A MODULE CONSTANT, because §3a writes the ANNOTATED one** --
        # ``_VALUES_COST_PER_THRESHOLD_RATE: tuple[str, ...] = (...)`` -- and a reader that
        # took ``ast.Assign`` alone found none of the four vocabulary modules' lists.
        target: str
        value: ast.expr | None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target, value = node.target.id, node.value
        elif (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            target, value = node.targets[0].id, node.value
        else:
            continue
        if not target.startswith("_") or not isinstance(value, ast.Tuple | ast.List):
            continue
        values = [e.value for e in value.elts if isinstance(e, ast.Constant)]
        if len(values) == len(value.elts):
            out[target] = values
    return out


def _member_value(node: ast.expr, lists: Mapping[str, list[Any]]) -> tuple[Any, ...]:
    """One enumeration member's VALUE, as a 1-tuple, or ``()`` where it states none.

    Two spellings and no others in either tree: a literal, and an index into one of
    :func:`_value_lists`' constants.  A ``MemberAlias(...)`` call is a second NAME for a
    member already counted and states no value of its own, so it answers ``()`` -- which is
    what keeps the member list a set of values rather than a count of statements.
    """
    if isinstance(node, ast.Constant):
        return (node.value,)
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and isinstance(node.slice, ast.Constant)
        and isinstance(node.slice.value, int)
    ):
        values = lists.get(node.value.id)
        if values is not None and -len(values) <= node.slice.value < len(values):
            return (values[node.slice.value],)
    return ()


def from_source(
    text: str, vocabularies: Mapping[str, list[Any]] = {}
) -> dict[str, dict[str, Any] | None]:
    """One PUBLISHED module's text -> each class's word and its structural identity.

    ``vocabularies`` is :func:`value_lists` over the other modules of the same tree, for the
    reason that function states: §3a's shared value list lives in its own module and an
    enumeration's members are indexes into it, so the values are not in this text.
    Upstream's generator writes every member as a literal, so their side passes nothing.

    **THE READER FOR UPSTREAM'S SIDE, and the one the gate turns on OUR side too.**  The run
    reads its own side off the IR (:func:`from_declarations`), which is the only reading
    available before a module is rendered -- so there are two readers of one key, and two
    readers of one key is exactly the arrangement a gate has to close.
    ``tests_emit/test_the_published_structure_is_bound.py`` runs THIS function over the
    text the run itself rendered and asserts the join it produces is the join the run
    recorded, module for module: one notion, two producers, compared over the whole tree.

    Inheritance is folded WITHIN the module and a base declared elsewhere contributes
    nothing, which is a limit of both readers and not of one: the run cannot see another
    module's fields from inside the pass that names this one.  It costs nothing on the
    population this join is for -- a cross-module base in either tree is an envelope base,
    and an envelope base sits on a document ROOT, which is the title rule's population and
    not this one.
    """
    parsed = ast.parse(text)
    lists = {**vocabularies, **_value_lists(parsed)}
    declared: dict[str, dict[str, Any]] = {}
    for node in parsed.body:
        if not isinstance(node, ast.ClassDef):
            continue
        fields: dict[str, Element] = {}
        members: list[Any] = []
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                name = stmt.target.id
                if name.startswith("_") or _head(stmt.annotation) == "ClassVar":
                    continue
                wire = _alias_of(stmt.annotation, stmt.value) or name.rstrip("_")
                shape, pinned = _shape_and_pin(stmt.annotation)
                fields[wire] = (wire, shape, pinned, stmt.value is None)
            elif (
                isinstance(stmt, ast.Assign)
                and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)
                and not stmt.targets[0].id.startswith("_")
                and stmt.targets[0].id != "model_config"
            ):
                members.extend(_member_value(stmt.value, lists))
        declared[node.name] = {
            "bases": [_head(b) for b in node.bases],
            "root": any(_head(b) in ROOT_BASES for b in node.bases),
            "own": fields,
            "members": members,
        }

    def folded(
        word: str, stack: frozenset[str]
    ) -> dict[str, tuple[str, str, tuple[Any, ...], bool]]:
        if word in stack or word not in declared:
            return {}
        out: dict[str, Element] = {}
        for base in declared[word]["bases"]:
            out.update(folded(base, stack | {word}))
        out.update(declared[word]["own"])
        return out

    out: dict[str, dict[str, Any] | None] = {}
    for word, blob in declared.items():
        if blob["members"]:
            out[word] = enumeration(blob["members"])
        elif blob["root"] or any(declared.get(b, {}).get("root") for b in blob["bases"]):
            out[word] = None
        else:
            out[word] = model(folded(word, frozenset()).values())
    return out


def names_bound(text: str) -> frozenset[str]:
    """Every name one rendered module's text binds at module scope.

    **THE TEXT's OWN READING OF ``occupied``**, which the naming pass computes from its
    symbol table, the renderer's carriers and the walk's imports.  A reader that had only
    the class definitions would propose a word the module already resolves through an
    import -- measured on this tree: ``collection/get_collection_list_response`` imports
    ``Collection`` from the document that declares it, and a join blind to the import binds
    upstream's ``Collection`` to our ``CollectionsItem`` in a module where the word already
    means something else.  Shadowing a resolving name is the one outcome worse than the
    absence (``lower/names.the_published_spellings``), so the gate's independent reading has
    to see the whole namespace and this is it.
    """
    out: set[str] = set()
    for node in ast.parse(text).body:
        if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            out.add(node.name)
        elif isinstance(node, ast.Import | ast.ImportFrom):
            out.update(alias.asname or alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.Assign):
            out.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            out.add(node.target.id)
    return frozenset(out)


# --------------------------------------------------------------------------- our reader


def from_declarations(
    declarations: Sequence[ir.Declaration],
) -> dict[str, dict[str, Any] | None]:
    """This run's own module -> each declared symbol and its structural identity.

    The same key as :func:`from_source` read off the IR instead of off text, which is what
    the naming pass has: a module's declarations are settled and its text is not written
    yet.  A :class:`ir.RootModelDecl`, a :class:`ir.AliasDecl`, a :class:`ir.ValuesDecl` and
    a :class:`ir.RootBinding`'s alias carry no element set and answer ``None``, which is
    :data:`STRUCTURAL_IDENTITY`'s own clause and not an omission.
    """
    classes = {d.name: d for d in declarations if isinstance(d, ir.ClassDecl)}

    def folded(
        symbol: str, stack: frozenset[str]
    ) -> dict[str, tuple[str, str, tuple[Any, ...], bool]]:
        if symbol in stack or symbol not in classes:
            return {}
        out: dict[str, Element] = {}
        for base in classes[symbol].bases:
            if base.local:
                out.update(folded(base.path, stack | {symbol}))
        for f in classes[symbol].fields:
            out[f.wire] = (f.wire, _shape_of(f.type), f.type.literals, f.required)
        return out

    out: dict[str, dict[str, Any] | None] = {}
    for declaration in declarations:
        if isinstance(declaration, ir.ClassDecl):
            out[declaration.name] = model(folded(declaration.name, frozenset()).values())
        elif isinstance(declaration, ir.EnumDecl):
            out[declaration.name] = enumeration(m.value for m in declaration.members)
        elif isinstance(declaration, ir.RootBinding):
            inner = declaration.declaration
            out[declaration.symbol] = (
                enumeration(m.value for m in inner.members)
                if isinstance(inner, ir.EnumDecl)
                else None
            )
        elif isinstance(declaration, ir.RootModelDecl | ir.AliasDecl | ir.ValuesDecl):
            out[declaration.name] = None
    return out


def _shape_of(type_ref: ir.TypeRef) -> str:
    """:attr:`ir.TypeRef.container` as a :data:`SHAPES` entry.

    ``ir.TypeRef`` already names ``list``, ``dict``, ``union`` and ``alias``, which is
    :data:`SHAPES` less the two this side never spells: a ``literal`` over several values is
    a reference to an ENUMERATION in this compiler's output, so the shape it answers is the
    reference's ``""``, and the other reader answers ``""`` for a reference too.

    **THE ``None`` ARM IS DROPPED HERE EXACTLY AS :func:`_unwrap` DROPS IT ON THE OTHER
    SIDE, and the two must do it together or neither.**  A field that admits an explicit
    JSON ``null`` is ``union`` over ``(X, None)`` in the IR and ``X | None`` in the text, so
    an unwrap on one side alone makes ONE field's shape read ``union`` against ``""`` and
    costs the whole class its match -- measured: 8 modules, found by the gate that compares
    the two readers.  What carries the optionality is requiredness, which both sides read
    and neither invents.
    """
    if type_ref.container == "union":
        rest = [arm for arm in type_ref.of if arm.path != "None"]
        if len(rest) == 1:
            return _shape_of(rest[0])
        if not rest:
            return ""
    return type_ref.container if type_ref.container in SHAPES else ""


# --------------------------------------------------------------------------- the join


#: Why one of upstream's words is NOT bound.  **EVERY OUTCOME IS NAMED, because an
#: ambiguous join is a defect to report and not one to break by picking a side**: a word
#: that reaches two declarations of ours reaches them because this key cannot tell them
#: apart, and binding the first would publish a name for a subject nobody decided.
REFUSALS = {
    "ours-already": (
        "the module already resolves this word -- it declares it, imports it, or the title "
        "rule bound it there (``lower/names.the_published_spellings``).  Shadowing a "
        "declaration to publish a second spelling of a third class is the one outcome "
        "worse than the absence"
    ),
    "theirs-has-no-structure": (
        "upstream's declaration has no structural identity: a root model, a constrained "
        "scalar, an alias or a field-free class.  :data:`STRUCTURAL_IDENTITY`'s own clause"
    ),
    "the-root's-question": (
        "the word's structure is our document ROOT's, and the root is the TITLE rule's "
        "population (``lower/names.UPSTREAM_TITLE_CASE``, measured at 101 of 101).  A word "
        "that could be the root is not this join's to bind, whatever its spelling"
    ),
    "ambiguous": (
        "the word's structure reaches SEVERAL declarations of ours, so this key could not "
        "decide the target.  Reported and never resolved by position"
    ),
    "unmatched": (
        "no declaration of ours in this module has that structure.  Either upstream states "
        "a subject we do not, or the two states differ at an element -- and which of those "
        "it is is a question for the bundle and not for a join"
    ),
    "target-unbound": (
        "upstream's own statement says this word is another word of theirs, and that other "
        "word is not bound here -- so the statement is READ and still resolves to nothing. "
        "An alias of an unbound name is unbound, never a guess at what it meant"
    ),
    "arity": (
        "upstream's root union and ours do not list the same number of arms, so the Nth "
        "arm of one is not the Nth of the other and the positions cannot be paired.  The "
        "whole family is refused rather than the arms that happen to line up"
    ),
    "const-disagrees": (
        "a property BOTH arms pin a ``const`` on does not agree across the pair, so the "
        "two positions are not one subject however they are ordered.  The whole family is "
        "refused, which is what makes a mis-ordered union detected instead of mis-bound"
    ),
}


def statements_from_source(text: str) -> dict[str, Any]:
    """One published module's own STATEMENTS, which are names and never subjects.

    **A SECOND KIND, DELIBERATELY NOT FOLDED INTO :func:`from_source`.**  That reader
    records a DECLARATION and its structural identity -- a subject.  A statement binds a
    name to something already declared, so it has no structure of its own and indexing it
    as though it did would make the oracle lie: ``Creatives1 = Creative`` would arrive as a
    word with ``Creative``'s structure, and a join keyed on structure would then see two
    of upstream's words at one identity and refuse BOTH as ``ambiguous``.  Measured over
    ``2954b258b:src/adcp/types/domains`` -- 1,088 modules, 4,360 declarations -- there are
    18 of the first kind and 30 of the second, and the index carried neither.

    Two kinds are returned, because they resolve by different rules:

    ``aliases``   ``X = Y`` with ``Y`` a bare name.  Eighteen in seven modules.  It
                  resolves through whatever ``Y`` resolves to, so it is bound by
                  :func:`bind_statements` AFTER the structural join has decided ``Y``.
    ``unions``    ``X = A | B | ...`` with every arm a bare name -- upstream's generated
                  spelling of a root union.  **THIS IS WHERE AN ORDINAL COMES FROM, and
                  it is a POSITION and not a suffix**: upstream's statement lists its arms
                  in the document's own order, so the Nth arm of their union is the Nth
                  arm of ours, and no digit in any word is read.  A rule that parsed the
                  ``1`` out of ``CreateMediaBuyResponse1`` would be a text match over a
                  spelling their generator chose; this is their own statement of the
                  order.

    A ``TypeAlias`` annotation is the same statement with a type given, so an ``AnnAssign``
    is read exactly as an ``Assign`` -- upstream writes both, and the annotation is about
    the name rather than about the subject.
    """
    aliases: dict[str, str] = {}
    unions: dict[str, list[str]] = {}
    for node in ast.parse(text).body:
        if isinstance(node, ast.Assign):
            if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                continue
            word, value = node.targets[0].id, node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            word, value = node.target.id, node.value
        else:
            continue
        if value is None or word.startswith("_") or word == "model_config":
            continue
        if isinstance(value, ast.Name):
            aliases[word] = value.id
        else:
            arms = _arms_of(value)
            if arms:
                unions[word] = arms
    return {"aliases": aliases, "unions": unions}


def _arms_of(node: ast.expr) -> list[str]:
    """``A | B | C`` as ``["A", "B", "C"]``, or ``[]`` where any arm is not a bare name.

    All-or-nothing on purpose: a union one of whose arms is a subscript or a literal is not
    a list of this module's words, and half of one is not a position table.
    """
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left, right = _arms_of(node.left), _arms_of(node.right)
        return [*left, *right] if left and right else []
    return []


def bind(
    ours: Mapping[str, Mapping[str, Any] | None],
    theirs: Mapping[str, Mapping[str, Any] | None],
    root: str,
    occupied: frozenset[str],
) -> tuple[dict[str, str], dict[str, str]]:
    """``(word -> our symbol, word -> why not)`` for one module.

    **THE POPULATION IS WHAT THE TITLE RULE DOES NOT REACH.**  Our document ROOT is
    excluded from the candidates and a word whose structure IS the root's is refused by
    name, so the two rules partition upstream's surface instead of competing for it: the
    title rule publishes a root's recased spelling by DERIVATION, and this one publishes a
    nested position's word by a join.  That is what keeps ``trusted_match``'s
    ``IdentityMatchResponse`` out -- a parenthesised qualifier is a ROOT question, no rule
    for it exists, and of the 13 documents that have one upstream carries OUR spelling 9
    times.

    **THE MATCH MUST BE UNIQUE AND IS NEVER BROKEN BY A TIE-BREAK.**  Both directions are
    checked: a word reaching several declarations of ours is ``ambiguous``, and so is a
    structure SEVERAL of upstream's words share -- the second is what stops ``Assets`` and
    ``Assets9`` from both landing on one class of ours if a future bundle ever stopped
    distinguishing them.
    """
    candidates: dict[str, list[str]] = {}
    root_keys: set[str] = set()
    for symbol, structure in sorted(ours.items()):
        key = digest(structure)
        if not key:
            continue
        if symbol == root:
            root_keys.add(key)
        else:
            candidates.setdefault(key, []).append(symbol)
    sharing: dict[str, int] = {}
    for structure in theirs.values():
        key = digest(structure)
        if key:
            sharing[key] = sharing.get(key, 0) + 1

    bound: dict[str, str] = {}
    refused: dict[str, str] = {}
    for word, structure in sorted(theirs.items()):
        key = digest(structure)
        if word in occupied:
            refused[word] = "ours-already"
        elif not key:
            refused[word] = "theirs-has-no-structure"
        elif key in root_keys:
            refused[word] = "the-root's-question"
        elif len(candidates.get(key, ())) > 1 or sharing.get(key, 0) > 1:
            refused[word] = "ambiguous"
        elif not candidates.get(key):
            refused[word] = "unmatched"
        else:
            bound[word] = candidates[key][0]
    return bound, refused


def pins_of(blob: Mapping[str, Any] | None) -> dict[str, Any]:
    """``{property: pinned value}`` for one model structure -- the ``const``s it states.

    Read back off :func:`model`'s own element form, so there is no second notion of what a
    pin is: an element whose third slot is non-empty is a pinned property, and the slot is
    the value's canonical JSON.  Used by :func:`bind_statements`' const gate, which is the
    one place a union's ORDER is checked against something the document states.
    """
    if not blob or blob.get("kind") != "model":
        return {}
    return {
        element[0]: json.loads(element[2])
        for element in blob.get("elements", ())
        if len(element) > 2 and element[2] != ""
    }


def bind_statements(
    statements: Mapping[str, Any],
    branches: Sequence[str],
    pins: Mapping[str, Mapping[str, Any]],
    resolved: Mapping[str, str],
    declared: Collection[str],
    occupied: frozenset[str],
) -> tuple[dict[str, str], dict[str, str]]:
    """``(word -> our symbol, word -> why not)`` for upstream's own STATEMENTS of a module.

    Run AFTER :func:`bind`, and handed that join's answer as ``resolved``, because both
    kinds here resolve THROUGH a word the structural join has already decided.  Neither
    reads a letter of any spelling.

    **THE ALIAS KIND IS UPSTREAM'S OWN SENTENCE, FOLLOWED.**  ``Creatives1 = Creative``
    says what ``Creatives1`` denotes; the only question is what ``Creative`` denotes here,
    and that is ``resolved`` or -- where our module declares the word itself -- the word.
    An alias whose target is unbound is refused ``target-unbound`` rather than guessed: a
    statement that is read and still resolves to nothing is not a binding.

    **THE UNION KIND IS A POSITION, GATED TWICE, and the gates are what make a
    mis-ordered union detected instead of mis-bound.**  ``branches`` is OUR root's branch
    order, which is the document's ``oneOf`` order (``ir.ClassDecl.branches``), and
    upstream's statement lists theirs in the same document's order.  So arm *i* pairs with
    arm *i*, and:

    * the two families must list the SAME NUMBER of arms (``arity``), so a union either
      side expanded is refused whole rather than paired as far as it goes; and
    * every property BOTH sides pin a ``const`` on must AGREE (``const-disagrees``), which
      is the discriminator the document states and the one fact a reordering would break.

    ``pins`` is ``word -> {property: const}`` for both sides' arms, keyed by word; a
    property only one side pins is not evidence either way and is skipped, because the two
    generators do not agree about where a discriminator is restated.

    **AN ARM REFUSED BY :func:`bind` ON SHAPE IS STILL BOUND HERE, and that is the point
    of a second key rather than a loosening of the first.**  ``adcp-client-python-eknd``:
    upstream's arms 1 and 3 carry a ``status`` default their own document does not state,
    so their SHAPE differs from ours and :func:`bind` is right to refuse -- shape cannot
    tell "a different subject" from "upstream's generator diverged".  The document's
    position can: the pointer is the same, so the subject is the same, and ours is the one
    that matches the document.  Upstream uses these four only as BASES, so a restored class
    subclasses ours and inherits the requiredness the document states -- stricter than what
    upstream shipped, with nothing weakened.
    """
    bound: dict[str, str] = {}
    refused: dict[str, str] = {}

    def target_of(word: str) -> str | None:
        if word in resolved:
            return resolved[word]
        return word if word in declared else None

    for word, arms in sorted(statements.get("unions", {}).items()):
        # **THE UNION'S OWN WORD BEING TAKEN DOES NOT REFUSE ITS ARMS.**  It usually IS
        # taken -- upstream's union word is the document's root word and our module
        # declares the root -- and treating that as a refusal of the family bound none of
        # the four ordinals on the first run.  The word and the positions are two
        # questions: the word is the root's, which the TITLE rule owns, and the arms are
        # this key's.
        if word not in occupied and word not in resolved:
            refused[word] = "the-root's-question"
        if len(arms) != len(branches):
            for arm in arms:
                refused[arm] = "arity"
            continue
        disagrees = [
            arm
            for arm, ours in zip(arms, branches, strict=True)
            for key in set(pins.get(arm, {})) & set(pins.get(ours, {}))
            if pins[arm][key] != pins[ours][key]
        ]
        if disagrees:
            for arm in arms:
                refused[arm] = "const-disagrees"
            continue
        for arm, ours in zip(arms, branches, strict=True):
            if arm in occupied or arm in resolved:
                refused.setdefault(arm, "ours-already")
            else:
                bound[arm] = ours

    for word, target in sorted(statements.get("aliases", {}).items()):
        if word in occupied or word in resolved or word in bound:
            refused[word] = "ours-already"
            continue
        symbol = target_of(target)
        if symbol is None:
            refused[word] = "target-unbound"
        else:
            bound[word] = symbol
    return bound, refused


def published(path: Path = PUBLISHED) -> dict[str, dict[str, dict[str, Any] | None]]:
    """Upstream's published structures, module by module, from :data:`PUBLISHED`.

    Read ONCE PER RUN by the caller that knows the run (``emit.emit``) and threaded to the
    naming pass, which is ``docs/plan/architecture.md``'s own rule for every set a callee
    needs: "a callee that needs the set of a bundle's documents ... must be TOLD it, not go
    and find it."
    """
    blob: dict[str, Any] = json.loads(path.read_text())
    modules: dict[str, dict[str, dict[str, Any] | None]] = blob["modules"]
    return modules


def published_statements(path: Path = PUBLISHED) -> dict[str, dict[str, Any]]:
    """Upstream's published STATEMENTS, module by module, from :data:`PUBLISHED`.

    :func:`published`'s sibling and deliberately not its contents
    (:func:`statements_from_source`): one answers "what subject did upstream declare here
    and what is its structure", the other "what names did upstream bind to something it had
    already declared".  Read once per run and threaded the same way.

    ``{}`` where the index predates this key, so an index not yet regenerated binds nothing
    rather than failing a run -- the counts in :func:`provenance` are what say which it is.
    """
    blob: dict[str, Any] = json.loads(path.read_text())
    return blob.get("statements") or {}


def provenance(path: Path = PUBLISHED) -> dict[str, Any]:
    """What :data:`PUBLISHED` says it was read from: the revision, the release, the counts.

    **A FIGURE IN THIS FILE IS A CLAIM ABOUT AN ARTIFACT, so the artifact names itself.**
    The gate reports this header beside its own counts, and the index's regeneration
    command rewrites it, so a stale index cannot be quoted as a current measurement.
    """
    blob = json.loads(path.read_text())
    return {k: v for k, v in blob.items() if k != "modules"}
