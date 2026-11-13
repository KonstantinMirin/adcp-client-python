"""What our tree BINDS, read from its source text and never by importing it.

**THE CYCLE WAS A CHOICE AND THIS REMOVES IT RATHER THAN MANAGING IT** (the owner's
reading, which supersedes ``survey/bootstrap.py``'s stubbing).  Three generators asked
*what names does our tree bind* and asked it by ``importlib.import_module("adcp.types")``.
That import resolves through the alias layer -- the very thing they are generating -- so:

* it is a CYCLE: a generator cannot run on a tree whose correct output it is about to
  produce, and it only worked because the previous output happened to import;
* it is also circular REASONING, which is the worse half.  The answer a generator got
  depended on the facade's resolution order, and the facade's resolution order is the
  thing being generated.  So the generator was asking its own output what its output
  should be.

**AND THE QUESTION DOES NOT NEED AN IMPORT.**  The emitted tree is TEXT, and every class
carries its subject in that text::

    class LegacyFormat(AdCPBaseModel):
        __adcp_schema__: ClassVar[SchemaRef] = SchemaRef(document='core/format.json', pointer='#')

So ``(module, class, document, pointer)`` is an AST read.  No import, no stubbing, no
ordering, and the answer is a function of the source rather than of whichever layer
happened to resolve a name first.

Upstream's side still IMPORTS and should: their wheel is installed, nothing we generate
touches it, and their classes carry no ``__adcp_schema__`` for a reader to find.

``survey/bootstrap.py`` is deleted by this: there is nothing to bootstrap once nothing
imports.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

#: The emitted tree and the hand-written surface beside it.  ``_schemas`` is where
#: declarations live; the rest of ``types/`` is where they are re-exported.
TREE = Path("src/adcp/types")


@dataclass(frozen=True)
class Bound:
    """One name a module of ours binds, and the subject it names where it has one."""

    module: str
    name: str
    #: ``(document, pointer)`` from the class's own ``__adcp_schema__``, or ``None`` for a
    #: re-export whose target this module does not declare and for a non-class binding.
    subject: tuple[str, str] | None
    #: Where a re-export points, as ``(module, name)``, or ``None`` for a declaration.
    points_at: tuple[str, str] | None
    declared: bool


def _module_name(path: Path, tree: Path) -> str:
    rel = path.relative_to(tree).with_suffix("")
    parts = [p for p in rel.parts if p != "__init__"]
    return ".".join(["adcp", "types", *parts])


def _schema_ref(body: list[ast.stmt]) -> tuple[str, str] | None:
    """``(document, pointer)`` from a class body's ``__adcp_schema__``, or ``None``.

    Read off the ASSIGNMENT and not off a resolved object, which is the whole point: the
    call is written literally in the source as ``SchemaRef(document='…', pointer='…')``, so
    the two keywords are string constants an AST pass can take.
    """
    for node in body:
        targets = (
            node.targets if isinstance(node, ast.Assign)
            else [node.target] if isinstance(node, ast.AnnAssign)
            else []
        )
        if not any(isinstance(t, ast.Name) and t.id == "__adcp_schema__" for t in targets):
            continue
        call = node.value
        if not isinstance(call, ast.Call):
            continue
        found = {
            kw.arg: kw.value.value
            for kw in call.keywords
            if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str)
        }
        if "document" in found and "pointer" in found:
            return (found["document"], found["pointer"])
    return None


def bindings(tree: Path = TREE) -> list[Bound]:
    """Every module-scope name our tree binds, with its subject where it has one.

    A ``class`` statement is a DECLARATION and carries its own subject.  A
    ``from X import Y as Z`` is a RE-EXPORT and carries where it points; the caller joins
    those to the declarations, which is one pass over this list rather than an import.

    A file that does not parse is SKIPPED and the caller is told by its absence -- the
    same fail-safe direction the importing version took on an ImportError, without the
    import.
    """
    out: list[Bound] = []
    for path in sorted(tree.rglob("*.py")):
        try:
            parsed = ast.parse(path.read_text())
        except SyntaxError:
            continue
        module = _module_name(path, tree)
        for node in parsed.body:
            if isinstance(node, ast.ClassDef):
                out.append(Bound(module, node.name, _schema_ref(node.body), None, True))
            elif isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    out.append(
                        Bound(
                            module,
                            alias.asname or alias.name,
                            None,
                            (node.module, alias.name),
                            False,
                        )
                    )
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith("__"):
                        out.append(Bound(module, target.id, None, None, False))
    return out


def resolved(tree: Path = TREE) -> dict[tuple[str, str], tuple[str, str] | None]:
    """``(module, name) -> (document, pointer)``, with re-exports followed to a declaration.

    Followed through the TEXT, so a chain of re-exports lands on the class that declares
    the subject -- which is what a caller asking "what subject does this word name" wants,
    and is what an import used to answer by resolution order.
    """
    held = bindings(tree)
    declared = {(b.module, b.name): b.subject for b in held if b.declared}
    points = {(b.module, b.name): b.points_at for b in held if b.points_at}
    out: dict[tuple[str, str], tuple[str, str] | None] = dict(declared)
    for key, target in points.items():
        seen = set()
        while target is not None and target not in seen:
            seen.add(target)
            if target in declared:
                out[key] = declared[target]
                break
            target = points.get(target)
        else:
            out.setdefault(key, None)
    return out


def names_of(module: str, tree: Path = TREE) -> set[str]:
    """Every name ``module`` binds -- the question the already-served check asks.

    Asked of the SOURCE, so a word the previous run bound is not mistaken for a word our
    tree genuinely carries.  That mistake is what made ``emit_legacy_names`` report 1,802
    of 1,817 words redundant, and the stubbing that repaired it is unnecessary once the
    question is asked here.
    """
    return {b.name for b in bindings(tree) if b.module == module}
