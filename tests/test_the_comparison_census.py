"""§8's COMPARISON over every pair, graded in a MINUTE, and the 155 pairs it reddens.

**Why this file exists and why it is not in ``tests/test_emit.py``**
(``adcp-client-python-3be.23``).  The comparison is the only check of §8 that can see a
model WIDER or NARROWER than its document, and its reading lived in exactly two tests that
read it off ``graded_reports()`` -- the suite's pole, 2,793 pair reports with a draw and a
dump each, 55 minutes at best and 6-7 hours as the tree stands, twice killed by the
kernel.  **So the instrument that would have said "155 pairs are red" did not run, and
``COMPARISON_FACTS`` held 0 ENTRIES against a live 155 pairs carrying 1,086 facts with
nothing red anywhere.**

That is the second census of this epic to rot in exactly this way.
``tests/test_the_declared_backlog.py`` records the first -- "``DECLARED_WIDENINGS`` came to
hold 11 sites against a live 117 ... with nothing red" -- and moved two instruments out
from behind the pole into a file that needs no pair, no draw and no dump.  This is the same
move for the one census that row left behind: ``tests/compared.py`` asks
``harness.compare_schema`` for the five arguments ``harness.check_pair`` asks it for,
argument for argument, so **no detection is traded away** -- what is dropped is the draw,
the liveness payload and the widening proof, none of which the comparison reads.
``./check --compare`` prints the same reading for a lane that wants it between edits.

**THE READING, measured at this row (``./check --compare`` re-derives it in 36-53 s warm;
``tests/compared.py`` carries the range and why it is a range):**

paired 2793 -- 2789 comparable and 4 whose document cannot be read at;
red 155 pairs in 75 documents / 1086 facts: missing 718, differs 43, added 325;
outcome: pass 2634, model_drops_a_fact 147, model_adds_a_fact 8.

**THE TWO DIRECTIONS ARE NOT ONE FINDING.**  ``missing`` and ``differs`` are a model WIDER
than its document, which §2 permits where a declaration says so -- 147 pairs, and every one
of them is a widening no declaration covers.  ``added`` is a model NARROWER, which §2
forbids outright and no declaration absorbs, because a narrower model refuses traffic the
document admits.  **8 pairs are red on ``added`` ALONE and each one is classified below
(:data:`NARROWER_THAN_ITS_DOCUMENT`): none of them is a real narrowing, and the test that
reads them grades the classification against the document's own text rather than taking
the sentence's word for it.**

``added`` facts also appear in 42 pairs that drop a fact as well, and they are the same
three shapes read at the same nodes -- the ``attestation_refs/items/properties/subject``
node, whose document statement is an ``allOf`` at a NESTED position
(``added properties`` 197, ``added additionalProperties`` 53, ``differs required`` 34), the
``unsatisfied_product_changes`` map, and a ``status`` property whose document states a
``const`` where the model renders the one-member ``enum`` and a ``default``.  Those pairs
are red on the drop direction too, so they are in :data:`COMPARISON_FACTS` with their facts
and are not separately classified here.

**BY SHAPE  (facts / pairs / documents)**, which is the axis a repair row is cut along --
three denominators and never one, for ``DECLARED_WIDENINGS``' reason ("``K`` and ``D`` are
different counts over different denominators and the report never adds them"):

  390     18      9   missing a property entry
  197     36     22   added properties
  102     50     21   missing propertyNames
   76     68     38   missing format
   66     47     30   missing required
   56     19     11   added type
   53     37     22   added additionalProperties
   40     35     21   missing patternProperties
   36     15      9   missing uniqueItems
   34     22     14   differs required
    9      9      2   added propertyNames
    6      3      3   added default
    6      3      3   differs type
    3      3      3   differs default
    2      2      1   missing maxLength
    2      2      2   missing pattern
    2      2      2   added required
    2      2      1   missing type
    2      2      2   added enum
    2      2      2   missing const

**BY DOCUMENT  (pairs / facts), the twelve worst**, which is the axis that says where a row
lands -- a document with ten red pairs is one node emitted ten ways and not ten findings:

   10     20   media-buy/proposal-refinement.json
    8    128   adagents.json
    8     22   media-buy/refine-proposals-response.json
    7     81   media-buy/create-media-buy-request.json
    5     36   core/async-response-data.json
    5     18   media-buy/request-proposals-response.json
    5     10   media-buy/build-creative-response.json
    4     68   core/wholesale-feed-event.json
    4     38   media-buy/buy-products-request.json
    4      9   core/audience-evidence-selection.json
    4      8   media-buy/request-proposals-request.json
    4      5   core/rights-attestation-evaluation.json

**WHAT THIS FILE DOES NOT OWN.**  The four unreadable pairs are
``adcp-client-python-3be.15``'s synthetic ``allOf`` pointer (ex ``10l.108``) and are pinned
here only so a FIFTH cannot leave the comparable population unnoticed; the fix is that
row's.  §8's two set equalities over the declared and approximated sets stay in
``tests/test_emit.py``'s census test, which needs the pairs for its other readings, and
``tests/test_the_declared_backlog.py`` owns §2's declared backlog.
"""

from __future__ import annotations

import pytest

from adcp.types._base import SchemaRef, entailed_types, schema_at

from codegen import harness

import compared
from nodeset import claimed, partitions, ratchet

#: One worker for the whole census, which is the measured cost of not saying so.
#: ``compared.census()`` is ``functools.cache``d and ``functools.cache`` DOES NOT CROSS A
#: PROCESS, so under ``--dist=loadgroup`` an unmarked second reader lands on another worker
#: and pays the pass again -- the defect ``pyproject.toml`` records at 31% of a full run
#: for ``graded_reports``'s four readers.  Every test in this file carries the mark.
CENSUS_GROUP = "comparison_census"

#: The pairing the census ranges over, as a FLOOR and never an equality: an emitting row
#: only adds pairs, and a drop means a class stopped carrying ``__adcp_schema__`` or
#: stopped being emitted.
PAIRED_FLOOR = 2793


