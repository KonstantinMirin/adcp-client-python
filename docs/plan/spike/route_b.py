"""Route B: emit Python directly from the schema dict. No dmcg. Everything the
library would have supplied (constraint spelling, imports, class ordering,
formatting) is written here."""

from __future__ import annotations

import sys
from pathlib import Path

SCALAR = {"string": "str", "number": "float", "integer": "int", "boolean": "bool"}
# JSON Schema keyword -> pydantic Field kwarg. The alias table dmcg carries.
CONSTRAINTS = {
    "minimum": "ge", "maximum": "le", "exclusiveMinimum": "gt", "exclusiveMaximum": "lt",
    "multipleOf": "multiple_of", "minItems": "min_length", "maxItems": "max_length",
    "minLength": "min_length", "maxLength": "max_length", "pattern": "pattern",
}


def pascal(title: str) -> str:
    return "".join(w[:1].upper() + w[1:] for w in title.split())


def field_line(name: str, schema: dict, *, required: bool) -> str:
    kwargs = [f"{CONSTRAINTS[k]}={v!r}" for k, v in schema.items() if k in CONSTRAINTS]
    ann = SCALAR[schema["type"]]
    if kwargs:
        ann = f"Annotated[{ann}, Field({', '.join(kwargs)})]"
    if required:
        return f"    {name}: {ann}"
    return f"    {name}: {ann} | None = None"


def emit_object(schema: dict, *, name: str | None = None, base: str = "BaseModel",
                only: set[str] | None = None, required: list[str] | None = None) -> str:
    props = {k: v for k, v in schema.get("properties", {}).items() if only is None or k in only}
    req = required if required is not None else schema.get("required", [])
    lines = [f"class {name or pascal(schema['title'])}({base}):"]
    if schema.get("additionalProperties") is False and base == "BaseModel":
        lines.append("    model_config = ConfigDict(extra='forbid')")
    lines += [field_line(k, v, required=k in req) for k, v in props.items()] or ["    pass"]
    return "\n".join(lines)


def emit_enum(schema: dict) -> str:
    lines = [f"class {pascal(schema['title'])}(str, Enum):"]
    lines += [f"    {v} = {v!r}" for v in schema["enum"]]
    return "\n".join(lines)


ONE_OF_RULE = '''
    @model_validator(mode="after")
    def _one_of_required_groups(self):
        groups = {groups}
        present = {{k for k in self.model_fields_set}}
        if sum(all(n in present for n in g) for g in groups) != 1:
            raise ValueError("exactly one of the required groups must be present: " + repr(groups))
        return self'''


def emit_union_with_base(schema: dict) -> list[str]:
    base_name = pascal(schema["title"])
    groups = tuple(tuple(arm["required"]) for arm in schema["oneOf"])
    out = [emit_object(schema, required=[]) + ONE_OF_RULE.format(groups=groups)]
    names = []
    for arm in schema["oneOf"]:
        names.append(pascal(arm["title"]))
        out.append(emit_object(schema, name=names[-1], base=base_name,
                               only=set(arm["required"]), required=arm["required"]))
    out.append(f"{base_name}Branches = {' | '.join(names)}")
    return out


HEADER = """from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator
"""


def main() -> str:
    sys.path.insert(0, str(Path(__file__).parent))
    from cases import ACCOUNT_REF, MONEY, STATUS

    blocks = [emit_object(MONEY), emit_enum(STATUS), *emit_union_with_base(ACCOUNT_REF)]
    return HEADER + "\n\n" + "\n\n\n".join(blocks) + "\n"


if __name__ == "__main__":
    out = main()
    Path(__file__).with_name("out_b.py").write_text(out)
    print(out)
