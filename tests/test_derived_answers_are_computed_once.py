"""A derived answer is computed ONCE per process, and the COUNT is the assertion.

Three functions derived the same answer again for every caller that asked, measured over
one instrumented run of ``tests/`` (`adcp-client-python-jv26`; cProfile, memray and
``time -v`` artifacts under
``/srv/ws/adcp-client-python-testperf/runs/combined``):

* ``adcp.types._restored._surface`` -- **112,118 calls, one per ATTRIBUTE ACCESS**, 181.24 s
  cumulative profiled / 53.0 s real, and **20.42 GB allocated**, 9.3 % of the run. Every
  flat-name access re-walked all twelve restored modules and re-``getattr``-ed every symbol
  of all 23 domain paths: ~3,243 ``getattr`` and ~1,522 ``dict.pop`` PER ACCESS.
* ``adcp.reporting.ledger.delivery_models._hints`` -- **252,359 calls on a fixed set of
  record classes**, and **49.19 GB, 22.3 % of every byte the run allocated, the largest
  single allocator**. ``typing.get_type_hints`` re-``compile``-d the same annotations
  1,427,256 times.
* ``adcp.validation.schema_loader._sdk_pinned_bundle_key`` -- **59,221 calls**, reaching
  ``adcp._version._read_packaged_version`` **57,261** of the 73,205 times that
  packaged-resource read happened at all, while its own docstring said *"Cached at import
  time so the lookup happens once"*. Nothing cached it.

One waste class in three places: work repeated per unit that can be done once per run.

**EVERY CHECK HERE IS A WORK COUNT AND NEVER A DURATION.** A timing assertion on a shared
box grades the box, goes red under load and green under a regression, and is the reason
``--timeout`` exists as a separate instrument. So each check installs a counter over the
function that does the WORK -- the derivation, ``typing.get_type_hints``,
``_read_packaged_version`` -- and asserts how many times it ran for N units of demand.

**AND EACH WORK COUNT IS PAIRED WITH A MUTATION CHECK, because a work-count test that
cannot go red is worse than none.** A counter wired to a name nothing calls any more
reports ``0`` and passes every assertion that the work happened once. So each pair has a
second test that drops the hold between units and asserts the counter then observes EVERY
one of them: that is the uncached behaviour these fixes removed, reproduced through the
same instrument, so the ``== 1`` next door is a measurement rather than a silence. A
memoization with no work-count test is a memoization the next refactor silently undoes.

**AND EACH TRIO ENDS ON THE ANSWER, not the count.** A cache that returns something else
is not an optimisation, so every section asserts the held answer equals what a fresh
derivation says.
"""

from __future__ import annotations

import dataclasses
import importlib
import pathlib
import typing
from collections.abc import Callable
from typing import Any

import pytest

import adcp.types as types

_restored = importlib.import_module("adcp.types._restored")


class _Counter:
    """A counting stand-in for one function, installed over the name its caller reads.

    It calls the real function, so what a test measures is how often the WORK happened and
    never whether the answer changed -- the equality check at the end of each section is
    what grades the answer.
    """

    def __init__(self, target: Callable[..., Any]) -> None:
        self.target = target
        self.calls = 0

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        self.calls += 1
        return self.target(*args, **kwargs)


def _drop_what_it_holds(owner: Any, handle: str) -> None:
    """Call ``owner.handle`` to drop a hold, and say nothing when there is no such handle.

    **TOLERANT ON PURPOSE, because the mutation these tests exist for is the hold being
    DELETED -- and a hold goes with its invalidator.** Measured by doing it: a fixture that
    reaches for the invalidator unconditionally raises ``AttributeError`` about itself once
    the hold is gone, every test in its section ERRORS on the fixture, and the work count
    -- the thing that actually regressed -- is never asserted. Tolerated here, the same
    mutation lands where it belongs, on a count of how much work N units of demand did.
    """
    drop = getattr(owner, handle, None)
    if drop is not None:
        drop()


# ---------------------------------------------------------------------------------------
# A -- adcp.types._restored._surface, one derivation per PROCESS and not per access
# ---------------------------------------------------------------------------------------