#: **EVERY RED PAIR AND EVERY RED FACT, BY NAME.**  ``document#pointer -> the sorted facts``,
#: each fact ``"<direction> <pointer>"``.
#:
#: **THIS WAS AN EMPTY DICT AGAINST A LIVE 155 PAIRS, and the empty was defended in the
#: comment it replaces**: "an EMPTY dict and not a deleted name ... empty is the strongest
#: state it has: every direction is examined and every one is zero".  That was true when it
#: was written and the set grew with every row that emitted more of the bundle, while the
#: only two readers sat behind the pole -- so for six rows the strongest state it had was a
#: state nothing could reach.  ``nodeset.ratchet``'s own rule is the one that was broken:
#: a floor below the truth gets exempted later instead of acted on.
#:
#: **So the floor is recorded WITH THE SHAPES IN IT.**  A count would say that 1,086 facts
#: exist; this says which pair, which pointer and which DIRECTION each one is, grouped by
#: document in the literal -- so a fact arriving reddens with its pair named, a fact
#: leaving reddens with the pair a repair row has to claim, and a fact that MOVED between
#: ``added``, ``missing`` and ``differs`` reddens too, which three per-direction counts
#: could not see.
#:
#: Duplicate entries in a pair's list are real and are kept: the direction and pointer are
#: what a fact is keyed on here, and two facts at one pointer differ in the VALUE the
#: sentence carries -- ``compliance/task-completion-data.json#/anyOf/0`` states
#: ``added /properties/.../subject/properties`` three times, once per position the
#: comparison reached it at.
COMPARISON_FACTS: dict[str, list[str]] = {
    # ---- media-buy/proposal-refinement.json: 10 pairs, 20 facts
    'media-buy/proposal-refinement.json#': [
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    'media-buy/proposal-refinement.json#/oneOf/0': [
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    'media-buy/proposal-refinement.json#/oneOf/1': [
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    'media-buy/proposal-refinement.json#/oneOf/1/anyOf/0': [
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    'media-buy/proposal-refinement.json#/oneOf/1/anyOf/1': [
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    'media-buy/proposal-refinement.json#/oneOf/1/anyOf/2': [
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    'media-buy/proposal-refinement.json#/oneOf/1/anyOf/3': [
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    'media-buy/proposal-refinement.json#/oneOf/1/anyOf/4': [
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    'media-buy/proposal-refinement.json#/oneOf/1/anyOf/5': [
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    'media-buy/proposal-refinement.json#/oneOf/1/anyOf/6': [
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    # ---- adagents.json: 8 pairs, 128 facts
    'adagents.json#/oneOf/1': [
        'missing /properties/formats/items/properties/applies_to_channels',
        'missing /properties/formats/items/properties/canonical_formats_only',
        'missing /properties/formats/items/properties/display_name',
        'missing /properties/formats/items/properties/experimental',
        'missing /properties/formats/items/properties/format_option_id',
        'missing /properties/formats/items/properties/format_schema',
        'missing /properties/formats/items/properties/format_shape',
        'missing /properties/formats/items/properties/locale_policy',
        'missing /properties/formats/items/properties/macro_resolution_capabilities',
        'missing /properties/formats/items/properties/publisher_domain',
        'missing /properties/formats/items/properties/sample_render_url',
        'missing /properties/formats/items/properties/seller_preference',
        'missing /properties/formats/items/properties/technical_requirements_complete',
        'missing /properties/formats/items/properties/tracker_execution_contract',
        'missing /properties/formats/items/properties/v1_format_ref',
        'missing /properties/formats/items/required',
    ],
    'adagents.json#/oneOf/1/allOf/0/anyOf/0': [
        'missing /properties/formats/items/properties/applies_to_channels',
        'missing /properties/formats/items/properties/canonical_formats_only',
        'missing /properties/formats/items/properties/display_name',
        'missing /properties/formats/items/properties/experimental',
        'missing /properties/formats/items/properties/format_option_id',
        'missing /properties/formats/items/properties/format_schema',
        'missing /properties/formats/items/properties/format_shape',
        'missing /properties/formats/items/properties/locale_policy',
        'missing /properties/formats/items/properties/macro_resolution_capabilities',
        'missing /properties/formats/items/properties/publisher_domain',
        'missing /properties/formats/items/properties/sample_render_url',
        'missing /properties/formats/items/properties/seller_preference',
        'missing /properties/formats/items/properties/technical_requirements_complete',
        'missing /properties/formats/items/properties/tracker_execution_contract',
        'missing /properties/formats/items/properties/v1_format_ref',
        'missing /properties/formats/items/required',
    ],
    'adagents.json#/oneOf/1/allOf/0/anyOf/1': [
        'missing /properties/formats/items/properties/applies_to_channels',
        'missing /properties/formats/items/properties/canonical_formats_only',
        'missing /properties/formats/items/properties/display_name',
        'missing /properties/formats/items/properties/experimental',
        'missing /properties/formats/items/properties/format_option_id',
        'missing /properties/formats/items/properties/format_schema',
        'missing /properties/formats/items/properties/format_shape',
        'missing /properties/formats/items/properties/locale_policy',
        'missing /properties/formats/items/properties/macro_resolution_capabilities',
        'missing /properties/formats/items/properties/publisher_domain',
        'missing /properties/formats/items/properties/sample_render_url',
        'missing /properties/formats/items/properties/seller_preference',
        'missing /properties/formats/items/properties/technical_requirements_complete',
        'missing /properties/formats/items/properties/tracker_execution_contract',
        'missing /properties/formats/items/properties/v1_format_ref',
        'missing /properties/formats/items/required',
    ],
    'adagents.json#/oneOf/1/allOf/0/anyOf/2': [
        'missing /properties/formats/items/properties/applies_to_channels',
        'missing /properties/formats/items/properties/canonical_formats_only',
        'missing /properties/formats/items/properties/display_name',
        'missing /properties/formats/items/properties/experimental',
        'missing /properties/formats/items/properties/format_option_id',
        'missing /properties/formats/items/properties/format_schema',
        'missing /properties/formats/items/properties/format_shape',
        'missing /properties/formats/items/properties/locale_policy',
        'missing /properties/formats/items/properties/macro_resolution_capabilities',
        'missing /properties/formats/items/properties/publisher_domain',
        'missing /properties/formats/items/properties/sample_render_url',
        'missing /properties/formats/items/properties/seller_preference',
        'missing /properties/formats/items/properties/technical_requirements_complete',
        'missing /properties/formats/items/properties/tracker_execution_contract',
        'missing /properties/formats/items/properties/v1_format_ref',
        'missing /properties/formats/items/required',
    ],
    'adagents.json#/oneOf/1/allOf/0/anyOf/3': [
        'missing /properties/formats/items/properties/applies_to_channels',
        'missing /properties/formats/items/properties/canonical_formats_only',
        'missing /properties/formats/items/properties/display_name',
        'missing /properties/formats/items/properties/experimental',
        'missing /properties/formats/items/properties/format_option_id',
        'missing /properties/formats/items/properties/format_schema',
        'missing /properties/formats/items/properties/format_shape',
        'missing /properties/formats/items/properties/locale_policy',
        'missing /properties/formats/items/properties/macro_resolution_capabilities',
        'missing /properties/formats/items/properties/publisher_domain',
        'missing /properties/formats/items/properties/sample_render_url',
        'missing /properties/formats/items/properties/seller_preference',
        'missing /properties/formats/items/properties/technical_requirements_complete',
        'missing /properties/formats/items/properties/tracker_execution_contract',
        'missing /properties/formats/items/properties/v1_format_ref',
        'missing /properties/formats/items/required',
    ],
    'adagents.json#/oneOf/1/allOf/0/anyOf/4': [
        'missing /properties/formats/items/properties/applies_to_channels',
        'missing /properties/formats/items/properties/canonical_formats_only',
        'missing /properties/formats/items/properties/display_name',
        'missing /properties/formats/items/properties/experimental',
        'missing /properties/formats/items/properties/format_option_id',
        'missing /properties/formats/items/properties/format_schema',
        'missing /properties/formats/items/properties/format_shape',
        'missing /properties/formats/items/properties/locale_policy',
        'missing /properties/formats/items/properties/macro_resolution_capabilities',
        'missing /properties/formats/items/properties/publisher_domain',
        'missing /properties/formats/items/properties/sample_render_url',
        'missing /properties/formats/items/properties/seller_preference',
        'missing /properties/formats/items/properties/technical_requirements_complete',
        'missing /properties/formats/items/properties/tracker_execution_contract',
        'missing /properties/formats/items/properties/v1_format_ref',
        'missing /properties/formats/items/required',
    ],
    'adagents.json#/oneOf/1/allOf/0/anyOf/5': [
        'missing /properties/formats/items/properties/applies_to_channels',
        'missing /properties/formats/items/properties/canonical_formats_only',
        'missing /properties/formats/items/properties/display_name',
        'missing /properties/formats/items/properties/experimental',
        'missing /properties/formats/items/properties/format_option_id',
        'missing /properties/formats/items/properties/format_schema',
        'missing /properties/formats/items/properties/format_shape',
        'missing /properties/formats/items/properties/locale_policy',
        'missing /properties/formats/items/properties/macro_resolution_capabilities',
        'missing /properties/formats/items/properties/publisher_domain',
        'missing /properties/formats/items/properties/sample_render_url',
        'missing /properties/formats/items/properties/seller_preference',
        'missing /properties/formats/items/properties/technical_requirements_complete',
        'missing /properties/formats/items/properties/tracker_execution_contract',
        'missing /properties/formats/items/properties/v1_format_ref',
        'missing /properties/formats/items/required',
    ],
    'adagents.json#/oneOf/1/properties/formats/items': [
        'missing /properties/applies_to_channels',
        'missing /properties/canonical_formats_only',
        'missing /properties/display_name',
        'missing /properties/experimental',
        'missing /properties/format_option_id',
        'missing /properties/format_schema',
        'missing /properties/format_shape',
        'missing /properties/locale_policy',
        'missing /properties/macro_resolution_capabilities',
        'missing /properties/publisher_domain',
        'missing /properties/sample_render_url',
        'missing /properties/seller_preference',
        'missing /properties/technical_requirements_complete',
        'missing /properties/tracker_execution_contract',
        'missing /properties/v1_format_ref',
        'missing /required',
    ],
    # ---- media-buy/refine-proposals-response.json: 8 pairs, 22 facts
    'media-buy/refine-proposals-response.json#': [
        'added /properties/results/items/properties/unsatisfied_product_changes/propertyNames',
        'missing /properties/products/items/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/products/items/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    'media-buy/refine-proposals-response.json#/anyOf/0': [
        'added /properties/results/items/properties/unsatisfied_product_changes/propertyNames',
        'missing /properties/products/items/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/products/items/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    'media-buy/refine-proposals-response.json#/anyOf/1': [
        'added /properties/results/items/properties/unsatisfied_product_changes/propertyNames',
        'added /properties/status/default',
        'added /properties/status/enum',
        'added /properties/task_id/default',
        'differs /properties/replayed/default',
        'differs /properties/status/type',
        'differs /properties/task_id/type',
        'missing /properties/products/items/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/products/items/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
        'missing /properties/status/const',
        'missing /required',
    ],
    'media-buy/refine-proposals-response.json#/properties/results/items': [
        'added /properties/unsatisfied_product_changes/propertyNames',
    ],
    'media-buy/refine-proposals-response.json#/properties/results/items/oneOf/0': [
        'added /properties/unsatisfied_product_changes/propertyNames',
    ],
    'media-buy/refine-proposals-response.json#/properties/results/items/oneOf/1': [
        'added /properties/unsatisfied_product_changes/propertyNames',
    ],
    'media-buy/refine-proposals-response.json#/properties/results/items/oneOf/2': [
        'added /properties/unsatisfied_product_changes/propertyNames',
    ],
    'media-buy/refine-proposals-response.json#/properties/results/items/oneOf/3': [
        'added /properties/unsatisfied_product_changes/propertyNames',
    ],
    # ---- media-buy/create-media-buy-request.json: 7 pairs, 81 facts
    'media-buy/create-media-buy-request.json#': [
        'added /properties/packages/items/properties/targeting_overlay/properties/collection_selection/type',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/additionalProperties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/type',
        'added /properties/packages/items/properties/targeting_overlay/properties/placement_selection/type',
        'missing /properties/packages/items/properties/creatives/items/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/packages/items/properties/creatives/items/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
        'missing /properties/packages/items/properties/targeting_overlay/properties/browser/uniqueItems',
        'missing /properties/packages/items/properties/targeting_overlay/properties/browser_exclude/uniqueItems',
    ],
    'media-buy/create-media-buy-request.json#/anyOf/0': [
        'added /properties/budget_allocation/additionalProperties',
        'added /properties/budget_allocation/type',
        'added /properties/packages/items/properties/targeting_overlay/properties/collection_selection/type',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/additionalProperties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/type',
        'added /properties/packages/items/properties/targeting_overlay/properties/placement_selection/type',
        'missing /properties/packages/items/properties/committed_metrics/items/type',
        'missing /properties/packages/items/properties/creatives/items/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/packages/items/properties/creatives/items/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
        'missing /properties/packages/items/properties/targeting_overlay/properties/browser/uniqueItems',
        'missing /properties/packages/items/properties/targeting_overlay/properties/browser_exclude/uniqueItems',
    ],
    'media-buy/create-media-buy-request.json#/anyOf/0/properties/budget_allocation': [
        'added /additionalProperties',
        'added /type',
    ],
    'media-buy/create-media-buy-request.json#/anyOf/0/properties/packages/items': [
        'added /properties/targeting_overlay/properties/collection_selection/type',
        'added /properties/targeting_overlay/properties/frequency_cap/additionalProperties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/type',
        'added /properties/targeting_overlay/properties/placement_selection/type',
        'missing /properties/committed_metrics/items/type',
        'missing /properties/creatives/items/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/creatives/items/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
        'missing /properties/targeting_overlay/properties/browser/uniqueItems',
        'missing /properties/targeting_overlay/properties/browser_exclude/uniqueItems',
    ],
    'media-buy/create-media-buy-request.json#/anyOf/1': [
        'added /properties/budget_allocation/additionalProperties',
        'added /properties/budget_allocation/properties',
        'added /properties/budget_allocation/type',
        'added /properties/packages/items/properties/targeting_overlay/properties/collection_selection/type',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/additionalProperties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/type',
        'added /properties/packages/items/properties/targeting_overlay/properties/placement_selection/type',
        'differs /properties/budget_allocation/required',
        'missing /properties/packages/items/properties/creatives/items/properties/assets/patternProperties',
        'missing /properties/packages/items/properties/creatives/items/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/packages/items/properties/creatives/items/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
        'missing /properties/packages/items/properties/targeting_overlay/properties/browser/uniqueItems',
        'missing /properties/packages/items/properties/targeting_overlay/properties/browser_exclude/uniqueItems',
    ],
    'media-buy/create-media-buy-request.json#/anyOf/1/properties/budget_allocation': [
        'added /additionalProperties',
        'added /properties',
        'added /type',
        'differs /required',
    ],
    'media-buy/create-media-buy-request.json#/anyOf/2': [
        'added /properties/packages/items/properties/targeting_overlay/properties/collection_selection/type',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/additionalProperties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/type',
        'added /properties/packages/items/properties/targeting_overlay/properties/placement_selection/type',
        'missing /properties/packages/items/properties/creatives/items/properties/assets/patternProperties',
        'missing /properties/packages/items/properties/creatives/items/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/packages/items/properties/creatives/items/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
        'missing /properties/packages/items/properties/targeting_overlay/properties/browser/uniqueItems',
        'missing /properties/packages/items/properties/targeting_overlay/properties/browser_exclude/uniqueItems',
    ],
    # ---- core/async-response-data.json: 5 pairs, 36 facts
    'core/async-response-data.json#': [
        'added /type',
    ],
    'core/async-response-data.json#/anyOf/0': [
        'added /properties/products/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/products/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/products/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/products/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/products/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/products/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/products/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/products/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'differs /properties/products/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/required',
        'differs /properties/products/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/required',
        'missing /properties/products/items/properties/audience_evidence_selections/items/properties/attestation_evaluations/items/properties/evaluation/properties/action_binding/properties/action_type/format',
        'missing /properties/products/items/properties/format_options/items/required',
        'missing /properties/products/items/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/products/items/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
        'missing /properties/products/items/properties/placements/items/properties/format_options/items/required',
    ],
    'core/async-response-data.json#/anyOf/3': [
        'added /properties/partial_results/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/partial_results/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/partial_results/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/partial_results/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/partial_results/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/partial_results/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/partial_results/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/partial_results/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'differs /properties/partial_results/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/required',
        'differs /properties/partial_results/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/required',
        'missing /properties/partial_results/items/properties/audience_evidence_selections/items/properties/attestation_evaluations/items/properties/evaluation/properties/action_binding/properties/action_type/format',
        'missing /properties/partial_results/items/properties/format_options/items/required',
        'missing /properties/partial_results/items/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/partial_results/items/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
        'missing /properties/partial_results/items/properties/placements/items/properties/format_options/items/required',
    ],
    'core/async-response-data.json#/anyOf/5': [
        'missing /properties/products/items/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/products/items/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    'core/async-response-data.json#/anyOf/7': [
        'added /properties/results/items/properties/unsatisfied_product_changes/propertyNames',
        'missing /properties/products/items/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/products/items/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    # ---- media-buy/request-proposals-response.json: 5 pairs, 18 facts
    'media-buy/request-proposals-response.json#': [
        'missing /properties/products/items/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/products/items/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    'media-buy/request-proposals-response.json#/anyOf/0': [
        'missing /properties/products/items/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/products/items/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    'media-buy/request-proposals-response.json#/anyOf/1': [
        'missing /properties/products/items/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/products/items/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    'media-buy/request-proposals-response.json#/anyOf/2': [
        'missing /properties/products/items/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/products/items/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    'media-buy/request-proposals-response.json#/anyOf/3': [
        'added /properties/status/default',
        'added /properties/status/enum',
        'added /properties/task_id/default',
        'differs /properties/replayed/default',
        'differs /properties/status/type',
        'differs /properties/task_id/type',
        'missing /properties/products/items/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/products/items/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
        'missing /properties/status/const',
        'missing /required',
    ],
    # ---- media-buy/build-creative-response.json: 5 pairs, 10 facts
    'media-buy/build-creative-response.json#/oneOf/0': [
        'missing /properties/creative_manifest/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/creative_manifest/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
    ],
    'media-buy/build-creative-response.json#/oneOf/1': [
        'missing /properties/creative_manifests/items/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/creative_manifests/items/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
    ],
    'media-buy/build-creative-response.json#/oneOf/2': [
        'missing /properties/creatives/items/properties/variants/items/properties/creative_manifest/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/creatives/items/properties/variants/items/properties/creative_manifest/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
    ],
    'media-buy/build-creative-response.json#/oneOf/2/properties/creatives/items': [
        'missing /properties/variants/items/properties/creative_manifest/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/variants/items/properties/creative_manifest/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
    ],
    'media-buy/build-creative-response.json#/oneOf/2/properties/creatives/items/properties/variants/items': [
        'missing /properties/creative_manifest/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/creative_manifest/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
    ],
    # ---- core/wholesale-feed-event.json: 4 pairs, 68 facts
    'core/wholesale-feed-event.json#/oneOf/0': [
        'added /properties/payload/properties/product/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/payload/properties/product/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/payload/properties/product/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/payload/properties/product/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/payload/properties/product/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/payload/properties/product/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/payload/properties/product/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/payload/properties/product/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'differs /properties/payload/properties/product/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/required',
        'differs /properties/payload/properties/product/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/required',
        'missing /properties/payload/properties/canonical_product/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/payload/properties/canonical_product/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
        'missing /properties/payload/properties/product/properties/audience_evidence_selections/items/properties/attestation_evaluations/items/properties/evaluation/properties/action_binding/properties/action_type/format',
        'missing /properties/payload/properties/product/properties/format_options/items/required',
        'missing /properties/payload/properties/product/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/payload/properties/product/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
        'missing /properties/payload/properties/product/properties/placements/items/properties/format_options/items/required',
    ],
    'core/wholesale-feed-event.json#/oneOf/0/properties/payload': [
        'added /properties/product/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/product/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/product/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/product/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/product/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/product/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/product/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/product/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'differs /properties/product/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/required',
        'differs /properties/product/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/required',
        'missing /properties/canonical_product/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/canonical_product/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
        'missing /properties/product/properties/audience_evidence_selections/items/properties/attestation_evaluations/items/properties/evaluation/properties/action_binding/properties/action_type/format',
        'missing /properties/product/properties/format_options/items/required',
        'missing /properties/product/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/product/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
        'missing /properties/product/properties/placements/items/properties/format_options/items/required',
    ],
    'core/wholesale-feed-event.json#/oneOf/1': [
        'added /properties/payload/properties/product/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/payload/properties/product/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/payload/properties/product/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/payload/properties/product/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/payload/properties/product/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/payload/properties/product/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/payload/properties/product/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/payload/properties/product/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'differs /properties/payload/properties/product/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/required',
        'differs /properties/payload/properties/product/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/required',
        'missing /properties/payload/properties/canonical_product/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/payload/properties/canonical_product/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
        'missing /properties/payload/properties/product/properties/audience_evidence_selections/items/properties/attestation_evaluations/items/properties/evaluation/properties/action_binding/properties/action_type/format',
        'missing /properties/payload/properties/product/properties/format_options/items/required',
        'missing /properties/payload/properties/product/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/payload/properties/product/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
        'missing /properties/payload/properties/product/properties/placements/items/properties/format_options/items/required',
    ],
    'core/wholesale-feed-event.json#/oneOf/1/properties/payload': [
        'added /properties/product/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/product/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/product/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/product/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/product/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/product/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/product/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/product/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'differs /properties/product/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/required',
        'differs /properties/product/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/required',
        'missing /properties/canonical_product/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/canonical_product/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
        'missing /properties/product/properties/audience_evidence_selections/items/properties/attestation_evaluations/items/properties/evaluation/properties/action_binding/properties/action_type/format',
        'missing /properties/product/properties/format_options/items/required',
        'missing /properties/product/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/product/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
        'missing /properties/product/properties/placements/items/properties/format_options/items/required',
    ],
    # ---- media-buy/buy-products-request.json: 4 pairs, 38 facts
    'media-buy/buy-products-request.json#': [
        'added /properties/purchases/items/properties/targeting_overlay/properties/collection_selection/type',
        'added /properties/purchases/items/properties/targeting_overlay/properties/frequency_cap/additionalProperties',
        'added /properties/purchases/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/purchases/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/purchases/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/purchases/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/purchases/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/purchases/items/properties/targeting_overlay/properties/frequency_cap/type',
        'added /properties/purchases/items/properties/targeting_overlay/properties/placement_selection/type',
        'missing /properties/purchases/items/properties/catalog_ids/uniqueItems',
        'missing /properties/purchases/items/properties/targeting_overlay/properties/browser/uniqueItems',
        'missing /properties/purchases/items/properties/targeting_overlay/properties/browser_exclude/uniqueItems',
    ],
    'media-buy/buy-products-request.json#/anyOf/0': [
        'added /properties/purchases/items/properties/targeting_overlay/properties/collection_selection/type',
        'added /properties/purchases/items/properties/targeting_overlay/properties/frequency_cap/additionalProperties',
        'added /properties/purchases/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/purchases/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/purchases/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/purchases/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/purchases/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/purchases/items/properties/targeting_overlay/properties/frequency_cap/type',
        'added /properties/purchases/items/properties/targeting_overlay/properties/placement_selection/type',
        'missing /properties/purchases/items/properties/catalog_ids/uniqueItems',
        'missing /properties/purchases/items/properties/targeting_overlay/properties/browser/uniqueItems',
        'missing /properties/purchases/items/properties/targeting_overlay/properties/browser_exclude/uniqueItems',
    ],
    'media-buy/buy-products-request.json#/anyOf/1': [
        'added /properties/purchases/items/properties/targeting_overlay/properties/collection_selection/type',
        'added /properties/purchases/items/properties/targeting_overlay/properties/frequency_cap/additionalProperties',
        'added /properties/purchases/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/purchases/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/purchases/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/purchases/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/purchases/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/purchases/items/properties/targeting_overlay/properties/frequency_cap/type',
        'added /properties/purchases/items/properties/targeting_overlay/properties/placement_selection/type',
        'missing /properties/account/required',
        'missing /properties/purchases/items/properties/catalog_ids/uniqueItems',
        'missing /properties/purchases/items/properties/targeting_overlay/properties/browser/uniqueItems',
        'missing /properties/purchases/items/properties/targeting_overlay/properties/browser_exclude/uniqueItems',
    ],
    'media-buy/buy-products-request.json#/anyOf/1/properties/account': [
        'missing /required',
    ],
    # ---- core/audience-evidence-selection.json: 4 pairs, 9 facts
    'core/audience-evidence-selection.json#': [
        'added /properties/evidence/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'differs /properties/evidence/properties/attestation_refs/items/properties/subject/required',
        'missing /properties/attestation_evaluations/items/properties/evaluation/properties/action_binding/properties/action_type/format',
    ],
    'core/audience-evidence-selection.json#/properties/attestation_evaluations/items': [
        'missing /properties/evaluation/properties/action_binding/properties/action_type/format',
    ],
    'core/audience-evidence-selection.json#/properties/attestation_evaluations/items/properties/evaluation': [
        'missing /properties/action_binding/properties/action_type/format',
    ],
    'core/audience-evidence-selection.json#/properties/attestation_evaluations/items/properties/evaluation/allOf/1/properties/action_binding': [
        'missing /properties/action_type/format',
    ],
    # ---- media-buy/request-proposals-request.json: 4 pairs, 8 facts
    'media-buy/request-proposals-request.json#': [
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    'media-buy/request-proposals-request.json#/anyOf/0': [
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    'media-buy/request-proposals-request.json#/anyOf/1': [
        'missing /properties/account/required',
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    'media-buy/request-proposals-request.json#/anyOf/1/properties/account': [
        'missing /required',
    ],
    # ---- core/rights-attestation-evaluation.json: 4 pairs, 5 facts
    'core/rights-attestation-evaluation.json#': [
        'missing /properties/evaluation/properties/action_binding/properties/action_type/format',
        'missing /properties/reference/properties/claim_type/format',
    ],
    'core/rights-attestation-evaluation.json#/properties/evaluation': [
        'missing /properties/action_binding/properties/action_type/format',
    ],
    'core/rights-attestation-evaluation.json#/properties/evaluation/allOf/1/properties/action_binding': [
        'missing /properties/action_type/format',
    ],
    'core/rights-attestation-evaluation.json#/properties/reference': [
        'missing /properties/claim_type/format',
    ],
    # ---- protocol/get-adcp-capabilities-response.json: 4 pairs, 4 facts
    'protocol/get-adcp-capabilities-response.json#': [
        'missing /properties/media_buy/properties/execution/properties/targeting/properties/geo_places/propertyNames',
    ],
    'protocol/get-adcp-capabilities-response.json#/properties/media_buy': [
        'missing /properties/execution/properties/targeting/properties/geo_places/propertyNames',
    ],
    'protocol/get-adcp-capabilities-response.json#/properties/media_buy/properties/execution': [
        'missing /properties/targeting/properties/geo_places/propertyNames',
    ],
    'protocol/get-adcp-capabilities-response.json#/properties/media_buy/properties/execution/properties/targeting': [
        'missing /properties/geo_places/propertyNames',
    ],
    # ---- media-buy/get-media-buys-response.json: 3 pairs, 96 facts
    'media-buy/get-media-buys-response.json#': [
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_pending/items/properties/applies_to_channels',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_pending/items/properties/canonical_formats_only',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_pending/items/properties/display_name',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_pending/items/properties/experimental',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_pending/items/properties/format_option_id',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_pending/items/properties/format_schema',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_pending/items/properties/format_shape',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_pending/items/properties/locale_policy',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_pending/items/properties/macro_resolution_capabilities',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_pending/items/properties/publisher_domain',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_pending/items/properties/sample_render_url',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_pending/items/properties/seller_preference',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_pending/items/properties/technical_requirements_complete',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_pending/items/properties/tracker_execution_contract',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_pending/items/properties/v1_format_ref',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_pending/items/required',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_to_provide/items/properties/applies_to_channels',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_to_provide/items/properties/canonical_formats_only',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_to_provide/items/properties/display_name',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_to_provide/items/properties/experimental',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_to_provide/items/properties/format_option_id',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_to_provide/items/properties/format_schema',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_to_provide/items/properties/format_shape',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_to_provide/items/properties/locale_policy',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_to_provide/items/properties/macro_resolution_capabilities',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_to_provide/items/properties/publisher_domain',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_to_provide/items/properties/sample_render_url',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_to_provide/items/properties/seller_preference',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_to_provide/items/properties/technical_requirements_complete',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_to_provide/items/properties/tracker_execution_contract',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_to_provide/items/properties/v1_format_ref',
        'missing /properties/media_buys/items/properties/packages/items/properties/formats_to_provide/items/required',
    ],
    'media-buy/get-media-buys-response.json#/properties/media_buys/items': [
        'missing /properties/packages/items/properties/formats_pending/items/properties/applies_to_channels',
        'missing /properties/packages/items/properties/formats_pending/items/properties/canonical_formats_only',
        'missing /properties/packages/items/properties/formats_pending/items/properties/display_name',
        'missing /properties/packages/items/properties/formats_pending/items/properties/experimental',
        'missing /properties/packages/items/properties/formats_pending/items/properties/format_option_id',
        'missing /properties/packages/items/properties/formats_pending/items/properties/format_schema',
        'missing /properties/packages/items/properties/formats_pending/items/properties/format_shape',
        'missing /properties/packages/items/properties/formats_pending/items/properties/locale_policy',
        'missing /properties/packages/items/properties/formats_pending/items/properties/macro_resolution_capabilities',
        'missing /properties/packages/items/properties/formats_pending/items/properties/publisher_domain',
        'missing /properties/packages/items/properties/formats_pending/items/properties/sample_render_url',
        'missing /properties/packages/items/properties/formats_pending/items/properties/seller_preference',
        'missing /properties/packages/items/properties/formats_pending/items/properties/technical_requirements_complete',
        'missing /properties/packages/items/properties/formats_pending/items/properties/tracker_execution_contract',
        'missing /properties/packages/items/properties/formats_pending/items/properties/v1_format_ref',
        'missing /properties/packages/items/properties/formats_pending/items/required',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/applies_to_channels',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/canonical_formats_only',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/display_name',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/experimental',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/format_option_id',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/format_schema',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/format_shape',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/locale_policy',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/macro_resolution_capabilities',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/publisher_domain',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/sample_render_url',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/seller_preference',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/technical_requirements_complete',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/tracker_execution_contract',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/v1_format_ref',
        'missing /properties/packages/items/properties/formats_to_provide/items/required',
    ],
    'media-buy/get-media-buys-response.json#/properties/media_buys/items/properties/packages/items': [
        'missing /properties/formats_pending/items/properties/applies_to_channels',
        'missing /properties/formats_pending/items/properties/canonical_formats_only',
        'missing /properties/formats_pending/items/properties/display_name',
        'missing /properties/formats_pending/items/properties/experimental',
        'missing /properties/formats_pending/items/properties/format_option_id',
        'missing /properties/formats_pending/items/properties/format_schema',
        'missing /properties/formats_pending/items/properties/format_shape',
        'missing /properties/formats_pending/items/properties/locale_policy',
        'missing /properties/formats_pending/items/properties/macro_resolution_capabilities',
        'missing /properties/formats_pending/items/properties/publisher_domain',
        'missing /properties/formats_pending/items/properties/sample_render_url',
        'missing /properties/formats_pending/items/properties/seller_preference',
        'missing /properties/formats_pending/items/properties/technical_requirements_complete',
        'missing /properties/formats_pending/items/properties/tracker_execution_contract',
        'missing /properties/formats_pending/items/properties/v1_format_ref',
        'missing /properties/formats_pending/items/required',
        'missing /properties/formats_to_provide/items/properties/applies_to_channels',
        'missing /properties/formats_to_provide/items/properties/canonical_formats_only',
        'missing /properties/formats_to_provide/items/properties/display_name',
        'missing /properties/formats_to_provide/items/properties/experimental',
        'missing /properties/formats_to_provide/items/properties/format_option_id',
        'missing /properties/formats_to_provide/items/properties/format_schema',
        'missing /properties/formats_to_provide/items/properties/format_shape',
        'missing /properties/formats_to_provide/items/properties/locale_policy',
        'missing /properties/formats_to_provide/items/properties/macro_resolution_capabilities',
        'missing /properties/formats_to_provide/items/properties/publisher_domain',
        'missing /properties/formats_to_provide/items/properties/sample_render_url',
        'missing /properties/formats_to_provide/items/properties/seller_preference',
        'missing /properties/formats_to_provide/items/properties/technical_requirements_complete',
        'missing /properties/formats_to_provide/items/properties/tracker_execution_contract',
        'missing /properties/formats_to_provide/items/properties/v1_format_ref',
        'missing /properties/formats_to_provide/items/required',
    ],
    # ---- core/audience-evidence.json: 3 pairs, 15 facts
    'core/audience-evidence.json#': [
        'added /properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/attestation_refs/items/properties/subject/properties',
        'added /properties/attestation_refs/items/properties/subject/properties',
        'added /properties/attestation_refs/items/properties/subject/properties',
        'differs /properties/attestation_refs/items/properties/subject/required',
    ],
    'core/audience-evidence.json#/properties/attestation_refs/items': [
        'added /properties/subject/additionalProperties',
        'added /properties/subject/properties',
        'added /properties/subject/properties',
        'added /properties/subject/properties',
        'differs /properties/subject/required',
    ],
    'core/audience-evidence.json#/properties/attestation_refs/items/allOf/1/properties/subject': [
        'added /additionalProperties',
        'added /properties',
        'added /properties',
        'added /properties',
        'differs /required',
    ],
    # ---- media-buy/list-products-response.json: 3 pairs, 6 facts
    'media-buy/list-products-response.json#': [
        'missing /properties/products/items/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/products/items/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    'media-buy/list-products-response.json#/oneOf/0': [
        'missing /properties/products/items/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/products/items/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    'media-buy/list-products-response.json#/oneOf/1': [
        'missing /properties/products/items/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/products/items/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    # ---- governance/check-governance-response.json: 3 pairs, 3 facts
    'governance/check-governance-response.json#': [
        'missing /properties/runtime_attestation_evaluations/items/properties/action_binding/properties/action_type/format',
    ],
    'governance/check-governance-response.json#/properties/runtime_attestation_evaluations/items': [
        'missing /properties/action_binding/properties/action_type/format',
    ],
    'governance/check-governance-response.json#/properties/runtime_attestation_evaluations/items/allOf/1/properties/action_binding': [
        'missing /properties/action_type/format',
    ],
    # ---- compliance/task-completion-data.json: 2 pairs, 66 facts
    'compliance/task-completion-data.json#/anyOf/0': [
        'added /properties/products/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/products/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/products/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/products/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/products/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/products/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/products/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/products/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'differs /properties/products/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/required',
        'differs /properties/products/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/required',
        'missing /properties/products/items/properties/audience_evidence_selections/items/properties/attestation_evaluations/items/properties/evaluation/properties/action_binding/properties/action_type/format',
        'missing /properties/products/items/properties/format_options/items/required',
        'missing /properties/products/items/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/products/items/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
        'missing /properties/products/items/properties/placements/items/properties/format_options/items/required',
    ],
    'compliance/task-completion-data.json#/anyOf/2': [
        'added /properties',
        'added /properties',
        'added /properties',
        'added /properties',
        'added /properties',
        'added /properties',
        'added /properties',
        'added /properties',
        'added /properties',
        'added /properties',
        'added /properties',
        'added /properties',
        'added /properties/packages/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/packages/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/packages/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/packages/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'differs /properties/packages/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/required',
        'differs /required',
        'missing /properties/packages/items/properties/audience_evidence_selections/items/properties/attestation_evaluations/items/properties/evaluation/properties/action_binding/properties/action_type/format',
        'missing /properties/packages/items/properties/formats_pending/items/properties/applies_to_channels',
        'missing /properties/packages/items/properties/formats_pending/items/properties/canonical_formats_only',
        'missing /properties/packages/items/properties/formats_pending/items/properties/display_name',
        'missing /properties/packages/items/properties/formats_pending/items/properties/experimental',
        'missing /properties/packages/items/properties/formats_pending/items/properties/format_option_id',
        'missing /properties/packages/items/properties/formats_pending/items/properties/format_schema',
        'missing /properties/packages/items/properties/formats_pending/items/properties/format_shape',
        'missing /properties/packages/items/properties/formats_pending/items/properties/locale_policy',
        'missing /properties/packages/items/properties/formats_pending/items/properties/macro_resolution_capabilities',
        'missing /properties/packages/items/properties/formats_pending/items/properties/publisher_domain',
        'missing /properties/packages/items/properties/formats_pending/items/properties/sample_render_url',
        'missing /properties/packages/items/properties/formats_pending/items/properties/seller_preference',
        'missing /properties/packages/items/properties/formats_pending/items/properties/technical_requirements_complete',
        'missing /properties/packages/items/properties/formats_pending/items/properties/tracker_execution_contract',
        'missing /properties/packages/items/properties/formats_pending/items/properties/v1_format_ref',
        'missing /properties/packages/items/properties/formats_pending/items/required',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/applies_to_channels',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/canonical_formats_only',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/display_name',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/experimental',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/format_option_id',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/format_schema',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/format_shape',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/locale_policy',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/macro_resolution_capabilities',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/publisher_domain',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/sample_render_url',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/seller_preference',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/technical_requirements_complete',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/tracker_execution_contract',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/v1_format_ref',
        'missing /properties/packages/items/properties/formats_to_provide/items/required',
    ],
    # ---- media-buy/package-request.json: 2 pairs, 15 facts
    'media-buy/package-request.json#': [
        'added /properties/targeting_overlay/properties/collection_selection/type',
        'added /properties/targeting_overlay/properties/frequency_cap/additionalProperties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/type',
        'added /properties/targeting_overlay/properties/placement_selection/type',
        'missing /properties/creatives/items/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/creatives/items/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
        'missing /properties/targeting_overlay/properties/browser/uniqueItems',
        'missing /properties/targeting_overlay/properties/browser_exclude/uniqueItems',
    ],
    'media-buy/package-request.json#/properties/creatives/items': [
        'missing /properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
    ],
    # ---- media-buy/package-update.json: 2 pairs, 15 facts
    'media-buy/package-update.json#': [
        'added /properties/targeting_overlay/properties/collection_selection/type',
        'added /properties/targeting_overlay/properties/frequency_cap/additionalProperties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/type',
        'added /properties/targeting_overlay/properties/placement_selection/type',
        'missing /properties/creatives/items/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/creatives/items/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
        'missing /properties/targeting_overlay/properties/browser/uniqueItems',
        'missing /properties/targeting_overlay/properties/browser_exclude/uniqueItems',
    ],
    'media-buy/package-update.json#/properties/creatives/items': [
        'missing /properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
    ],
    # ---- creative/list-creatives-response.json: 2 pairs, 8 facts
    'creative/list-creatives-response.json#': [
        'missing /properties/creatives/items/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/creatives/items/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
        'missing /properties/creatives/items/properties/rights_attestation_evaluations/items/properties/evaluation/properties/action_binding/properties/action_type/format',
        'missing /properties/creatives/items/properties/rights_attestation_evaluations/items/properties/reference/properties/claim_type/format',
    ],
    'creative/list-creatives-response.json#/properties/creatives/items': [
        'missing /properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
        'missing /properties/rights_attestation_evaluations/items/properties/evaluation/properties/action_binding/properties/action_type/format',
        'missing /properties/rights_attestation_evaluations/items/properties/reference/properties/claim_type/format',
    ],
    # ---- creative/preview-creative-request.json: 2 pairs, 6 facts
    'creative/preview-creative-request.json#': [
        'missing /properties/creative_manifest/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/creative_manifest/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
        'missing /properties/requests/items/properties/creative_manifest/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/requests/items/properties/creative_manifest/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
    ],
    'creative/preview-creative-request.json#/properties/requests/items': [
        'missing /properties/creative_manifest/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/creative_manifest/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
    ],
    # ---- creative/get-creative-delivery-response.json: 2 pairs, 4 facts
    'creative/get-creative-delivery-response.json#': [
        'missing /properties/creatives/items/properties/variants/items/properties/manifest/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/creatives/items/properties/variants/items/properties/manifest/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
    ],
    'creative/get-creative-delivery-response.json#/properties/creatives/items': [
        'missing /properties/variants/items/properties/manifest/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/variants/items/properties/manifest/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
    ],
    # ---- creative/sync-creatives-request.json: 2 pairs, 4 facts
    'creative/sync-creatives-request.json#': [
        'missing /properties/creatives/items/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/creatives/items/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
    ],
    'creative/sync-creatives-request.json#/properties/creatives/items': [
        'missing /properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
    ],
    # ---- creative/validate-input-request.json: 2 pairs, 4 facts
    'creative/validate-input-request.json#': [
        'missing /properties/manifest/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/manifest/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
        'missing /properties/targets/items/required',
    ],
    'creative/validate-input-request.json#/properties/targets/items': [
        'missing /required',
    ],
    # ---- core/targeting-overlay-support.json: 2 pairs, 3 facts
    'core/targeting-overlay-support.json#': [
        'missing /properties/geo_places/properties/systems/propertyNames',
        'missing /properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    'core/targeting-overlay-support.json#/definitions/placeSupport': [
        'missing /properties/systems/propertyNames',
    ],
    # ---- brand/acquire-rights-response.json: 2 pairs, 2 facts
    'brand/acquire-rights-response.json#/oneOf/0': [
        'missing /properties/rights_constraint/properties/attestation_refs/items/properties/claim_type/format',
    ],
    'brand/acquire-rights-response.json#/oneOf/0/properties/rights_constraint': [
        'missing /properties/attestation_refs/items/properties/claim_type/format',
    ],
    # ---- brand/update-rights-response.json: 2 pairs, 2 facts
    'brand/update-rights-response.json#/oneOf/0': [
        'missing /properties/rights_constraint/properties/attestation_refs/items/properties/claim_type/format',
    ],
    'brand/update-rights-response.json#/oneOf/0/properties/rights_constraint': [
        'missing /properties/attestation_refs/items/properties/claim_type/format',
    ],
    # ---- compliance/comply-test-controller-response.json: 2 pairs, 2 facts
    'compliance/comply-test-controller-response.json#/oneOf/6/properties/recorded_calls/items/oneOf/0': [
        'missing /properties/payload/maxLength',
    ],
    'compliance/comply-test-controller-response.json#/oneOf/6/properties/recorded_calls/items/oneOf/1': [
        'missing /properties/payload/maxLength',
    ],
    # ---- core/rights-constraint.json: 2 pairs, 2 facts
    'core/rights-constraint.json#': [
        'missing /properties/attestation_refs/items/properties/claim_type/format',
    ],
    'core/rights-constraint.json#/properties/attestation_refs/items': [
        'missing /properties/claim_type/format',
    ],
    # ---- core/media-buy.json: 1 pairs, 38 facts
    'core/media-buy.json#': [
        'added /properties/packages/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/packages/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/packages/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/packages/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'differs /properties/packages/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/required',
        'missing /properties/packages/items/properties/audience_evidence_selections/items/properties/attestation_evaluations/items/properties/evaluation/properties/action_binding/properties/action_type/format',
        'missing /properties/packages/items/properties/formats_pending/items/properties/applies_to_channels',
        'missing /properties/packages/items/properties/formats_pending/items/properties/canonical_formats_only',
        'missing /properties/packages/items/properties/formats_pending/items/properties/display_name',
        'missing /properties/packages/items/properties/formats_pending/items/properties/experimental',
        'missing /properties/packages/items/properties/formats_pending/items/properties/format_option_id',
        'missing /properties/packages/items/properties/formats_pending/items/properties/format_schema',
        'missing /properties/packages/items/properties/formats_pending/items/properties/format_shape',
        'missing /properties/packages/items/properties/formats_pending/items/properties/locale_policy',
        'missing /properties/packages/items/properties/formats_pending/items/properties/macro_resolution_capabilities',
        'missing /properties/packages/items/properties/formats_pending/items/properties/publisher_domain',
        'missing /properties/packages/items/properties/formats_pending/items/properties/sample_render_url',
        'missing /properties/packages/items/properties/formats_pending/items/properties/seller_preference',
        'missing /properties/packages/items/properties/formats_pending/items/properties/technical_requirements_complete',
        'missing /properties/packages/items/properties/formats_pending/items/properties/tracker_execution_contract',
        'missing /properties/packages/items/properties/formats_pending/items/properties/v1_format_ref',
        'missing /properties/packages/items/properties/formats_pending/items/required',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/applies_to_channels',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/canonical_formats_only',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/display_name',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/experimental',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/format_option_id',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/format_schema',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/format_shape',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/locale_policy',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/macro_resolution_capabilities',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/publisher_domain',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/sample_render_url',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/seller_preference',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/technical_requirements_complete',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/tracker_execution_contract',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/v1_format_ref',
        'missing /properties/packages/items/properties/formats_to_provide/items/required',
    ],
    # ---- core/package.json: 1 pairs, 38 facts
    'core/package.json#': [
        'added /properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'differs /properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/required',
        'missing /properties/audience_evidence_selections/items/properties/attestation_evaluations/items/properties/evaluation/properties/action_binding/properties/action_type/format',
        'missing /properties/formats_pending/items/properties/applies_to_channels',
        'missing /properties/formats_pending/items/properties/canonical_formats_only',
        'missing /properties/formats_pending/items/properties/display_name',
        'missing /properties/formats_pending/items/properties/experimental',
        'missing /properties/formats_pending/items/properties/format_option_id',
        'missing /properties/formats_pending/items/properties/format_schema',
        'missing /properties/formats_pending/items/properties/format_shape',
        'missing /properties/formats_pending/items/properties/locale_policy',
        'missing /properties/formats_pending/items/properties/macro_resolution_capabilities',
        'missing /properties/formats_pending/items/properties/publisher_domain',
        'missing /properties/formats_pending/items/properties/sample_render_url',
        'missing /properties/formats_pending/items/properties/seller_preference',
        'missing /properties/formats_pending/items/properties/technical_requirements_complete',
        'missing /properties/formats_pending/items/properties/tracker_execution_contract',
        'missing /properties/formats_pending/items/properties/v1_format_ref',
        'missing /properties/formats_pending/items/required',
        'missing /properties/formats_to_provide/items/properties/applies_to_channels',
        'missing /properties/formats_to_provide/items/properties/canonical_formats_only',
        'missing /properties/formats_to_provide/items/properties/display_name',
        'missing /properties/formats_to_provide/items/properties/experimental',
        'missing /properties/formats_to_provide/items/properties/format_option_id',
        'missing /properties/formats_to_provide/items/properties/format_schema',
        'missing /properties/formats_to_provide/items/properties/format_shape',
        'missing /properties/formats_to_provide/items/properties/locale_policy',
        'missing /properties/formats_to_provide/items/properties/macro_resolution_capabilities',
        'missing /properties/formats_to_provide/items/properties/publisher_domain',
        'missing /properties/formats_to_provide/items/properties/sample_render_url',
        'missing /properties/formats_to_provide/items/properties/seller_preference',
        'missing /properties/formats_to_provide/items/properties/technical_requirements_complete',
        'missing /properties/formats_to_provide/items/properties/tracker_execution_contract',
        'missing /properties/formats_to_provide/items/properties/v1_format_ref',
        'missing /properties/formats_to_provide/items/required',
    ],
    # ---- media-buy/create-media-buy-response.json: 1 pairs, 38 facts
    'media-buy/create-media-buy-response.json#/oneOf/0': [
        'added /properties/packages/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/packages/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/packages/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/packages/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'differs /properties/packages/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/required',
        'missing /properties/packages/items/properties/audience_evidence_selections/items/properties/attestation_evaluations/items/properties/evaluation/properties/action_binding/properties/action_type/format',
        'missing /properties/packages/items/properties/formats_pending/items/properties/applies_to_channels',
        'missing /properties/packages/items/properties/formats_pending/items/properties/canonical_formats_only',
        'missing /properties/packages/items/properties/formats_pending/items/properties/display_name',
        'missing /properties/packages/items/properties/formats_pending/items/properties/experimental',
        'missing /properties/packages/items/properties/formats_pending/items/properties/format_option_id',
        'missing /properties/packages/items/properties/formats_pending/items/properties/format_schema',
        'missing /properties/packages/items/properties/formats_pending/items/properties/format_shape',
        'missing /properties/packages/items/properties/formats_pending/items/properties/locale_policy',
        'missing /properties/packages/items/properties/formats_pending/items/properties/macro_resolution_capabilities',
        'missing /properties/packages/items/properties/formats_pending/items/properties/publisher_domain',
        'missing /properties/packages/items/properties/formats_pending/items/properties/sample_render_url',
        'missing /properties/packages/items/properties/formats_pending/items/properties/seller_preference',
        'missing /properties/packages/items/properties/formats_pending/items/properties/technical_requirements_complete',
        'missing /properties/packages/items/properties/formats_pending/items/properties/tracker_execution_contract',
        'missing /properties/packages/items/properties/formats_pending/items/properties/v1_format_ref',
        'missing /properties/packages/items/properties/formats_pending/items/required',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/applies_to_channels',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/canonical_formats_only',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/display_name',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/experimental',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/format_option_id',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/format_schema',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/format_shape',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/locale_policy',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/macro_resolution_capabilities',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/publisher_domain',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/sample_render_url',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/seller_preference',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/technical_requirements_complete',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/tracker_execution_contract',
        'missing /properties/packages/items/properties/formats_to_provide/items/properties/v1_format_ref',
        'missing /properties/packages/items/properties/formats_to_provide/items/required',
    ],
    # ---- media-buy/update-media-buy-response.json: 1 pairs, 38 facts
    'media-buy/update-media-buy-response.json#/oneOf/0': [
        'added /properties/affected_packages/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/affected_packages/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/affected_packages/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/affected_packages/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'differs /properties/affected_packages/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/required',
        'missing /properties/affected_packages/items/properties/audience_evidence_selections/items/properties/attestation_evaluations/items/properties/evaluation/properties/action_binding/properties/action_type/format',
        'missing /properties/affected_packages/items/properties/formats_pending/items/properties/applies_to_channels',
        'missing /properties/affected_packages/items/properties/formats_pending/items/properties/canonical_formats_only',
        'missing /properties/affected_packages/items/properties/formats_pending/items/properties/display_name',
        'missing /properties/affected_packages/items/properties/formats_pending/items/properties/experimental',
        'missing /properties/affected_packages/items/properties/formats_pending/items/properties/format_option_id',
        'missing /properties/affected_packages/items/properties/formats_pending/items/properties/format_schema',
        'missing /properties/affected_packages/items/properties/formats_pending/items/properties/format_shape',
        'missing /properties/affected_packages/items/properties/formats_pending/items/properties/locale_policy',
        'missing /properties/affected_packages/items/properties/formats_pending/items/properties/macro_resolution_capabilities',
        'missing /properties/affected_packages/items/properties/formats_pending/items/properties/publisher_domain',
        'missing /properties/affected_packages/items/properties/formats_pending/items/properties/sample_render_url',
        'missing /properties/affected_packages/items/properties/formats_pending/items/properties/seller_preference',
        'missing /properties/affected_packages/items/properties/formats_pending/items/properties/technical_requirements_complete',
        'missing /properties/affected_packages/items/properties/formats_pending/items/properties/tracker_execution_contract',
        'missing /properties/affected_packages/items/properties/formats_pending/items/properties/v1_format_ref',
        'missing /properties/affected_packages/items/properties/formats_pending/items/required',
        'missing /properties/affected_packages/items/properties/formats_to_provide/items/properties/applies_to_channels',
        'missing /properties/affected_packages/items/properties/formats_to_provide/items/properties/canonical_formats_only',
        'missing /properties/affected_packages/items/properties/formats_to_provide/items/properties/display_name',
        'missing /properties/affected_packages/items/properties/formats_to_provide/items/properties/experimental',
        'missing /properties/affected_packages/items/properties/formats_to_provide/items/properties/format_option_id',
        'missing /properties/affected_packages/items/properties/formats_to_provide/items/properties/format_schema',
        'missing /properties/affected_packages/items/properties/formats_to_provide/items/properties/format_shape',
        'missing /properties/affected_packages/items/properties/formats_to_provide/items/properties/locale_policy',
        'missing /properties/affected_packages/items/properties/formats_to_provide/items/properties/macro_resolution_capabilities',
        'missing /properties/affected_packages/items/properties/formats_to_provide/items/properties/publisher_domain',
        'missing /properties/affected_packages/items/properties/formats_to_provide/items/properties/sample_render_url',
        'missing /properties/affected_packages/items/properties/formats_to_provide/items/properties/seller_preference',
        'missing /properties/affected_packages/items/properties/formats_to_provide/items/properties/technical_requirements_complete',
        'missing /properties/affected_packages/items/properties/formats_to_provide/items/properties/tracker_execution_contract',
        'missing /properties/affected_packages/items/properties/formats_to_provide/items/properties/v1_format_ref',
        'missing /properties/affected_packages/items/properties/formats_to_provide/items/required',
    ],
    # ---- media-buy/update-media-buy-request.json: 1 pairs, 34 facts
    'media-buy/update-media-buy-request.json#': [
        'added /properties/frequency_cap/additionalProperties',
        'added /properties/frequency_cap/properties',
        'added /properties/frequency_cap/properties',
        'added /properties/frequency_cap/properties',
        'added /properties/frequency_cap/properties',
        'added /properties/frequency_cap/properties',
        'added /properties/frequency_cap/required',
        'added /properties/frequency_cap/type',
        'added /properties/new_packages/items/properties/targeting_overlay/properties/collection_selection/type',
        'added /properties/new_packages/items/properties/targeting_overlay/properties/frequency_cap/additionalProperties',
        'added /properties/new_packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/new_packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/new_packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/new_packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/new_packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/new_packages/items/properties/targeting_overlay/properties/frequency_cap/type',
        'added /properties/new_packages/items/properties/targeting_overlay/properties/placement_selection/type',
        'added /properties/packages/items/properties/targeting_overlay/properties/collection_selection/type',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/additionalProperties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/type',
        'added /properties/packages/items/properties/targeting_overlay/properties/placement_selection/type',
        'missing /properties/new_packages/items/properties/creatives/items/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/new_packages/items/properties/creatives/items/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
        'missing /properties/new_packages/items/properties/targeting_overlay/properties/browser/uniqueItems',
        'missing /properties/new_packages/items/properties/targeting_overlay/properties/browser_exclude/uniqueItems',
        'missing /properties/packages/items/properties/creatives/items/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/packages/items/properties/creatives/items/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
        'missing /properties/packages/items/properties/targeting_overlay/properties/browser/uniqueItems',
        'missing /properties/packages/items/properties/targeting_overlay/properties/browser_exclude/uniqueItems',
    ],
    # ---- media-buy/control-media-buy-request.json: 1 pairs, 19 facts
    'media-buy/control-media-buy-request.json#': [
        'added /properties/frequency_cap/additionalProperties',
        'added /properties/frequency_cap/properties',
        'added /properties/frequency_cap/properties',
        'added /properties/frequency_cap/properties',
        'added /properties/frequency_cap/properties',
        'added /properties/frequency_cap/properties',
        'added /properties/frequency_cap/required',
        'added /properties/frequency_cap/type',
        'added /properties/packages/items/properties/targeting_overlay/properties/collection_selection/type',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/additionalProperties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/packages/items/properties/targeting_overlay/properties/frequency_cap/type',
        'added /properties/packages/items/properties/targeting_overlay/properties/placement_selection/type',
        'missing /properties/packages/items/properties/targeting_overlay/properties/browser/uniqueItems',
        'missing /properties/packages/items/properties/targeting_overlay/properties/browser_exclude/uniqueItems',
    ],
    # ---- core/package-format-snapshot.json: 1 pairs, 16 facts
    'core/package-format-snapshot.json#': [
        'missing /properties/applies_to_channels',
        'missing /properties/canonical_formats_only',
        'missing /properties/display_name',
        'missing /properties/experimental',
        'missing /properties/format_option_id',
        'missing /properties/format_schema',
        'missing /properties/format_shape',
        'missing /properties/locale_policy',
        'missing /properties/macro_resolution_capabilities',
        'missing /properties/publisher_domain',
        'missing /properties/sample_render_url',
        'missing /properties/seller_preference',
        'missing /properties/technical_requirements_complete',
        'missing /properties/tracker_execution_contract',
        'missing /properties/v1_format_ref',
        'missing /required',
    ],
    # ---- trusted-match/available-package.json: 1 pairs, 16 facts
    'trusted-match/available-package.json#': [
        'missing /properties/format_options/items/properties/applies_to_channels',
        'missing /properties/format_options/items/properties/canonical_formats_only',
        'missing /properties/format_options/items/properties/display_name',
        'missing /properties/format_options/items/properties/experimental',
        'missing /properties/format_options/items/properties/format_option_id',
        'missing /properties/format_options/items/properties/format_schema',
        'missing /properties/format_options/items/properties/format_shape',
        'missing /properties/format_options/items/properties/locale_policy',
        'missing /properties/format_options/items/properties/macro_resolution_capabilities',
        'missing /properties/format_options/items/properties/publisher_domain',
        'missing /properties/format_options/items/properties/sample_render_url',
        'missing /properties/format_options/items/properties/seller_preference',
        'missing /properties/format_options/items/properties/technical_requirements_complete',
        'missing /properties/format_options/items/properties/tracker_execution_contract',
        'missing /properties/format_options/items/properties/v1_format_ref',
        'missing /properties/format_options/items/required',
    ],
    # ---- core/async-response-refs/media-buy/get-products-async-response-input-required.json: 1 pairs, 15 facts
    'core/async-response-refs/media-buy/get-products-async-response-input-required.json#': [
        'added /properties/partial_results/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/partial_results/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/partial_results/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/partial_results/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/partial_results/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/partial_results/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/partial_results/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/partial_results/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'differs /properties/partial_results/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/required',
        'differs /properties/partial_results/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/required',
        'missing /properties/partial_results/items/properties/audience_evidence_selections/items/properties/attestation_evaluations/items/properties/evaluation/properties/action_binding/properties/action_type/format',
        'missing /properties/partial_results/items/properties/format_options/items/required',
        'missing /properties/partial_results/items/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/partial_results/items/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
        'missing /properties/partial_results/items/properties/placements/items/properties/format_options/items/required',
    ],
    # ---- core/product.json: 1 pairs, 15 facts
    'core/product.json#': [
        'added /properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'differs /properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/required',
        'differs /properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/required',
        'missing /properties/audience_evidence_selections/items/properties/attestation_evaluations/items/properties/evaluation/properties/action_binding/properties/action_type/format',
        'missing /properties/format_options/items/required',
        'missing /properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
        'missing /properties/placements/items/properties/format_options/items/required',
    ],
    # ---- media-buy/get-products-async-response-input-required.json: 1 pairs, 15 facts
    'media-buy/get-products-async-response-input-required.json#': [
        'added /properties/partial_results/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/partial_results/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/partial_results/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/partial_results/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/partial_results/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/partial_results/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/partial_results/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/partial_results/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'differs /properties/partial_results/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/required',
        'differs /properties/partial_results/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/required',
        'missing /properties/partial_results/items/properties/audience_evidence_selections/items/properties/attestation_evaluations/items/properties/evaluation/properties/action_binding/properties/action_type/format',
        'missing /properties/partial_results/items/properties/format_options/items/required',
        'missing /properties/partial_results/items/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/partial_results/items/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
        'missing /properties/partial_results/items/properties/placements/items/properties/format_options/items/required',
    ],
    # ---- media-buy/get-products-response.json: 1 pairs, 15 facts
    'media-buy/get-products-response.json#': [
        'added /properties/products/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/products/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/products/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/products/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/products/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/additionalProperties',
        'added /properties/products/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/products/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'added /properties/products/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/properties',
        'differs /properties/products/items/properties/audience_evidence/items/properties/attestation_refs/items/properties/subject/required',
        'differs /properties/products/items/properties/audience_evidence_selections/items/properties/evidence/properties/attestation_refs/items/properties/subject/required',
        'missing /properties/products/items/properties/audience_evidence_selections/items/properties/attestation_evaluations/items/properties/evaluation/properties/action_binding/properties/action_type/format',
        'missing /properties/products/items/properties/format_options/items/required',
        'missing /properties/products/items/properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/products/items/properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
        'missing /properties/products/items/properties/placements/items/properties/format_options/items/required',
    ],
    # ---- media-buy/product-purchase-input.json: 1 pairs, 12 facts
    'media-buy/product-purchase-input.json#': [
        'added /properties/targeting_overlay/properties/collection_selection/type',
        'added /properties/targeting_overlay/properties/frequency_cap/additionalProperties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/type',
        'added /properties/targeting_overlay/properties/placement_selection/type',
        'missing /properties/catalog_ids/uniqueItems',
        'missing /properties/targeting_overlay/properties/browser/uniqueItems',
        'missing /properties/targeting_overlay/properties/browser_exclude/uniqueItems',
    ],
    # ---- core/targeting-input.json: 1 pairs, 11 facts
    'core/targeting-input.json#': [
        'added /properties/collection_selection/type',
        'added /properties/frequency_cap/additionalProperties',
        'added /properties/frequency_cap/properties',
        'added /properties/frequency_cap/properties',
        'added /properties/frequency_cap/properties',
        'added /properties/frequency_cap/properties',
        'added /properties/frequency_cap/properties',
        'added /properties/frequency_cap/type',
        'added /properties/placement_selection/type',
        'missing /properties/browser/uniqueItems',
        'missing /properties/browser_exclude/uniqueItems',
    ],
    # ---- media-buy/package-control.json: 1 pairs, 11 facts
    'media-buy/package-control.json#': [
        'added /properties/targeting_overlay/properties/collection_selection/type',
        'added /properties/targeting_overlay/properties/frequency_cap/additionalProperties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/properties',
        'added /properties/targeting_overlay/properties/frequency_cap/type',
        'added /properties/targeting_overlay/properties/placement_selection/type',
        'missing /properties/targeting_overlay/properties/browser/uniqueItems',
        'missing /properties/targeting_overlay/properties/browser_exclude/uniqueItems',
    ],
    # ---- media-buy/decline-proposals-response.json: 1 pairs, 6 facts
    'media-buy/decline-proposals-response.json#/anyOf/1': [
        'added /properties/status/default',
        'added /properties/task_id/default',
        'differs /properties/replayed/default',
        'differs /properties/status/type',
        'differs /properties/task_id/type',
        'missing /required',
    ],
    # ---- media-buy/build-creative-request.json: 1 pairs, 5 facts
    'media-buy/build-creative-request.json#': [
        'missing /properties/creative_manifest/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/creative_manifest/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
        'missing /properties/creative_representation_set/properties/representations/items/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/creative_representation_set/properties/representations/items/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
        'missing /properties/representation_destination/properties/format_option/required',
    ],
    # ---- core/canonical-product.json: 1 pairs, 2 facts
    'core/canonical-product.json#': [
        'missing /properties/overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    # ---- core/creative-asset.json: 1 pairs, 2 facts
    'core/creative-asset.json#': [
        'missing /properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
    ],
    # ---- core/creative-manifest.json: 1 pairs, 2 facts
    'core/creative-manifest.json#': [
        'missing /properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
    ],
    # ---- core/creative-representation-set.json: 1 pairs, 2 facts
    'core/creative-representation-set.json#': [
        'missing /properties/representations/items/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/representations/items/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
    ],
    # ---- core/creative-representation.json: 1 pairs, 2 facts
    'core/creative-representation.json#': [
        'missing /properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
    ],
    # ---- core/creative-variant.json: 1 pairs, 2 facts
    'core/creative-variant.json#': [
        'missing /properties/manifest/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/manifest/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
    ],
    # ---- core/targeting-overlay-requirements.json: 1 pairs, 2 facts
    'core/targeting-overlay-requirements.json#': [
        'missing /properties/geo_places/properties/systems/propertyNames',
        'missing /properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    # ---- creative/get-creative-features-request.json: 1 pairs, 2 facts
    'creative/get-creative-features-request.json#': [
        'missing /properties/creative_manifest/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/creative_manifest/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
    ],
    # ---- creative/preview-creative-response.json: 1 pairs, 2 facts
    'creative/preview-creative-response.json#/oneOf/2': [
        'missing /properties/manifest/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/manifest/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
    ],
    # ---- media-buy/get-products-request.json: 1 pairs, 2 facts
    'media-buy/get-products-request.json#': [
        'missing /properties/required_overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/required_overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    # ---- media-buy/list-products-request.json: 1 pairs, 2 facts
    'media-buy/list-products-request.json#': [
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/criteria/properties/required_overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    # ---- media-buy/product-discovery-criteria.json: 1 pairs, 2 facts
    'media-buy/product-discovery-criteria.json#': [
        'missing /properties/required_overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/required_overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    # ---- media-buy/refine-proposals-request.json: 1 pairs, 2 facts
    'media-buy/refine-proposals-request.json#': [
        'missing /properties/refinements/items/properties/criteria/properties/required_overlay_support/properties/geo_places/properties/systems/propertyNames',
        'missing /properties/refinements/items/properties/criteria/properties/required_overlay_support/properties/geo_places_exclude/properties/systems/propertyNames',
    ],
    # ---- trusted-match/context-match-response.json: 1 pairs, 2 facts
    'trusted-match/context-match-response.json#': [
        'missing /properties/offers/items/properties/creative_manifest/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/offers/items/properties/creative_manifest/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
    ],
    # ---- trusted-match/offer.json: 1 pairs, 2 facts
    'trusted-match/offer.json#': [
        'missing /properties/creative_manifest/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/creative_manifest/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
    ],
    # ---- trusted-match/provider-context-match-response.json: 1 pairs, 2 facts
    'trusted-match/provider-context-match-response.json#': [
        'missing /properties/offers/items/properties/creative_manifest/properties/component_assets/additionalProperties/patternProperties',
        'missing /properties/offers/items/properties/creative_manifest/properties/rights/items/properties/attestation_refs/items/properties/claim_type/format',
    ],
    # ---- core/format.json: 1 pairs, 1 facts
    'core/format.json#': [
        'missing /properties/canonical_parameters/required',
    ],
    # ---- core/geo-place-requirement.json: 1 pairs, 1 facts
    'core/geo-place-requirement.json#': [
        'missing /properties/systems/propertyNames',
    ],
    # ---- core/mcp-webhook-payload.json: 1 pairs, 1 facts
    'core/mcp-webhook-payload.json#': [
        'added /properties/result/type',
    ],
    # ---- core/placement.json: 1 pairs, 1 facts
    'core/placement.json#': [
        'missing /properties/format_options/items/required',
    ],
    # ---- core/postal-area.json: 1 pairs, 1 facts
    'core/postal-area.json#/anyOf/0/allOf/0/anyOf/3': [
        'missing /properties/country/pattern',
    ],
    # ---- core/postal-country-system.json: 1 pairs, 1 facts
    'core/postal-country-system.json#/anyOf/3': [
        'missing /properties/country/pattern',
    ],
    # ---- core/product-format-declaration.json: 1 pairs, 1 facts
    'core/product-format-declaration.json#': [
        'missing /required',
    ],
    # ---- core/representation-destination.json: 1 pairs, 1 facts
    'core/representation-destination.json#': [
        'missing /properties/format_option/required',
    ],
    # ---- core/transformer.json: 1 pairs, 1 facts
    'core/transformer.json#': [
        'missing /properties/input_formats/items/required',
    ],
    # ---- creative/list-creative-formats-response.json: 1 pairs, 1 facts
    'creative/list-creative-formats-response.json#': [
        'missing /properties/formats/items/properties/canonical_parameters/required',
    ],
    # ---- creative/list-transformers-response.json: 1 pairs, 1 facts
    'creative/list-transformers-response.json#': [
        'missing /properties/transformers/items/properties/input_formats/items/required',
    ],
    # ---- media-buy/list-creative-formats-response.json: 1 pairs, 1 facts
    'media-buy/list-creative-formats-response.json#': [
        'missing /properties/formats/items/properties/canonical_parameters/required',
    ],
}


#: **THE ``added`` DIRECTION, CLASSIFIED BEFORE IT WAS PINNED.**  A model that ADDS a fact
#: is NARROWER than its document: §2 forbids it outright and no declaration absorbs it,
#: because such a model refuses traffic the document admits.  These are the pairs red on
#: that direction ALONE -- ``ComparisonResult.outcome``'s ``model_adds_a_fact`` -- and the
#: sentence per pair says which of two things it is: a real narrowing, or a fact the
#: DOCUMENT states somewhere the comparison does not read.
#:
#: **All 8 are the second, and each was read off the document's own text.  Three causes:**
#:
#: * **a union root's ``type``, entailed by every arm and stated in its own text by all but
#:   three** -- ``_base.entailed_types``' first clause asks a branch for its OWN ``type``
#:   word, and two arms of ``core/async-response-data.json`` state it inside their single
#:   ``allOf`` conjunct while a third entails it through its own ``oneOf``.  The same
#:   function's docstring already records the one-level-in version of this
#:   (``_branch_target``, for a branch that is a bare local ``$ref``).
#: * **a conjunct the fold DROPS.**  ``harness._composed`` folds
#:   ``create-media-buy-request``'s ``budget_allocation`` to
#:   ``{description, properties, required}`` -- the hoisted conjunct's ``oneOf``, with the
#:   two branches that state ``type: object`` and ``additionalProperties: false``, is gone.
#:   ``_entails_type`` answers ``False`` on the folded node and ``True`` on the node as the
#:   document states it, which is the whole of the finding.
#: * **a conjunct at a NESTED node, never folded at all** -- the five
#:   ``refine-proposals-response`` pairs, whose ``unsatisfied_product_changes`` states its
#:   own ``propertyNames`` inside its own ``allOf``.
#:
#: :func:`test_no_pair_the_model_narrows_is_a_real_narrowing` grades these sentences
#: against the documents rather than trusting them, so a bundle version that makes one of
#: them a genuine narrowing reddens here instead of being absorbed by a comment.
NARROWER_THAN_ITS_DOCUMENT: dict[str, str] = {
    'core/async-response-data.json#': (
        "added /type -- NOT a narrowing: the root is an anyOf of 42 arms and NO arm "
        "admits a non-object.  39 state the word in their own text; arms 6 "
        "(RequestProposalsAsyncSubmitted) and 8 (RefineProposalsAsyncSubmitted) state it "
        "inside their single allOf conjunct; arm 28 (PreviewCreativeResponse) entails it "
        "through its own oneOf.  _base.entailed_types' first clause reads a branch's OWN "
        "type word, so the union root answers frozenset() and the base class's type: "
        "object reads as added. "
    ),
    'core/mcp-webhook-payload.json#': (
        "added /properties/result/type -- NOT a narrowing: the same 42-arm union, inlined "
        "under result.  One cause with the pair above. "
    ),
    'media-buy/create-media-buy-request.json#/anyOf/0/properties/budget_allocation': (
        "added /type and /additionalProperties -- NOT a narrowing: the node's allOf "
        "conjunct is the hoisted Budget Allocation, a oneOf whose BOTH branches state "
        "type: object and additionalProperties: false, so the document states both facts "
        "the model renders.  harness._composed folds the conjunct and DROPS its oneOf: "
        "the folded node is {description, properties, required}, where _entails_type "
        "answers False -- and answers True on the node as the document states it. "
    ),
    'media-buy/refine-proposals-response.json#/properties/results/items': (
        "added /properties/unsatisfied_product_changes/propertyNames -- NOT a narrowing: "
        "that property's own allOf conjunct (the Product Change Map) states "
        "propertyNames: {minLength: 1, x-entity: product} itself, and the model renders "
        "{minLength: 1} of it.  A conjunct at a NESTED node is not folded, which is the "
        "same cause as the pair above one level in. "
    ),
    'media-buy/refine-proposals-response.json#/properties/results/items/oneOf/0': (
        "added /properties/unsatisfied_product_changes/propertyNames -- NOT a narrowing: "
        "oneOf arm 0 of the pair above, which carries the same property and the same "
        "unfolded conjunct. "
    ),
    'media-buy/refine-proposals-response.json#/properties/results/items/oneOf/1': (
        "added /properties/unsatisfied_product_changes/propertyNames -- NOT a narrowing: "
        "oneOf arm 1 of the pair above, which carries the same property and the same "
        "unfolded conjunct. "
    ),
    'media-buy/refine-proposals-response.json#/properties/results/items/oneOf/2': (
        "added /properties/unsatisfied_product_changes/propertyNames -- NOT a narrowing: "
        "oneOf arm 2 of the pair above, which carries the same property and the same "
        "unfolded conjunct. "
    ),
    'media-buy/refine-proposals-response.json#/properties/results/items/oneOf/3': (
        "added /properties/unsatisfied_product_changes/propertyNames -- NOT a narrowing: "
        "oneOf arm 3 of the pair above, which carries the same property and the same "
        "unfolded conjunct. "
    ),
}


#: **The pairs whose DOCUMENT CANNOT BE READ AT**, with the raise.  ``schema_at`` raises
#: ``KeyError: '0'`` on a synthetic ``allOf`` pointer -- ``adcp-client-python-3be.15``
#: (ex ``10l.108``), whose two symptoms are one cause -- so these four pairs are neither
#: compared nor a pass.
#:
#: **Pinned HERE although the fix is another row's**, for one reason: a pair that cannot be
#: read leaves the comparable population silently, and an unpinned raise is how a fifth one
#: would.  It is this file's only ratchet that is expected to reach zero by someone else's
#: work.
UNREADABLE_PAIRS: dict[str, str] = {
    'media-buy/buy-products-request.json#/anyOf/1/properties/account/allOf/0/anyOf/0': "KeyError: '0'",
    'media-buy/buy-products-request.json#/anyOf/1/properties/account/allOf/0/anyOf/1': "KeyError: '0'",
    'media-buy/request-proposals-request.json#/anyOf/1/properties/account/allOf/0/anyOf/0': "KeyError: '0'",
    'media-buy/request-proposals-request.json#/anyOf/1/properties/account/allOf/0/anyOf/1': "KeyError: '0'",
}


@pytest.mark.xdist_group(CENSUS_GROUP)
def test_the_comparison_census_is_the_set_this_tree_produces() -> None:
    """:data:`COMPARISON_FACTS`, against ``compare_schema`` over every pair of a fresh run.

    The equality is over the SET and not over any count of it: a fact arriving, a fact
    leaving and a fact moving between the three directions each redden with the pair, the
    pointer and the direction named.  The failure message carries the two groupings a
    reader needs to act -- by shape, which says what the cause is, and by document, which
    says where the row lands.
    """
    census = compared.census()
    claimed(
        "pairs the comparison ranges over",
        {f"{one.ref.document}{one.ref.pointer}" for one in compared.pairs()},
    )
    ratchet(
        "pairs of the fresh tree the comparison reaches",
        census.paired,
        at_least=PAIRED_FLOOR,
        because="an emitting row only ADDS pairs; a drop means a class stopped carrying "
        "__adcp_schema__ or stopped being emitted, which is never this suite's intent",
    )
    if census.red != COMPARISON_FACTS:
        arrived = {name: census.red[name] for name in sorted(set(census.red) - set(COMPARISON_FACTS))}
        left = sorted(set(COMPARISON_FACTS) - set(census.red))
        moved = {
            name: {"live": census.red[name], "pinned": COMPARISON_FACTS[name]}
            for name in sorted(set(census.red) & set(COMPARISON_FACTS))
            if census.red[name] != COMPARISON_FACTS[name]
        }
        raise AssertionError(
            {
                "red and not pinned": arrived,
                "pinned and no longer red": left,
                "the facts moved at": moved,
                "live by shape": compared.by_shape(census.red),
                "live by document": compared.by_document(census.red),
            }
        )


@pytest.mark.xdist_group(CENSUS_GROUP)
def test_every_comparable_pair_is_a_pass_or_is_one_of_the_two_fact_carrying_verdicts() -> None:
    """The OUTCOME partition, derived from the facts and from the harness's own verdict.

    Two readings of one pass that must agree, and neither is a count beside the other: the
    set of pairs :data:`COMPARISON_FACTS` names is the set ``ComparisonResult.outcome``
    calls ``model_drops_a_fact`` or ``model_adds_a_fact``, and the ``pass`` figure is the
    complement over the comparable pairs.

    **AND THE THREE VERDICTS THAT CARRY NO FACT ARE PINNED EMPTY HERE**, which is what a
    census read off the facts alone cannot do: §8's sixth outcome
    (``declaration_outlived_its_widening`` -- a declaration that outlived its widening,
    which "hides the next real gap at the same pointer"), a ``harness_error`` from a model
    whose own schema cannot be built, and ``no_evidence`` from a pair whose document states
    nothing.  All three have an empty ``added``/``missing``/``differs``, so a check that
    read the facts would call them a pass.  ``tests/test_emit.py``'s census test holds the
    same zero behind the pole; this one runs.
    """
    census = compared.census()
    comparable = claimed(
        "comparable pairs",
        {f"{one.ref.document}{one.ref.pointer}" for one in compared.pairs()} - set(census.unreadable),
    )
    drops = {name for name, outcome in census.verdicts.items() if outcome == "model_drops_a_fact"}
    adds = {name for name, outcome in census.verdicts.items() if outcome == "model_adds_a_fact"}
    other = {
        name: outcome
        for name, outcome in census.verdicts.items()
        if outcome not in ("model_drops_a_fact", "model_adds_a_fact")
    }
    assert other == {}, other
    assert drops | adds == set(census.red), sorted((drops | adds) ^ set(census.red))
    partitions(comparable, passes=comparable - drops - adds, drops=drops, adds=adds)


@pytest.mark.xdist_group(CENSUS_GROUP)
def test_no_pair_the_model_narrows_is_a_real_narrowing() -> None:
    """:data:`NARROWER_THAN_ITS_DOCUMENT`, with the classification GRADED, not quoted.

    A sentence in a comment is not a finding, so each of the three causes is read back off
    the document here: the union arms admit only objects, the dropped conjunct's branches
    state both facts the model renders, and the nested conjunct states the very
    ``propertyNames`` the model carries.  A bundle version that makes any of them a genuine
    narrowing -- an arm that admits a string, a branch that admits an extra key -- reddens
    this test, which is the one way the classification cannot quietly become false.
    """
    census = compared.census()
    narrower = claimed(
        "pairs whose model states a fact its document does not",
        {name for name, facts in census.red.items() if all(fact.startswith("added ") for fact in facts)},
    )
    assert narrower == set(NARROWER_THAN_ITS_DOCUMENT), sorted(
        narrower ^ set(NARROWER_THAN_ITS_DOCUMENT)
    )
    assert len(narrower) == census.outcomes["model_adds_a_fact"]

    # CAUSE 1 -- the 42-arm union whose every arm admits only objects.  Read arm by arm:
    # its own ``type`` word, or its conjuncts', or its own combinator's entailment.  The
    # arms are claimed BY INDEX, because a schema node is not hashable and a set of them
    # cannot be named -- the index is what says the list was not empty.
    union = schema_at(SchemaRef("core/async-response-data.json", "#"))["anyOf"]
    for index in sorted(claimed("arms of the async-response-data union", range(len(union)))):
        arm = union[index]
        own = arm.get("type") == "object"
        conjoined = any(
            isinstance(one, dict) and one.get("type") == "object" for one in arm.get("allOf") or []
        )
        assert own or conjoined or "object" in entailed_types(arm), (
            index,
            "this arm does not force object: the union root's model-only type: object "
            "would be a REAL narrowing and NARROWER_THAN_ITS_DOCUMENT is wrong",
            sorted(arm),
        )

    # CAUSE 2 -- the conjunct ``_composed`` drops.  Both branches of the hoisted union
    # state the two facts the model renders, and the fold loses them.
    node = schema_at(
        SchemaRef("media-buy/create-media-buy-request.json", "#/anyOf/0/properties/budget_allocation")
    )
    hoisted = node["allOf"][0]["allOf"][0]["oneOf"]
    for index in sorted(claimed("branches of the hoisted Budget Allocation", range(len(hoisted)))):
        branch = hoisted[index]
        assert branch.get("type") == "object", (index, "no type: object")
        assert branch.get("additionalProperties") is False, (index, "extras not forbidden")
    folded = harness._composed(
        node, schema_at(SchemaRef("media-buy/create-media-buy-request.json", "#"))
    )
    assert "oneOf" not in folded and "allOf" not in folded, (
        "the fold no longer drops the conjunct's oneOf: re-read the classification, the "
        "two added facts may now be comparable"
    )

    # CAUSE 3 -- the nested conjunct, never folded: the document states the very
    # ``propertyNames`` the model renders.
    mapped = claimed(
        "pairs red on the unsatisfied_product_changes propertyNames",
        {name for name in NARROWER_THAN_ITS_DOCUMENT if "refine-proposals-response" in name},
    )
    for name in sorted(mapped):
        document, _, pointer = name.partition("#")
        node = schema_at(SchemaRef(document, f"#{pointer}"))
        # The property is on the node's own ``properties`` at the ITEMS pair and on a
        # CONJUNCT's at each ``oneOf`` arm -- draft-07 holds a conjunct against the same
        # instance, so both are the document stating this property of this node.
        views = [node, *(one for one in node.get("allOf") or [] if isinstance(one, dict))]
        stated = [
            view["properties"]["unsatisfied_product_changes"]
            for view in views
            if "unsatisfied_product_changes" in (view.get("properties") or {})
        ]
        assert stated, (name, "the document states no such property: re-read the entry")
        for one in stated:
            states = one["allOf"][0]["propertyNames"]
            assert states.get("minLength") == 1, (name, states)


@pytest.mark.xdist_group(CENSUS_GROUP)
def test_every_pair_whose_document_cannot_be_read_at_is_named() -> None:
    """:data:`UNREADABLE_PAIRS`, so a fifth cannot leave the population quietly.

    An equality and not a ceiling, in both directions: a pair arriving reddens with its
    raise, and a pair leaving reddens too, which is how ``adcp-client-python-3be.15``
    landing is read off this file rather than reported by nobody.
    """
    census = compared.census()
    claimed("pairs the comparison ranges over", {f"{one.ref.document}{one.ref.pointer}" for one in compared.pairs()})
    assert census.unreadable == UNREADABLE_PAIRS, {
        "unreadable and not pinned": {
            name: census.unreadable[name] for name in sorted(set(census.unreadable) - set(UNREADABLE_PAIRS))
        },
        "pinned and now readable": sorted(set(UNREADABLE_PAIRS) - set(census.unreadable)),
    }
