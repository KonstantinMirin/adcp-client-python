"""A swallowed exception's FAULT, named for a log line, with the data left out.

**WHY A SWALLOW IS SOMETIMES THE CONTRACT.**  Two production paths catch broadly and raise
a typed error with no ``__cause__`` and no ``__context__``, and upstream's own tests assert
exactly that -- ``tests/test_reporting_frozen_read_corrections.py``'s
``test_response_validation_failure_stays_remote_typed_and_redacted`` checks the code, the
absence of a payload secret from ``str`` and ``repr``, AND that both chaining slots are
``None``.  A provider's exception may name anything and its message may carry a bearer
token, so narrowing the ``except`` or chaining the cause would weaken a redaction
guarantee.  The swallow stays.

**WHAT WAS WRONG IS THAT THE CAUSE WAS UNOBSERVABLE.**  Measured twice, in two packages,
on the same day:

* ``adcp.reporting._reconcile`` answered ``STATUS_READ_FAILED`` for every defect, so 99
  reporting tests expecting the specific code their own chain defect earns could not say
  what had been refused;
* ``adcp.property_lists`` answered ``SERVICE_UNAVAILABLE / transient`` for a
  ``GetPropertyListRequest`` refused at ``pagination.cursor`` -- 17 failures that read as
  an unowned cause in ``survey.causes`` because the report carried no trace of the real
  one.  A broad ``except`` does not only hide a cause from a reader; it hides it from the
  ATTRIBUTION, so the work lands on nobody.

So the cause is reported where it costs the exception nothing: a ``DEBUG`` line.  **One
helper and not one per call site**, because a redaction written twice is a redaction with
two readings of what counts as data, and the second one is where a token gets through.
"""

from __future__ import annotations

#: How many of a ``ValidationError``'s rows a line names.  A refused page can report
#: hundreds; the first few say which node and the rest repeat the shape.
_ROWS = 8


def refused_at(error: BaseException) -> str:
    """A REDACTED one-line summary of a swallowed failure: WHAT, and WHERE.

    **THE VALUE IS NEVER IN IT.**  A ``ValidationError``'s own text carries
    ``input_value``, and the payload is the provider's or the buyer's -- it may hold a
    credential, which is the thing the surrounding redaction exists to keep out of the
    error.  So this takes the two fields that name the FAULT and not the data: each row's
    ``loc`` path and its ``type`` code.  Everything else of pydantic's row, ``msg`` and
    ``input`` included, is dropped -- and ``msg`` is dropped even though it reads harmless,
    because pydantic interpolates the input into it (``Input should be a valid string
    [input_value='sk-live-…']``).

    For any other exception it is the CLASS NAME alone, for the same reason: a provider's
    message is theirs and may name anything.
    """
    rows = getattr(error, "errors", None)
    if not callable(rows):
        return type(error).__name__
    try:
        found = rows()
    except Exception:  # noqa: BLE001 -- a diagnostic may not raise over the error it describes
        return type(error).__name__
    where = ", ".join(
        ".".join(str(part) for part in row.get("loc", ())) + f" [{row.get('type')}]"
        for row in found[:_ROWS]
    )
    return f"{type(error).__name__}: {where}" if where else type(error).__name__
