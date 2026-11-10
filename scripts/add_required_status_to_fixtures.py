"""Give upstream's response fixtures the ``status`` the protocol envelope requires.

``core/protocol-envelope.json`` carries ``required: ["status"]`` and says so in prose:
"The `status` field is REQUIRED on every task response envelope, including synchronous
metadata responses [...] Agents shipping responses without a top-level `status` are
non-conformant regardless of whether the task body schema would otherwise validate."
Every response document composes that envelope through ``allOf``.  Upstream's code
generator dropped allOf-composed required fields, so upstream's own fixtures construct
responses the PROTOCOL rejects, and our schema-derived types correctly refuse them.
Established against the raw documents with ``jsonschema``, not against our own IR --
see commit ``d28f936``, which did six such sites by hand.

**THE POPULATION IS KEYED ON THE RESOLVED CLASS, NEVER ON THE CALLEE'S WORD.**  Walking
``tests/`` for calls whose callee *name* is one of the 383 classes in
``adcp.types._schemas`` with a required ``status`` reports 321 sites across 57 files.
That number is wrong, and wrong by a factor of three, because class names collide across
schemas.  Of those 321:

* 180 resolve to ``adcp.decisioning``'s hand-written ``Account`` / ``MediaBuy`` /
  ``Task``, which are not pydantic models at all.  ``Account`` ALONE accounts for 195
  name matches, and the ``Account`` that requires ``status`` is
  ``account/sync-governance-response.json``'s, whose status enum is
  ``['synced', 'failed']`` -- a different field in a different document.
* 60 resolve to the ``get_adcp_capabilities_response`` sub-models re-exported by
  ``capabilities.py`` (``GetAdCPCapabilitiesResponseMediaBuy`` and friends), which have
  no ``status`` field whatsoever.
* 4 resolve to classes the test file DEFINES itself, shadowing a schema name
  (``tests/type_checks/cross_class_override_with_schema_variant.py``).

So each callee is resolved through its file's own lexical import bindings -- innermost
enclosing scope outward, because these tests import inside the test function -- and the
site counts only when the object that name actually denotes is a pydantic model whose
``status`` field ``is_required()``.  That leaves 106 sites across 24 files.  Nothing is
listed, so a schema bump that adds, drops or renames a response moves through here with
nothing edited.

The value is derived too, from the envelope's own prose and from the loaded field:

* **A single-valued annotation leaves no choice.**  ``UpdateMediaBuyResponse3`` pins
  ``status`` to ``Literal["submitted"]``; ``completed`` would not validate.  Taken from
  the annotation, not from the class's name.
* **A required ``errors`` field marks the rejection arm.**  The envelope: "a
  task-specific rejection arm emits ``status: 'rejected'`` without turning the transport
  into a failure."  ``errors`` being *required* is what distinguishes the error arm of a
  ``oneOf`` from an ordinary response that merely admits warnings, and it picks out
  exactly ``CreateMediaBuyResponse2`` and ``ActivateSignalError``.
* **A non-empty ``errors=`` argument marks a failure.**  The envelope's own example
  "Failed task response with error details" is a payload ``errors[]`` under
  ``status: "failed"``.  ``errors=None`` is not that, so the test is on the argument's
  value and not on its presence.
* Otherwise ``completed``, which the envelope calls the normal synchronous value.

**A SITE WHOSE TEST READS ``.status`` BACK IS NOT TOUCHED.**  Several fixtures exist to
assert that ``status`` is *defaulted* -- ``test_canonical_responses_construct_without_status``
and the "``status`` is defaulted, so construction must not demand it" section of
``tests/type_checks/response_envelope_fields.py``.  Supplying the field there would turn
``assert buys.status == "completed"`` into a tautology and erase a real disagreement
between upstream's contract and the document, so the rewrite skips any site whose
enclosing scope reads ``.status`` off the name it binds, and prints them instead.

Out of scope, deliberately: the other required fields upstream's generator also dropped
(``type``, ``mode``, ``estimate``, ``creatives``, ``asset_type``).  Each needs a real
per-case value where ``status`` has a neutral one, so a site needing both still fails
after this runs -- which is the honest outcome, not a regression.

Run ``--check`` to print the plan and touch nothing.
"""

from __future__ import annotations

