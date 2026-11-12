"""``model_summary`` asks for the SUBJECT, and the subject is what our class states.

**THE DEFECT THIS GRADES WAS A NAME REACHING MACHINERY.**
``adcp.types.base._RESPONSE_MESSAGE_REGISTRY`` is upstream's, and its keys are
upstream's published class names -- ``CreateMediaBuyResponse1``, "the first arm of
that document's ``oneOf``", because their generator emits a class per POSITION.
This repository emits one class per SUBJECT and names it from the subject's own
document, so the object that answers ``model_summary()`` is ``CreateMediaBuySuccess``
and a registry keyed on ``__class__.__name__`` missed every formatter: 19 of
``tests/test_response_str.py``'s 32 read ``"CreateMediaBuySuccess response"`` where
the document's subject has a message registered for it.

**AND THE RELATION IS ALREADY HELD, so this grades a resolution and not a list.**
``survey/name_table.py`` resolved each of upstream's 9.6.1 words to the class of
ours denoting one subject, by rule; ``survey/emit_legacy_names.py`` emitted those
rows as the alias layer ``adcp.types`` consults. The assertions below are therefore
about three things and nothing else:

1. every word upstream registered a formatter for resolves, through that table, to
   a class of ours that STATES a subject (``__adcp_schema__``) -- the count is the
   finding, and a word that stops resolving is a schema delta, not a typo;
2. the formatter reached is the one upstream wrote for that subject, asked by OUR
   name;
3. the generic fallback is intact -- a type with no formatter registered has no
   message to give, and ``"<name> response"`` is the correct answer, not a miss.
"""

from __future__ import annotations

import pytest

from adcp.types import base
from adcp.types.media_buy import (
    BuildCreativeError,
    CreateMediaBuyError,
    CreateMediaBuySuccess,
    GetProductsResponse,
    UpdateMediaBuySuccess,
)


def _subjects() -> dict[object, object]:
    """The built index, with the module cache reset so the build itself is graded."""
    base._SUBJECT_MESSAGE_REGISTRY = None
    base._WORDS_WITH_NO_SUBJECT = ()
    return base._subject_message_registry()


class TestEveryWordResolvesToASubject:
    """Upstream's registry keys, resolved through the alias table to our classes."""

    def test_the_registry_is_upstreams_words(self) -> None:
        """The keys are their spellings, which is why the lookup had to be re-keyed.

        Not an assertion about how many formatters exist -- an assertion that the
        keys are POSITIONAL names of theirs and so cannot match ours. If this ever
        reads zero, upstream re-keyed the registry and this whole layer is moot.
        """
        positional = [w for w in base._RESPONSE_MESSAGE_REGISTRY if w[-1].isdigit()]
        assert positional, "no key is one of upstream's numbered position names"

    def test_no_word_is_left_without_a_subject(self) -> None:
        """**THE COUNT IS THE FINDING.**

        A word that resolves to nothing is a formatter for a type we do not emit,
        or a word ``legacy_names.__adcp_ambiguous__`` DECLINED as ambiguous. Either
        wants reading -- neither wants a hand-written row -- so it is named here
        rather than tolerated.
        """
        index = _subjects()
        assert base._WORDS_WITH_NO_SUBJECT == (), (
            f"{len(base._WORDS_WITH_NO_SUBJECT)} of upstream's registry keys resolve "
            f"to no class of ours stating a subject: {base._WORDS_WITH_NO_SUBJECT}"
        )
        assert len(index) == len(base._RESPONSE_MESSAGE_REGISTRY)

    def test_each_subject_is_a_document_and_a_pointer(self) -> None:
        """The key IS the identity: a bundle-relative document plus a JSON pointer.

        Keyed on the subject and not on the resolved class's ``__name__`` because
        our generated names are generator-derived too -- a numbered one can
        renumber on a schema bump -- while the document and pointer do not move
        unless the schema does.
        """
        for subject in _subjects():
            document = subject.document  # type: ignore[attr-defined]
            pointer = subject.pointer  # type: ignore[attr-defined]
            assert document.endswith(".json"), document
            assert pointer.startswith("#"), pointer

    def test_the_index_is_built_once(self) -> None:
        """Resolution is a first-use cost, not a per-call one."""
        first = _subjects()
        assert base._subject_message_registry() is first