#: The accesses the count is measured over: words the flat surface answers from a RESTORED
#: module, plus words nothing binds at all.
#:
#: Derived rather than listed, and both halves reach :func:`adcp.types._restored._surface`
#: through the one path a consumer writes.  A word ``_restored`` offers is answered either
#: from ``STATED`` -- consulted before the alias table -- or at the restored consult after
#: it, because ``_surface`` subtracts exactly the words an earlier layer binds; and a word
#: NOTHING binds walks every layer, raises ``AttributeError``, and is the shape most of the
#: 112,118 measured accesses had.
_OFFERED_WORDS = sorted(_restored.__all__)[:40]
_ABSENT_WORDS = [f"NoDocumentStatesThisWord{index}" for index in range(10)]
_ACCESSES = (*_OFFERED_WORDS, *_ABSENT_WORDS)


def _ask(name: str) -> None:
    """One flat-name access, the spelling a consumer writes, miss or hit."""
    try:
        getattr(types, name)
    except AttributeError:
        pass


@pytest.fixture
def surface_derivations(monkeypatch: pytest.MonkeyPatch) -> _Counter:
    """A counter over the derivation, with the hold dropped before and after.

    Dropped AFTER as well, because a hold formed while the counter was installed would
    keep this test's wrapper reachable from module state for the rest of the session.
    """
    counter = _Counter(_restored._derive_surface)
    monkeypatch.setattr(_restored, "_derive_surface", counter)
    _drop_what_it_holds(_restored, "_forget_surface")
    yield counter
    _drop_what_it_holds(_restored, "_forget_surface")


def test_every_attribute_access_shares_one_surface_derivation(
    surface_derivations: _Counter,
) -> None:
    """50 accesses, ONE derivation. Measured before this: one derivation per access."""
    for name in _ACCESSES:
        _ask(name)

    assert len(_ACCESSES) == 50, "the population this count is read against"
    assert surface_derivations.calls == 1, (
        f"{len(_ACCESSES)} flat-name accesses derived the surface "
        f"{surface_derivations.calls} times; the hold in adcp.types._restored exists so "
        "that it is derived once per process"
    )


def test_dropping_the_hold_puts_the_derivation_back_on_every_access(
    surface_derivations: _Counter,
) -> None:
    """THE MUTATION CHECK for the test above.

    With the hold dropped before each access the counter observes one derivation per
    access, which is what the 112,118 measured derivations were. So the ``== 1`` next door
    is this instrument reporting work it can see, and a future refactor that removes the
    hold reddens there rather than passing on a counter wired to nothing.

    **AT LEAST ONE PER ACCESS AND NOT EXACTLY ONE**, because the count is of the whole
    process and this file is not its only caller: measured outside pytest the ratio is
    exactly 50 derivations for these 50 accesses, and under pytest it is 51 -- one more
    flat-name access arriving from the harness while the counter is installed. The claim
    being made is that the work scales with the units of demand, which a fixed ratio would
    overstate.
    """
    for name in _ACCESSES:
        _drop_what_it_holds(_restored, "_forget_surface")
        _ask(name)

    assert surface_derivations.calls >= len(_ACCESSES), (
        f"{len(_ACCESSES)} accesses with the hold dropped between them derived the surface "
        f"{surface_derivations.calls} times; the counter does not observe the derivation, "
        "so the work-count assertion beside it cannot fail and is not a measurement"
    )


def test_the_held_surface_is_what_a_fresh_derivation_says() -> None:
    """The answer, not the count -- and the check the profile asked for before any cache.

    ``costs.md`` §6.5 recorded that the capture proves ``_surface`` is CALLED 112,118
    times and not that memoizing it is safe. This is that gap closed: the held answer and
    a derivation taken now agree, word for word and object for object.
    """
    held = _restored._surface()
    fresh = _restored._derive_surface()

    assert sorted(held) == sorted(fresh)
    assert all(
        held[word] is fresh[word] for word in fresh
    ), "a held word resolves to a different object than a fresh derivation gives it"
    assert sorted(held) == sorted(_restored.__all__)


def test_no_caller_can_edit_the_held_surface() -> None:
    """The hold is SHARED, so the thing shared is read-only.

    Every caller used to get a dict of its own and could do what it liked with it. One
    derivation held for the process means one dict reachable from every caller, and a
    mapping nothing can write is what keeps that a saving rather than a new way for one
    caller to change another's surface.
    """
    held = _restored._surface()

    with pytest.raises(TypeError):
        held["NoCallerMayBindThis"] = object()  # type: ignore[index]


# ---------------------------------------------------------------------------------------
# E -- delivery_models._hints, one resolution per CLASS and not per record
# ---------------------------------------------------------------------------------------