import argparse
import ast
import collections
import enum
import importlib
import pathlib
import sys
import typing

import pydantic

ROOT = pathlib.Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"

#: Scopes that can carry an import binding. ``Module`` is the outermost.
SCOPES = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)

#: The envelope's normal synchronous value, per ``core/protocol-envelope.json``.
NEUTRAL = "completed"

#: ``line-length`` in ``pyproject.toml``, which governs ruff and black alike. Six of the
#: single-line fixtures do not fit the extra keyword, so those calls are exploded one
#: argument per line rather than left as a new E501 for someone else to find.
LIMIT = 100

#: Why the field appears, recorded at every site the way ``d28f936`` recorded its six.
BASE_REASON = (
    "`status` is required by core/protocol-envelope.json, which this",
    "document composes via allOf. Upstream's generator dropped",
    "allOf-composed required fields, so their fixtures omit it.",
)


def requires_status(obj: object) -> bool:
    """Is ``obj`` a model the protocol envelope's ``status`` is required on?"""
    if not (isinstance(obj, type) and issubclass(obj, pydantic.BaseModel)):
        return False
    field = obj.model_fields.get("status")
    return field is not None and field.is_required()


def permitted(model: type[pydantic.BaseModel]) -> list[str]:
    """Every value ``model.status`` admits, read off the loaded annotation."""
    annotation = model.model_fields["status"].annotation
    if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
        return [str(member.value) for member in annotation]
    out: list[str] = []
    for arg in typing.get_args(annotation):
        if isinstance(arg, enum.Enum):
            out.append(str(arg.value))
        elif isinstance(arg, str):
            out.append(arg)
        elif isinstance(arg, type) and issubclass(arg, enum.Enum):
            out.extend(str(member.value) for member in arg)
    return out


def scope_bindings(scope: ast.AST) -> dict[str, tuple[str, str | None]]:
    """``name -> (module, attribute)`` for imports bound DIRECTLY in one scope.

    Nested scopes are skipped, so the caller can walk outward and let an inner
    ``from adcp.decisioning import Account`` shadow an outer ``from adcp.types import
    Account``. Both spellings occur in the same file, which is why this cannot be a
    flat per-file map.
    """
    out: dict[str, tuple[str, str | None]] = {}

    def walk(statements: list[ast.stmt]) -> None:
        for statement in statements:
            if isinstance(statement, ast.ImportFrom):
                if statement.level or statement.module is None:
                    continue  # relative import: not resolvable by module name alone
                for alias in statement.names:
                    out[alias.asname or alias.name] = (statement.module, alias.name)
            elif isinstance(statement, ast.Import):
                for alias in statement.names:
                    if alias.asname:
                        out[alias.asname] = (alias.name, None)
                    else:
                        head = alias.name.split(".")[0]
                        out[head] = (head, None)
            elif isinstance(statement, SCOPES):
                continue  # a nested scope's bindings are not this scope's
            else:
                for _, value in ast.iter_fields(statement):
                    if isinstance(value, list):
                        walk([v for v in value if isinstance(v, ast.stmt)])
                    elif isinstance(value, ast.stmt):
                        walk([value])

    walk(getattr(scope, "body", []))
    return out


class Resolver:
    """Resolves a callee to the object it denotes, through one file's imports."""

    def __init__(self, tree: ast.Module) -> None:
        self.parent: dict[ast.AST, ast.AST] = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                self.parent[child] = node
        self.cache: dict[ast.AST, dict[str, tuple[str, str | None]]] = {}

    def binding(self, node: ast.AST, name: str) -> tuple[str, str | None] | None:
        scope: ast.AST | None = node
        while scope is not None:
            if isinstance(scope, SCOPES):
                if scope not in self.cache:
                    self.cache[scope] = scope_bindings(scope)
                if name in self.cache[scope]:
                    return self.cache[scope][name]
            scope = self.parent.get(scope)
        return None

    def callee(self, call: ast.Call) -> object | None:
        """The object ``call.func`` denotes, or ``None`` when it is not an import."""
        func = call.func
        if isinstance(func, ast.Name):
            found = self.binding(call, func.id)
        elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            base = self.binding(call, func.value.id)
            if base is None:
                return None
            module = base[0] if base[1] is None else f"{base[0]}.{base[1]}"
            found = (module, func.attr)
        else:
            return None
        if found is None:
            return None
        module_name, attribute = found
        try:
            module = importlib.import_module(module_name)
        except Exception:
            return None
        return module if attribute is None else getattr(module, attribute, None)

    def enclosing_scope(self, node: ast.AST) -> ast.AST | None:
        scope: ast.AST | None = self.parent.get(node)
        while scope is not None and not isinstance(scope, SCOPES):
            scope = self.parent.get(scope)
        return scope