class TestOurNameReachesTheirFormatter:
    """The message upstream wrote, asked for by the name our compiler chose."""

    @pytest.mark.parametrize(
        ("construct", "expected"),
        [
            # core/create-media-buy-response.json#/oneOf/0 -- upstream's
            # ``CreateMediaBuyResponse1``.
            (
                lambda: CreateMediaBuySuccess.model_construct(
                    media_buy_id="mb_123", packages=[{"package_id": "pkg_1"}]
                ),
                "Media buy mb_123 created with 1 package.",
            ),
            # ...#/oneOf/1 -- upstream's ``CreateMediaBuyResponse2``.
            (
                lambda: CreateMediaBuyError.model_construct(errors=[{"code": "x"}]),
                "Media buy creation failed with 1 error.",
            ),
            # media-buy/update-media-buy-response.json#/oneOf/0.
            (
                lambda: UpdateMediaBuySuccess.model_construct(media_buy_id="mb_9"),
                "Media buy mb_9 updated successfully.",
            ),
            # **AND THE ONE THE DOCUMENT REORDERED.** Upstream's
            # ``BuildCreativeResponse2`` is the arm requiring ``errors``; in the
            # pinned bundle that arm is ``#/oneOf/4`` and not the second one. A
            # positional match would hand this formatter to
            # ``BuildCreativeMultiSuccess``; the subject does not care what index
            # the arm sits at.
            (
                lambda: BuildCreativeError.model_construct(errors=[{"code": "x"}]),
                "Creative build failed with 1 error.",
            ),
        ],
    )
    def test_the_formatter_is_found_by_subject(self, construct, expected: str) -> None:
        assert construct().model_summary() == expected

    def test_a_word_shared_with_upstream_still_answers(self) -> None:
        """Where the two spellings agree, nothing changed.

        Five of the nineteen subjects carry the same word on both sides -- the
        five whose document declares no ``oneOf``, so there is no arm for their
        generator to number. The
        subject probe answers them, and the class-name probe behind it would have
        too -- which is the point: this is not a redirection of working behaviour.
        """
        response = GetProductsResponse.model_construct(products=[{"product_id": "p1"}])
        assert response.model_summary() == "Found 1 product matching your requirements."


class TestTheGenericFallbackIsKept:
    """An unregistered type has no message, and the generic form is the answer."""

    def test_a_type_with_no_formatter_gets_the_generic_form(self) -> None:
        """``"<name> response"`` is CORRECT upstream behaviour, not a failure mode."""

        class Unregistered(base.AdCPBaseModel):
            pass

        assert Unregistered.model_construct().model_summary() == "Unregistered response"

    def test_a_subject_with_no_formatter_falls_through(self) -> None:
        """A generated class whose document has no formatter registered for it.

        Exercises the path where the subject probe finds a subject and no
        formatter, which must fall through to the name probe and then to the
        generic form rather than raising or answering with a sibling's message.
        """
        from adcp.types.media_buy import BuildCreativeMultiSuccess

        summary = BuildCreativeMultiSuccess.model_construct(creative_manifests=[]).model_summary()
        assert summary == "BuildCreativeMultiSuccess response"

    def test_the_class_name_probe_survives_for_a_subjectless_object(self) -> None:
        """Upstream's own hand-written classes state no subject, and still answer.

        Their kept machinery builds models that never came from a document, so the
        registry's own keys must keep working for an object that carries no
        ``__adcp_schema__`` at all.
        """

        class GetProductsResponse(base.AdCPBaseModel):  # noqa: N801 -- upstream's word
            pass

        assert not hasattr(GetProductsResponse, "__adcp_schema__")
        built = GetProductsResponse.model_construct()
        assert built.model_summary() == "No products matched your requirements."
