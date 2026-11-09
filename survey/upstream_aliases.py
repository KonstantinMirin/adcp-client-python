"""**UPSTREAM'S OWN SOURCE IS THE ORACLE FOR A NAME IT BINDS RATHER THAN DECLARES.**

`survey/adapter_surface.py` answers "which subject of ours does an upstream name denote" by
reading upstream's RUNTIME dump: a class carries its declaring module in `__module__` and its
word in `__qualname__`, and that module's path IS a bundle document's path.  That reading is
exact and it has one blind spot, which this module is the whole of:

    a name upstream BINDS rather than DECLARES has no `__module__` to read.

Measured on upstream's 9.6.1 wheel: `adcp.types.legacy.LegacyCreateMediaBuyResponse` is a
union `TypeAlias`, so the runtime dump records no declaring module for it and the adapter
table's verdict was `NO-DOCUMENT-NO-SUBJECT` -- while upstream's own `legacy.py` says, in one
statement, exactly which document it is::

    legacy.py:85   from adcp.types.domains.media_buy.create_media_buy_response import (
                       CreateMediaBuyResponse as LegacyCreateMediaBuyResponse)

So the binding is READ and never guessed, and it is read from the one source that cannot be
wrong about it.  Measured by `--report` over upstream's hand-written type layer at the commit
`survey/upstream-machinery-9.6.1.tsv` names: **283 statements of the form `X as Y`, 230
`Y = X` renames and 209 `Y: TypeAlias = <expression>`**, over 15,223 module-scope bindings in
that layer and 33,187 across their whole `types/` tree.  This module extracts all of them
with `ast`, follows the chain, and reports the TERMINAL -- the statement past which upstream's
own tree says nothing more.

**THERE IS NO LIST OF NAMES HERE.**  A hand-typed map of the names today's census happens to
ask for goes stale on the first version bump, and the whole point of the exercise is that
upstream's source states the answer: the population is every module-scope binding in their
tree, and the rev is the one the machinery classification already pins
(`survey/upstream_machinery.rows`) rather than a second commit spelled here.

**THE TERMINAL IS A FACT ABOUT UPSTREAM AND NEVER A CLAIM ABOUT US.**  This module resolves
`Y` to upstream's own `X` and stops.  Which subject of OURS `X` denotes is
`survey/adapter_surface.Join`'s question, decided by the document and the node and never by
the spelling -- so a terminal landing in `adcp.types.domains.<document>` hands that instrument
a DOCUMENT and a WORD, which is the input its eleven keys already take.  Nothing here reads
one letter of our tree.

Five terminal kinds, each a different fact and each needing a different answer upstream:

    declared-class      upstream declares it with a `class` statement.  The strong case: the
                        module is a document's and the word is their generator's, which is
                        `Join`'s own key.
    declared-function   a `def`.  Not a type at all, so not an adapter's to serve
                        (`validate_union`, `project_geo_postal_areas`).
    expression          `Y: TypeAlias = <expr>`.  NOT a rename -- the expression has to be
                        ported, so :attr:`Terminal.arms` and
                        :attr:`Terminal.discriminator` report what it is made of and the
                        caller decides whether its parts resolve.
    absent              upstream's module exists and binds no such name.  The honest
                        remainder: `AcceptedLoss` is in no statement of their type layer.
    no-such-module      upstream's tree holds no such module either.

::

    PYTHONPATH=.:src ./.venv/bin/python survey/upstream_aliases.py --report
    PYTHONPATH=.:src ./.venv/bin/python survey/upstream_aliases.py \
        --trace adcp.types.legacy.LegacyCreateMediaBuyResponse
"""

from __future__ import annotations

import argparse
import ast
import collections
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import upstream_machinery as um  # noqa: E402

#: The subtree of upstream's that holds their type layer, and the only one read here.
TREE = "src/adcp/types"

#: Their GENERATED package, whose module path is a bundle document's path -- the one terminal
#: location that hands `adcp.types.domains.<document>` to a caller as a document and a word.
THEIR_GEN = "adcp.types.domains"