def bound_name(resolver: Resolver, call: ast.Call) -> str | None:
    """The single name ``call``'s result is assigned to, if it is assigned at all."""
    parent = resolver.parent.get(call)
    if isinstance(parent, ast.Assign) and len(parent.targets) == 1:
        target = parent.targets[0]
        if isinstance(target, ast.Name):
            return target.id
    if isinstance(parent, ast.AnnAssign) and isinstance(parent.target, ast.Name):
        return parent.target.id
    return None


def reads_status_back(resolver: Resolver, call: ast.Call) -> bool:
    """Does the enclosing scope read ``.status`` off the name this call binds?

    That makes ``status`` the test's SUBJECT rather than a field it forgot, and
    supplying it would make the test's own assertion vacuous.
    """
    name = bound_name(resolver, call)
    scope = resolver.enclosing_scope(call)
    if name is None or scope is None:
        return False
    for node in ast.walk(scope):
        if (
            isinstance(node, ast.Attribute)
            and node.attr == "status"
            and isinstance(node.value, ast.Name)
            and node.value.id == name
        ):
            return True
    return False


def chosen_status(model: type[pydantic.BaseModel], call: ast.Call) -> tuple[str, str | None]:
    """``(value, extra reason)`` for one site, derived from the model and the call."""
    allowed = permitted(model)
    if len(allowed) == 1:
        return allowed[0], (
            f"This arm pins `status` to the single member `{allowed[0]}`, so"
            " the neutral value would not validate."
        )

    errors = model.model_fields.get("errors")
    if errors is not None and errors.is_required() and "rejected" in allowed:
        return "rejected", (
            "`errors` is REQUIRED here, which marks the rejection arm of the"
            " oneOf; the envelope says such an arm emits `rejected`."
        )

    for keyword in call.keywords:
        if keyword.arg != "errors":
            continue
        value = keyword.value
        empty = isinstance(value, ast.Constant) and value.value is None
        empty = empty or (isinstance(value, (ast.List, ast.Tuple)) and not value.elts)
        if not empty and "failed" in allowed:
            return "failed", (
                "This construction passes a non-empty `errors[]`, which is the"
                " envelope's own 'Failed task response with error details'."
            )

    return NEUTRAL, None


class Site(typing.NamedTuple):
    line: int
    end_line: int
    paren_column: int
    end_column: int
    arguments: tuple[tuple[int, int], ...]
    single_line: bool
    callee: str
    model: str
    value: str
    extra: str | None


def sites(path: pathlib.Path) -> tuple[list[Site], list[str]]:
    """Every construction in ``path`` missing ``status``, and the skipped subjects."""
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return [], []
    resolver = Resolver(tree)
    found: list[Site] = []
    skipped: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        model = resolver.callee(node)
        if not requires_status(model):
            continue
        model = typing.cast("type[pydantic.BaseModel]", model)
        keywords = {keyword.arg for keyword in node.keywords}
        if "status" in keywords or None in keywords:
            continue  # already supplied, or forwarded through **kwargs
        spelling = ast.unparse(node.func)
        if reads_status_back(resolver, node):
            skipped.append(f"{path.relative_to(ROOT)}:{node.lineno} {spelling}")
            continue
        value, extra = chosen_status(model, node)
        found.append(
            Site(
                line=node.lineno,
                end_line=node.end_lineno or node.lineno,
                paren_column=node.func.end_col_offset or 0,
                end_column=node.end_col_offset or 0,
                # Positional args too, in source order: exploding a call must not
                # drop an argument the author wrote, even though no fixture in the
                # current population passes one.
                arguments=tuple(
                    sorted(
                        (argument.col_offset, argument.end_col_offset or 0)
                        for argument in (*node.args, *node.keywords)
                    )
                ),
                single_line=node.lineno == (node.end_lineno or node.lineno),
                callee=spelling,
                model=f"{model.__module__}.{model.__qualname__}",
                value=value,
                extra=extra,
            )
        )
    return found, skipped