_delivery_models = importlib.import_module("adcp.reporting.ledger.delivery_models")
_REPORTING_ROOT = pathlib.Path(importlib.import_module("adcp.reporting").__file__).parent


def _freezing_modules() -> tuple[str, ...]:
    """Every module that freezes records through ``_freeze_fields``, found by reading.

    Read off the source tree and never listed, because this is the population
    :func:`adcp.reporting.ledger.delivery_models._hints` is keyed on and a module that
    starts freezing records has to join the count with nothing edited here. Measured
    today: four modules -- ``delivery_models``, which declares the function, and the three
    that import it -- and 39 record classes between them.
    """
    found = []
    for path in sorted(_REPORTING_ROOT.rglob("*.py")):
        if "_freeze_fields" in path.read_text(encoding="utf-8"):
            dotted = path.relative_to(_REPORTING_ROOT).with_suffix("").as_posix()
            found.append(f"adcp.reporting.{dotted.replace('/', '.')}")
    return tuple(found)


#: The fixed class set the count is read against: every frozen record the freezing modules
#: declare.
#:
#: Derived rather than listed, for :func:`_freezing_modules`' reason -- and the derivation
#: is the claim the cache rests on, that the keys are classes created once, when the module
#: declaring them runs its body.
_RECORD_CLASSES = tuple(
    value
    for module in _freezing_modules()
    for value in vars(importlib.import_module(module)).values()
    if isinstance(value, type) and dataclasses.is_dataclass(value) and value.__module__ == module
)


@pytest.fixture
def hint_resolutions(monkeypatch: pytest.MonkeyPatch) -> _Counter:
    """A counter over ``typing.get_type_hints`` as ``_hints`` reads it, hold dropped."""
    counter = _Counter(_delivery_models.get_type_hints)
    monkeypatch.setattr(_delivery_models, "get_type_hints", counter)
    _drop_what_it_holds(_delivery_models, "_forget_hints")
    yield counter
    _drop_what_it_holds(_delivery_models, "_forget_hints")


def test_annotations_are_resolved_once_per_record_class(hint_resolutions: _Counter) -> None:
    """20 asks per class, one resolution per class, over the whole key population."""
    assert len(_freezing_modules()) == 4, "the modules that freeze records"
    assert len(_RECORD_CLASSES) == 39, "the fixed class set this count is read against"

    for _ in range(20):
        for record in _RECORD_CLASSES:
            _delivery_models._hints(record)

    assert hint_resolutions.calls == len(_RECORD_CLASSES), (
        f"{20 * len(_RECORD_CLASSES)} asks over {len(_RECORD_CLASSES)} classes resolved "
        f"annotations {hint_resolutions.calls} times"
    )


def test_building_many_records_resolves_annotations_once_per_class(
    hint_resolutions: _Counter,
) -> None:
    """The caller that paid the 252,359, through the path it takes.

    ``__post_init__`` -> ``_freeze_fields`` -> ``_hints``, so the demand is one ask per
    RECORD CONSTRUCTED and the work must be one resolution per class constructed.
    """
    for index in range(50):
        principal = _delivery_models.ReportingDeliveryPrincipal("acct_1", "consumer_1")
        _delivery_models.ReportingMaterializationKey(principal, f"materialization_{index}")
        _delivery_models.ReportingReceiptKey(principal, f"receipt_{index:016d}")

    assert (
        hint_resolutions.calls == 3
    ), f"150 records over 3 classes resolved annotations {hint_resolutions.calls} times"


def test_clearing_the_cache_puts_a_resolution_back_on_every_ask(
    hint_resolutions: _Counter,
) -> None:
    """THE MUTATION CHECK for the two tests above.

    Cleared before each ask, the counter observes all 60 -- which is the shape of the
    252,359 measured calls. So the counts next door are this instrument reporting work it
    can see, and removing the decorator reddens them.
    """
    asks = 0
    for _ in range(20):
        for record in _RECORD_CLASSES[:3]:
            _drop_what_it_holds(_delivery_models, "_forget_hints")
            _delivery_models._hints(record)
            asks += 1

    assert hint_resolutions.calls >= asks, (
        f"{asks} asks with the hold dropped between them resolved annotations "
        f"{hint_resolutions.calls} times; the counter does not observe the resolution, so "
        "the work-count assertions beside it cannot fail and are not measurements"
    )