#: **UPSTREAM'S FLAT NAMESPACE IS SERVED BY A CHAIN AND THE CHAIN IS THEIRS.**  Their
#: `__init__` is a PEP 562 facade whose `__getattr__` imports `_eager`, which binds every
#: public name, largely from `_generated`.  So `from adcp.types import X` is three statements
#: of theirs and not one, and a lookup that stopped at `__init__` would report 48 of the names
#: upstream's own suite imports as absent when their tree states each one.  Read in order, so
#: a name `__init__` binds itself is never overridden by `_generated`'s.
FLAT = ("adcp.types", "adcp.types._eager", "adcp.types._generated")

#: How far a chain may be followed before it is reported as a defect rather than traversed.
#: Measured: the longest real chain in their 9.6.1 tree is six statements
#: (`adcp.types` -> `_eager` -> `_generated` -> `domains.<doc>`, with two renames on the way),
#: so this is an order of magnitude of headroom and not a tuned number.
DEPTH = 24


@dataclass(frozen=True)
class Statement:
    """One module-scope statement of upstream's that BINDS a name, as their file states it."""

    kind: str
    module: str
    name: str
    line: int
    ref_module: str = ""
    ref_word: str = ""
    annotation: str = ""
    expression: str = ""

    def __str__(self) -> str:
        where = f"{self.module.rpartition('.')[2]}.py:{self.line}"
        if self.kind in ("import", "import-as"):
            tail = f"{self.ref_word} as {self.name}" if self.kind == "import-as" else self.name
            return f"{where}  from {self.ref_module} import {tail}"
        if self.kind in ("class", "function"):
            keyword = "class" if self.kind == "class" else "def"
            return f"{where}  {keyword} {self.name}"
        return f"{where}  {self.name} = {self.expression or self.ref_word}"


@dataclass(frozen=True)
class Terminal:
    """What upstream's own tree says a name finally IS, and nothing about what ours holds."""

    kind: str
    module: str = ""
    name: str = ""
    line: int = 0
    expression: str = ""
    #: The bare arm NAMES of a union expression, in the order upstream wrote them, resolved
    #: in :attr:`module`'s own namespace.  Empty where the expression is not a union.
    arms: tuple[str, ...] = ()
    #: The discriminator upstream's `Annotated` metadata pins, if any.  **Reported and never
    #: dropped**: a discriminated union and the bare `A | B` under it are different admissible
    #: sets, so a caller porting the expression has to decide about it rather than not see it.
    discriminator: str = ""
    #: True where the expression carries `Annotated` metadata of any kind -- a `Discriminator`,
    #: a `Tag`, a `Field(...)`, a validator.  The one screen a plain-union port needs.
    annotated: bool = False

    @property
    def document(self) -> str:
        """The bundle document upstream's terminal module names, dotted, or ``""``."""
        if not self.module.startswith(THEIR_GEN + "."):
            return ""
        return self.module[len(THEIR_GEN) + 1 :]

    @property
    def family_stem(self) -> str:
        """The common stem where every arm is ``<stem><N>`` -- their generator's own suffix.

        `CreateMediaBuyResponse1 | CreateMediaBuyResponse2 | CreateMediaBuyResponse3` is how
        their generator spells a document's ROOT UNION, and the stem is the root's word.  The
        stem is all this reports; whether it IS that document's root is a question about the
        document, answered where the document is known.
        """
        if not self.arms:
            return ""
        stems = {re.sub(r"\d+$", "", arm) for arm in self.arms}
        if len(stems) != 1 or not all(re.fullmatch(r".*\d+", arm) for arm in self.arms):
            return ""
        return stems.pop()


def _dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return f"{base}.{node.attr}" if base else ""
    return ""


