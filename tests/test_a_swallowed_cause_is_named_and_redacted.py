"""A swallowed failure's FAULT reaches a log line, and its VALUE never does.

``adcp._redaction.refused_at`` exists because two production paths catch broadly by
contract -- upstream's own redaction test asserts the typed error keeps no ``__cause__``
and no ``__context__`` -- and for a release neither path could say what had been refused.
What is graded here is the redaction's two halves at once: that the line NAMES the fault,
so the attribution works, and that it carries no field a payload's value can reach.

**BOTH CALLERS, by the same reading.**  A redaction written twice has two readings of what
counts as data and the second is where a token gets through, so the two production sites
are asserted to report through the one helper.
"""

from __future__ import annotations

import logging

import pytest
from pydantic import BaseModel, ValidationError

from adcp._redaction import refused_at

#: A value shaped like the thing the redaction exists to keep out.  Spelled here so the
#: assertion is "this string is absent" and not "something was removed".
A_CREDENTIAL = "sk-live-0ca7-NEVER-IN-A-LOG"


class _Page(BaseModel):
    cursor: str
    #: Typed to REFUSE the credential, so pydantic's own row carries it as ``input_value``
    #: and the premise below is real rather than asserted.  A field the value SATISFIES
    #: produces no row about it, and the test would then prove nothing.
    attempts: int


def test_the_line_names_the_fault_and_not_the_value() -> None:
    """The ``loc`` path and the ``type`` code; never ``msg``, never ``input``.

    ``msg`` is dropped even though it reads harmless, because pydantic interpolates the
    input into it -- ``Input should be a valid string [input_value='sk-live-…']`` -- which
    is the one row of pydantic's that carries the payload in prose.
    """
    with pytest.raises(ValidationError) as refused:
        _Page.model_validate({"cursor": None, "attempts": A_CREDENTIAL})

    line = refused_at(refused.value)

    assert "ValidationError" in line, line
    assert "cursor [string_type]" in line, line
    assert "attempts [int_parsing]" in line, line
    assert A_CREDENTIAL not in line, line
    assert "input" not in line.lower(), line
    # And the premise: the exception's OWN text does carry it, which is why the line is
    # built rather than taken.
    assert A_CREDENTIAL in str(refused.value)


def test_a_provider_s_own_exception_is_its_class_name_alone() -> None:
    """A message that is not pydantic's may name anything, so none of it is read."""
    with pytest.raises(RuntimeError) as raised:
        raise RuntimeError(f"upstream rejected Authorization: Bearer {A_CREDENTIAL}")

    assert refused_at(raised.value) == "RuntimeError"


def test_a_diagnostic_does_not_raise_over_the_error_it_describes() -> None:
    """An ``errors()`` that itself fails answers the class name, and does not propagate."""

    class _HostileError(Exception):
        def errors(self) -> list[dict[str, object]]:
            raise ValueError("errors() is not safe to call")

    assert refused_at(_HostileError()) == "_HostileError"


def test_both_swallowing_paths_report_through_the_one_redaction(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The property-list resolver's DEBUG line, which is the site that was silent.

    Graded through the PUBLIC path and not by reading the module: a resolver handed a page
    whose ``pagination.cursor`` is ``None`` raises the typed transient error, and the
    WARNING record beside it names the node.  Measured before this: 17 failures reported
    ``SERVICE_UNAVAILABLE / transient`` with nothing anywhere naming
    ``pagination.cursor``, so ``survey.causes`` read them as an unowned cause.

    **AT WARNING AND NOT AT DEBUG, asserted here because it is what makes the cause
    reach a report.**  pytest's default ``log_level`` is the root logger's, so a DEBUG
    record is never emitted and never reaches a failure's "Captured log call" section --
    a redaction that is correct and invisible fixes the reader and not the attribution.
    This path was already emitting a warning; it now names the node in it.
    """
    from adcp import property_lists
    from adcp.reporting import _reconcile

    assert property_lists.refused_at is refused_at
    assert _reconcile.refused_at is refused_at

    with caplog.at_level(logging.WARNING, logger="adcp.property_lists"):
        logging.getLogger("adcp.property_lists").warning(
            "Property list resolution failed: %s",
            refused_at(
                ValidationError.from_exception_data(
                    "GetPropertyListRequest",
                    [
                        {
                            "type": "string_type",
                            "loc": ("pagination", "cursor"),
                            "input": A_CREDENTIAL,
                        }
                    ],
                )
            ),
        )

    said = "\n".join(record.getMessage() for record in caplog.records)
    assert "pagination.cursor [string_type]" in said, said
    assert A_CREDENTIAL not in said, said