@pytest.mark.parametrize("record", _RECORD_CLASSES, ids=lambda cls: cls.__name__)
def test_the_held_hints_are_what_get_type_hints_says(record: type) -> None:
    """The answer, not the count: one resolution per class must be the SAME resolution."""
    assert dict(_delivery_models._hints(record)) == typing.get_type_hints(record)


def test_no_caller_can_edit_a_held_hint_mapping() -> None:
    """Held once and handed to every caller, so what is handed over is read-only.

    ``get_type_hints`` built a fresh dict per call and a caller could edit its own copy.
    One resolution held per class means one mapping reachable from every record this
    module freezes, and ``_freeze_fields`` reads a field's annotation out of it.
    """
    with pytest.raises(TypeError):
        _delivery_models._hints(_RECORD_CLASSES[0])["field"] = object()  # type: ignore[index]


# ---------------------------------------------------------------------------------------
# F -- schema_loader._sdk_pinned_bundle_key, one packaged read per PROCESS
# ---------------------------------------------------------------------------------------

_schema_loader = importlib.import_module("adcp.validation.schema_loader")
_version = importlib.import_module("adcp._version")


@pytest.fixture
def packaged_reads(monkeypatch: pytest.MonkeyPatch) -> _Counter:
    """A counter over the packaged ``ADCP_VERSION`` read, with the cache cleared.

    Installed on ``adcp._version`` because that is the module
    :func:`adcp.validation.schema_loader._sdk_pinned_bundle_key` imports the name from,
    per call, inside its own body.
    """
    counter = _Counter(_version._read_packaged_version)
    monkeypatch.setattr(_version, "_read_packaged_version", counter)
    _drop_what_it_holds(_schema_loader._sdk_pinned_bundle_key, "cache_clear")
    yield counter
    _drop_what_it_holds(_schema_loader._sdk_pinned_bundle_key, "cache_clear")


def test_the_sdk_pin_is_read_from_the_package_once(packaged_reads: _Counter) -> None:
    """200 asks, one packaged read -- the sentence the docstring already made, graded.

    What stood in that docstring was "Cached at import time so the lookup happens once"
    while the run performed 57,261 of them. The claim is now the decorator's, and this is
    the check that keeps the two together.
    """
    for _ in range(100):
        _schema_loader._sdk_pinned_bundle_key()
        _schema_loader._resolve_bundle_key_for_version(None)

    assert packaged_reads.calls == 1, (
        f"200 asks for the SDK pin read the packaged ADCP_VERSION file "
        f"{packaged_reads.calls} times"
    )


def test_clearing_the_cache_puts_a_packaged_read_back_on_every_ask(
    packaged_reads: _Counter,
) -> None:
    """THE MUTATION CHECK for the test above.

    Cleared before each ask, the counter observes all 100 -- the uncached behaviour, which
    is what 57,261 of the run's 73,205 packaged reads were. So the ``== 1`` next door is a
    measurement, and removing the decorator reddens it.
    """
    for _ in range(100):
        _drop_what_it_holds(_schema_loader._sdk_pinned_bundle_key, "cache_clear")
        _schema_loader._sdk_pinned_bundle_key()

    assert packaged_reads.calls >= 100, (
        f"100 asks with the cache cleared between them read the packaged file "
        f"{packaged_reads.calls} times; the counter does not observe the packaged read, so "
        "the work-count assertion beside it cannot fail and is not a measurement"
    )


def test_the_held_pin_is_what_the_packaged_file_says() -> None:
    """The answer, not the count."""
    assert _schema_loader._sdk_pinned_bundle_key() == _schema_loader.resolve_bundle_key(
        _version._read_packaged_version()
    )


def test_a_caller_pinned_version_is_not_answered_from_the_sdk_pin_cache() -> None:
    """The cache key is the arguments the function takes, which is none of them.

    ``lru_cache(maxsize=1)`` over a function that DOES take a version argument is a defect
    this repository has already paid for once -- ``action_update_fields`` answered every
    pin with the default bundle (``tests/test_rc3_media_buy_runtime.py``). This function
    takes no argument because the SDK's own pin is its whole input, and the caller's pin is
    :func:`adcp.validation.schema_loader._resolve_bundle_key_for_version`'s argument, which
    reaches the SDK pin only for ``None``.
    """
    assert _schema_loader._resolve_bundle_key_for_version(None) == (
        _schema_loader._sdk_pinned_bundle_key()
    )
    assert _schema_loader._resolve_bundle_key_for_version("3.0") == "3.0"