def indent_of(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


def apply(lines: list[str], site: Site) -> list[str]:
    """Insert ``status=`` into one call, with its reason above the statement."""
    reason = [*BASE_REASON]
    if site.extra:
        words = site.extra.split()
        current = ""
        for word in words:
            if len(current) + len(word) + 1 > 66:
                reason.append(current)
                current = word
            else:
                current = f"{current} {word}".strip()
        if current:
            reason.append(current)

    head = site.line - 1
    pad = indent_of(lines[head])
    comment = [f"{pad}# {text}" for text in reason]

    if site.single_line:
        column = site.paren_column
        text = lines[head]
        assert text[column] == "(", text  # ``func(`` -- the paren follows the callee
        rest = text[column + 1 :]
        # ``Response()`` takes no separator and no trailing comma; ``Response(x=1)``
        # takes both. Getting this wrong is what black would otherwise rewrite.
        tail = "" if rest.startswith(")") else ", "
        inline = f'{text[: column + 1]}status="{site.value}"{tail}{rest}'
        if len(inline) <= LIMIT:
            lines[head] = inline
        else:
            inner = pad + "    "
            arguments = [f'{inner}status="{site.value}",']
            arguments += [f"{inner}{text[start:end]}," for start, end in site.arguments]
            lines[head : head + 1] = [
                text[: column + 1],
                *arguments,
                f"{pad}{text[site.end_column - 1 :]}",
            ]
    else:
        inner = indent_of(lines[head + 1]) if len(lines) > head + 1 else pad + "    "
        lines.insert(head + 1, f'{inner}status="{site.value}",')
    lines[head:head] = comment
    return lines


def reformat(paths: list[pathlib.Path]) -> None:
    """Hand the edited files to the repository's own black, at its own settings.

    Inserting a first argument into a call changes what black wants of the LAST one
    (a magic trailing comma it did not need while the argument was alone), and an
    exploded nested call is a shape black re-indents from the outside in. Replicating
    that here would be a second formatter to keep in step with ``[tool.black]``, so
    the one in ``pyproject.toml`` is asked instead.
    """
    try:
        import black
    except ImportError:
        print("black is not importable -- run `black` over the edited files", file=sys.stderr)
        return
    mode = black.Mode(line_length=LIMIT, target_versions={black.TargetVersion.PY310})
    for path in paths:
        source = path.read_text(encoding="utf-8")
        try:
            formatted = black.format_file_contents(source, fast=False, mode=mode)
        except black.NothingChanged:
            continue
        path.write_text(formatted, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="print the plan, write nothing")
    arguments = parser.parse_args()

    plan: dict[pathlib.Path, list[Site]] = {}
    skipped: list[str] = []
    for path in sorted(TESTS.rglob("*.py")):
        found, subject = sites(path)
        skipped.extend(subject)
        if found:
            plan[path] = found

    if not plan and not skipped:
        print("no construction is missing the envelope's `status`", file=sys.stderr)
        return 1

    counts: collections.Counter[str] = collections.Counter()
    for found in plan.values():
        counts.update(site.value for site in found)
    total = sum(counts.values())
    print(f"{total} constructions across {len(plan)} files are missing `status`:")
    for value, count in sorted(counts.items(), key=lambda item: -item[1]):
        print(f"    {count:4d}  status={value!r}")

    if skipped:
        print(f"\n{len(skipped)} sites SKIPPED -- the test reads `.status` back, so the")
        print("field is its subject and supplying it would make the assertion vacuous:")
        for entry in skipped:
            print(f"    {entry}")

    for path, found in plan.items():
        print(f"\n  {path.relative_to(ROOT)}")
        for site in sorted(found):
            note = f"  ({site.extra.split('.')[0]}.)" if site.extra else ""
            print(f"    L{site.line:<5} {site.callee:<34} status={site.value!r}{note}")
        if arguments.check:
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        for site in sorted(found, reverse=True):
            lines = apply(lines, site)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if not arguments.check:
        reformat(list(plan))

    verb = "would add" if arguments.check else "added"
    print(f"\n{verb} `status` at {total} sites across {len(plan)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
