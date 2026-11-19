"""Which is narrower, the class or its document -- and if the class, was it DECIDED?

Takes an import path and a JSON payload, validates the payload against the DOCUMENT
with jsonschema at the pointer the class carries in ``__adcp_schema__``, then hands the
same payload to pydantic.  Where the class refuses what the document admits, reads
``__adcp_approximations__`` for a ``NARROWED`` record at the refused pointer, because a
declared narrowing is a decision and only an UNDECLARED one is a defect.  Prints one of:

  (a) EMISSION  -- document accepts, class refuses, nothing declares the narrowing
  (b) STALE     -- document refuses
  (c) DECIDED   -- document accepts, class refuses, a NARROWED approximation declares it
  BOTH-ACCEPT   -- neither refuses (the failure is elsewhere)

Usage:
    python scripts/adjudicate_validation_error.py adcp.types:GetSignalsRequest '{"a": 1}'
"""

from __future__ import annotations

import importlib
import json
import sys

from adcp.types._base import _refuse_at


def _load(spec: str) -> type:
    module, _, name = spec.partition(":")
    obj = importlib.import_module(module)
    for part in name.split("."):
        obj = getattr(obj, part)
    return obj  # type: ignore[return-value]


def main() -> int:
    cls = _load(sys.argv[1])
    payload = json.loads(sys.argv[2])
    ref = cls.__adcp_schema__
    print(f"class    : {cls.__module__}.{cls.__qualname__}")
    print(f"document : {ref.document}")
    print(f"pointer  : {ref.pointer or '#'}")
    print(f"payload  : {json.dumps(payload)}")

    doc_err = None
    try:
        _refuse_at(ref, payload, cls.__name__, module=cls.__module__)
    except Exception as exc:  # noqa: BLE001 - the verdict is the exception
        doc_err = exc

    cls_err = None
    try:
        cls.model_validate(payload)
    except Exception as exc:  # noqa: BLE001 - the verdict is the exception
        cls_err = exc

    print("\n-- DOCUMENT (jsonschema at the pointer) --")
    print("accepts" if doc_err is None else f"REFUSES:\n{doc_err}")
    print("\n-- CLASS (pydantic) --")
    print("accepts" if cls_err is None else f"REFUSES:\n{cls_err}")

    if doc_err is not None:
        print("\nVERDICT: (b) STALE TEST -- the document itself refuses this payload")
        return 0
    if cls_err is None:
        print("\nVERDICT: BOTH ACCEPT -- the ValidationError comes from somewhere else")
        return 0

    # The class refuses what the document admits.  A NARROWED approximation at one of
    # the refused pointers makes that a decision; its absence makes it the defect.
    refused = {"/".join(str(p) for p in e["loc"]) for e in cls_err.errors()}
    declared = [
        a
        for a in getattr(cls, "__adcp_approximations__", ())
        if a.kind == "NARROWED"
        and any(a.pointer.endswith(f"/properties/{r.split('/')[0]}") or r == "" for r in refused)
    ]
    print("\n-- NARROWED approximations at the refused pointers --")
    if declared:
        for a in declared:
            print(f"  {a.pointer} {a.keyword}={a.fact} [{a.kind}/{a.rung}] <- {a.attribution}")
        print("\nVERDICT: (c) DECIDED -- a NARROWED approximation declares this narrowing")
    else:
        print("  none")
        print("\nVERDICT: (a) EMISSION DEFECT -- document accepts, class refuses, undeclared")
    return 0


if __name__ == "__main__":
    sys.exit(main())