def _module_scope(tree: ast.Module) -> list[ast.stmt]:
    """Every statement that RUNS when the module is imported, flattened.

    The same reading `survey/adapter_surface.module_scope_imports` takes and for the same
    reason: a top-level `if TYPE_CHECKING:`, `try:`/`except ImportError:` or `with` executes
    as the module body runs, so a binding inside one is a binding the module makes.  Measured
    on their tree: `_eager.py` keeps 19 of its renames inside a guarded block.
    """
    out: list[ast.stmt] = []

    def walk(body: list[ast.stmt]) -> None:
        for node in body:
            if isinstance(
                node,
                (
                    ast.ImportFrom,
                    ast.Assign,
                    ast.AnnAssign,
                    ast.ClassDef,
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            ):
                out.append(node)
            elif isinstance(node, (ast.If, ast.Try, ast.With, ast.For, ast.While)):
                for attr in ("body", "orelse", "finalbody"):
                    walk(getattr(node, attr, None) or [])
                for handler in getattr(node, "handlers", None) or []:
                    walk(handler.body)

    walk(tree.body)
    return out


def _arms(value: ast.expr) -> tuple[tuple[str, ...], str, bool]:
    """The arm names, the discriminator and whether `Annotated` metadata is present.

    **THE METADATA IS READ, NOT SKIPPED.**  `Discriminator("asset_type")` is a POSITIONAL
    call and `Field(discriminator="scope")` is a keyword one, and a reader that looked only
    at keywords reported upstream's `AssetInstance` as a plain twenty-arm union when their
    `aliases.py:383` pins a discriminator on it -- which would have ported a different
    admissible set under their name.  Both forms are read, and :attr:`Terminal.annotated`
    says "there was metadata here" even where neither form is recognised, so the screen a
    caller applies is "upstream wrote a bare union" and not "I found nothing I understood".
    """
    names: list[str] = []
    discriminator = ""
    annotated = False

    def unwrap(node: ast.expr) -> None:
        nonlocal discriminator, annotated
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            unwrap(node.left)
            unwrap(node.right)
            return
        if isinstance(node, ast.Subscript) and _dotted(node.value).lstrip("_").endswith(
            "Annotated"
        ):
            held = node.slice
            parts = list(held.elts) if isinstance(held, ast.Tuple) else [held]
            unwrap(parts[0])
            annotated = annotated or len(parts) > 1
            for extra in parts[1:]:
                if not isinstance(extra, ast.Call):
                    continue
                called = _dotted(extra.func).rpartition(".")[2].lstrip("_")
                if called == "Discriminator" and extra.args:
                    first = extra.args[0]
                    if isinstance(first, ast.Constant) and isinstance(first.value, str):
                        discriminator = first.value
                for keyword in extra.keywords:
                    if keyword.arg == "discriminator" and isinstance(keyword.value, ast.Constant):
                        discriminator = str(keyword.value.value)
            return
        if isinstance(node, ast.Name):
            names.append(node.id)
            return
        # Anything else -- a `Literal[...]`, a call, a subscript we do not read -- is not an
        # arm, and saying so by its node type is what keeps a partial reading visible.
        names.append("?" + type(node).__name__)

    unwrap(value)
    return tuple(names), discriminator, annotated


@dataclass
class Oracle:
    """Upstream's whole type layer at one commit, as the statements it binds names with."""

    rev: str
    root: Path
    bindings: dict[tuple[str, str], Statement] = field(default_factory=dict)
    modules: set[str] = field(default_factory=set)

    @classmethod
    def at(cls, rev: str | None = None, scratch: Path | None = None) -> Oracle:
        """Extract `src/adcp/types` at `rev` and parse it.

        The rev defaults to the one `survey/upstream-machinery-9.6.1.tsv` names in its own
        header, which is the commit the restored machinery is already measured against --
        one pin for the whole project, so the alias layer and the restore cannot come to be
        about two different upstreams.

        **THE EXTRACTION IS CACHED UNDER THE REV, which is correctness and not speed.**  A
        fresh `mkdtemp` per call leaves one copy of their 1,137-file tree behind per run,
        and `/tmp` here is a tmpfs with a million inodes: eleven runs of this instrument
        exhausted them and the twelfth `tar` failed with "No space left on device" mid-tree
        -- a half-extracted tree is an ORACLE THAT SILENTLY ANSWERS `absent`, which is the
        one failure mode this module must not have.  Keyed on the rev, so the bytes under
        the path are the bytes that rev names, and re-extracted when the marker is missing.
        """
        rev = rev or um.rows()[0]
        root = Path(scratch) if scratch else Path(tempfile.gettempdir()) / f"adcp-upstream-{rev}"
        marker = root / ".complete"
        if not marker.is_file():
            archive = subprocess.run(
                ["git", "archive", rev, "--", TREE],
                cwd=HERE.parent,
                capture_output=True,
                check=True,
            ).stdout
            root.mkdir(parents=True, exist_ok=True)
            subprocess.run(["tar", "-x", "-C", str(root)], input=archive, check=True)
            marker.write_text(rev)
        out = cls(rev=rev, root=root / TREE)
        out.read()
        return out

    def module_name(self, path: Path) -> str:
        rel = path.relative_to(self.root).with_suffix("")
        return ".".join(["adcp", "types", *(p for p in rel.parts if p != "__init__")])

    def read(self) -> None:
        """Every module-scope binding of upstream's tree, keyed by `(module, bound name)`.

        `setdefault` and not assignment: where a module binds one name twice the FIRST
        statement is the one the import machinery runs, and a last-wins reading reported
        their `_eager`'s re-export as the definition of a name `__init__` had already bound.
        """
        for path in sorted(self.root.rglob("*.py")):
            module = self.module_name(path)
            self.modules.add(module)
            here = module.split(".")
            try:
                tree = ast.parse(path.read_text())
            except SyntaxError:  # pragma: no cover -- their tree parses on 3.10+
                continue
            for node in _module_scope(tree):
                if isinstance(node, ast.ClassDef):
                    self._bind(Statement("class", module, node.name, node.lineno))
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self._bind(Statement("function", module, node.name, node.lineno))
                elif isinstance(node, ast.ImportFrom):
                    source = node.module or ""
                    if node.level:
                        base = here[: len(here) - node.level]
                        source = ".".join([*base, source]) if source else ".".join(base)
                    for alias in node.names:
                        if alias.name == "*":
                            continue
                        bound = alias.asname or alias.name
                        self._bind(
                            Statement(
                                "import-as" if bound != alias.name else "import",
                                module,
                                bound,
                                node.lineno,
                                ref_module=source,
                                ref_word=alias.name,
                            )
                        )
                elif node.value is not None:
                    targets = (
                        [node.target] if isinstance(node, ast.AnnAssign) else list(node.targets)
                    )
                    reference = _dotted(node.value)
                    for target in targets:
                        if not isinstance(target, ast.Name):
                            continue
                        self._bind(
                            Statement(
                                "assign-name" if reference else "assign-expression",
                                module,
                                target.id,
                                node.lineno,
                                ref_word=reference,
                                annotation=(
                                    _dotted(node.annotation)
                                    if isinstance(node, ast.AnnAssign)
                                    else ""
                                ),
                                expression=ast.unparse(node.value),
                            )
                        )

    def _bind(self, statement: Statement) -> None:
        self.bindings.setdefault((statement.module, statement.name), statement)

    def statement(self, module: str, name: str) -> Statement | None:
        """The statement upstream binds `name` with in `module`, following their flat chain."""
        held = self.bindings.get((module, name))
        if held is not None:
            return held
        if module == "adcp.types":
            for alternative in FLAT[1:]:
                held = self.bindings.get((alternative, name))
                if held is not None:
                    return held
        return None

    def referent(self, module: str, reference: str) -> tuple[str, str]:
        """``(module, name)`` for a dotted reference, with its HEAD resolved locally.

        **A MODULE ALIAS IS A LOCAL NAME AND NOT A MODULE PATH**, which is where a reader
        that split on the last dot goes wrong.  Their `_eager.py:40` writes
        `from adcp.types import canonical_creative as _canonical_creative` and then
        `_eager.py:931` writes
        `CreateMediaBuySuccessResponse = _canonical_creative.CreateMediaBuyResponse1`; split
        naively, the module is `_canonical_creative`, which is no module of theirs at all --
        so eight names their own suite imports came back `no-such-module` when their tree
        states each one, and three of those are the `<Verb>SuccessResponse` family another
        lane is measuring as a suffix problem.  The head is therefore looked up in the
        module's own bindings first, which is what the import system does.
        """
        head, _, tail = reference.partition(".")
        if not tail:
            return module, reference
        held = self.statement(module, head)
        if held is not None and held.kind in ("import", "import-as"):
            candidate = f"{held.ref_module}.{held.ref_word}"
            if candidate in self.modules:
                return candidate, tail
        return reference.rpartition(".")[0], reference.rpartition(".")[2]

    def trace(self, module: str, name: str) -> tuple[Terminal, tuple[Statement, ...]]:
        """Follow upstream's own statements to the terminal, and report the whole chain.

        The chain is returned because it is the EVIDENCE: a row bound through this oracle
        says which file and line of upstream's stated it, so the binding can be read back
        rather than trusted.
        """
        chain: list[Statement] = []
        seen: set[tuple[str, str]] = set()
        current = (module, name)
        for _ in range(DEPTH):
            if current in seen:
                return Terminal("cycle", *current), tuple(chain)
            seen.add(current)
            held = self.statement(*current)
            if held is None:
                kind = "absent" if current[0] in self.modules else "no-such-module"
                return Terminal(kind, *current), tuple(chain)
            chain.append(held)
            if held.kind in ("class", "function"):
                return (
                    Terminal("declared-" + held.kind, held.module, held.name, held.line),
                    tuple(chain),
                )
            if held.kind == "assign-expression":
                arms, discriminator, annotated = _arms(ast.parse(held.expression, mode="eval").body)
                return (
                    Terminal(
                        "expression",
                        held.module,
                        held.name,
                        held.line,
                        expression=held.expression,
                        arms=arms,
                        discriminator=discriminator,
                        annotated=annotated,
                    ),
                    tuple(chain),
                )
            if held.kind == "assign-name":
                current = self.referent(held.module, held.ref_word)
            else:
                #: **A SUBMODULE IMPORT IS A MODULE AND NOT A NAME.**  Their `__init__` writes
                #: `from adcp.types import aliases`, and a lookup that recursed on the WORD
                #: came back to the same pair and reported a cycle -- which is a defect in the
                #: reader, not in their tree.  A module is a terminal of its own kind, because
                #: no subject of ours is one and the caller has to be told that rather than
                #: handed a false `absent`.
                submodule = f"{held.ref_module}.{held.ref_word}"
                if submodule in self.modules:
                    return Terminal("module", submodule), tuple(chain)
                current = (held.ref_module, held.ref_word)
        return Terminal("too-deep", *current), tuple(chain)  # pragma: no cover


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--rev", default=None)
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--trace", action="append", default=[], metavar="MODULE.NAME")
    args = parser.parse_args()

    oracle = Oracle.at(args.rev)
    if args.report or not args.trace:
        kinds = collections.Counter(s.kind for s in oracle.bindings.values())
        hand = {
            k: v
            for k, v in oracle.bindings.items()
            if not k[0].startswith(THEIR_GEN + ".") and k[0] != THEIR_GEN
        }
        print(f"upstream {oracle.rev}: {len(oracle.modules)} modules of their type layer")
        print(f"  module-scope bindings            {len(oracle.bindings)}")
        for kind, n in kinds.most_common():
            print(f"      {kind:20} {n}")
        print(f"  in their HAND-WRITTEN layer      {len(hand)}")
        for kind, n in collections.Counter(s.kind for s in hand.values()).most_common():
            print(f"      {kind:20} {n}")
        renames = [s for s in hand.values() if s.kind == "import-as"]
        print(f"  'X as Y' renames                 {len(renames)}")
        for module, n in collections.Counter(s.module for s in renames).most_common(8):
            print(f"      {n:5} {module}")
    for spelling in args.trace:
        module, _, name = spelling.rpartition(".")
        terminal, chain = oracle.trace(module, name)
        print(f"\n{spelling}")
        for statement in chain:
            print(f"    {statement}")
        print(f"  -> {terminal.kind} {terminal.module}.{terminal.name}")
        if terminal.kind == "expression":
            print(f"     document={terminal.document!r} stem={terminal.family_stem!r}")
            print(f"     arms={list(terminal.arms)} discriminator={terminal.discriminator!r}")


if __name__ == "__main__":
    main()
