"""§3a's JUDGEMENT per repeated value list, for the value lists the bundle NAMES NOWHERE.

``docs/plan/architecture.md`` §3a states the three local answers and says which of them is
a judgement rather than a derivation:

    "So the local state is one of three:

    * **one named type** -- the positions are one subject and the bundle names it;
    * **separate types, one value list** -- the positions are genuinely different subjects;
    * **separate types pending a name** -- the positions are plausibly one subject and
      nothing in the bundle names it.  The filing asks for the name, and the local answer
      changes when it arrives."

A TITLE decides the question without a judgement, and ``codegen/catalogue.py`` answers it
there: one title names the vocabulary, and two titles of which exactly one is a document's
own root are §3a's correction of 2026-11-02.  **What is left is every value list the
bundle states at more than one position and titles at none of them**, and for those §3a's
own default is that they are NOT collapsed -- "nothing names the concept, and without a
title there is nothing to tell a coincidental member-set overlap from an identity".  This
module is where that default is overridden, per value list, by a judgement made against
the bundle's own descriptions and property names.

**IT IS AN INPUT AND NOT AN ALLOWLIST, and the difference is which direction it moves in.**
An allowlist admits a failure a check would otherwise report.  A row here decides what the
compiler EMITS: it has no power over any gate, the gate
(``tests/test_catalogue.py``'s ``test_no_two_classes_carry_one_named_vocabulary``) ranges
over the entries the rows produce, and a wrong row makes that gate red rather than green.
``tests/test_vocabularies.py`` holds the two readings that keep it honest: every row names
a value list this bundle states at more than one position, and no row names one the bundle
titles -- so a row cannot go stale and cannot reach a question a title already answered.

**WHERE THE NAME COMES FROM, which is §4's standing rule and §3a's table.**

    "The line is per TOKEN: a name is the bundle's when every token in it is stated at that
    vocabulary's own positions."

:data:`AGREED` needs no name here at all, and that is the whole reason it is a separate
collection: **every position of those 62 value lists already derived one and the same name
under §4, independently, before this layer existed.**  There is nothing to choose, so
nothing is written down -- the entry takes the name §4 derives at its home position, which
is the name every other position derived too.  61 of the 62 also share one property name
across every position, which is §3a's "the property name the positions share -- take it";
the one that does not is ``{master, sub_brand, endorsed, independent}``, stated at
``brand.json``'s ``keller_type`` and at a position that carries the enum without the
property.

**A 63rd row was declared and ``tests/test_vocabularies.py`` refused it**, which is what
that file is for: ``{DE, CH, AT}`` drew two classes in the pre-catalogue tree and the
bundle states it at ONE position.  The second class is §2's intersection rule handing
``core/postal-country-system.json``'s ``^[A-Z]{2}$`` back beside the three members, which
is a restatement §4 and §5 own and this layer never sees.

:data:`JUDGED` carries a name because the positions derived DIFFERENT names and the
judgement weighed which of them -- or which stated lengthening of one of them -- is the
subject.  ``'FileFormat'`` over ``{jsonl, csv, parquet, avro, orc}`` is the shape of it:
the five positions spell the property ``format``, ``formats`` and ``accepted_formats``, so
``Format`` is the shared property name, and ``core/format.json`` already exports ``Format``
for the creative-format concept -- which makes the lengthening §4's own collision rule and
not a mint.

:data:`PENDING_A_NAME` is §3a's third state and the one that is **not terminal**: "that is
not the same verdict, and collapsing the two hides which of them upstream can fix".  Those
four are plausibly one subject and the only candidate name could be composed only from a
``description`` -- and "a ``description`` states what a thing IS; it does not state what it
is CALLED".  So the name is carried as the UPSTREAM ASK's content and is never emitted, the
positions keep separate types over one value list, and the local answer changes when the
specification answers.

:data:`DISTINCT` is the second state: different subjects whose values coincide.  The names
are carried because they are what the judgement preserved -- ``brand.json``'s ``contrast``
("Contrast level in photography") beside its ``intensity`` ("Texture intensity"), over
``{low, medium, high}``, are two scales and not one, and the sibling evidence is that
``depth_of_field`` uses ``shallow/medium/deep`` and ``color_temperature``
``warm/neutral/cool``.

**NO ROW REACHES A VALUE LIST ONE DOCUMENT STATES ALONE**, because §4's content dedup is
the whole rule in that scope -- "two nodes with identical content emit one class ...
declared under the name of the position the walk reaches first" -- and its key is node
EQUALITY, which keeps two positions apart exactly when they state different things about an
instance.  ``tests/test_vocabularies.py`` holds that, and five rows were written and
removed by it: *Surface* and *Fit*, which §4 would have to be widened to collapse
(``brand.json``'s ``color_ref.surface`` beside its ``color_constraint.applies_to``, and
``core/placement-presentation.json``'s two ``fit`` properties), and three it already keeps
apart correctly -- ``brand.json``'s ``contrast``/``intensity`` over ``{low, medium, high}``,
``governance/get-plan-audit-logs-response.json``'s plan status beside its action status, and
``protocol/get-adcp-capabilities-response.json``'s two ``requirement`` blocks.  Widening
§4's key from node equality to the value list is a change to THAT rule and is not taken
here.

**EVERY ROW IS ALSO AN UPSTREAM QUESTION, and §3a says so of all four collections**:
"either the bundle defines one thing twice, or it defines two things that coincide on
their values and says nothing about why.  Both are questions for the specification, and
both are filed."  The filings are consolidated by family and are not this module's.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # The arrow runs ``catalogue -> vocabularies`` at RUN time: the collection consults
    # these rows and nothing here reads the collection.  The alias is wanted for the
    # annotations alone, so the import is the type checker's and the cycle is not one.
    from codegen.catalogue import Vocabulary

#: The value lists every stating position already names ALIKE under §4 (62).  One subject,
#: and the name is the one the home position derives -- see the module docstring.
AGREED: frozenset[Vocabulary] = frozenset(
    {
    ('string', ('buyer_uploaded', 'publisher_host_recorded', 'seller_pre_rendered_from_brief', 'seller_human_designed', 'agent_synthesized', 'publisher_owned_reference')),   # AssetSource
    ('string', ('public', 'account')),   # CacheScope
    ('string', ('Polygon', 'MultiPolygon')),   # GeometryType
    ('string', ('dark-bg', 'light-bg', 'transparent-bg')),   # Background
    ('string', ('decommitment', 'refund', 'credit', 'makegood')),   # AdjustmentType
    ('string', ('gross_commitment', 'verified_net_cost')),   # AccountingMode
    ('string', ('master', 'sub_brand', 'endorsed', 'independent')),   # KellerType
    ('string', ('preferred', 'accepted', 'discouraged')),   # SellerPreference
    ('string', ('transient', 'correctable', 'terminal')),   # Recovery
    ('string', ('APPROVAL_REQUIRED', 'ASSET_CONFIRMATION', 'FORMAT_CLARIFICATION')),   # Reason
    ('string', ('APPROVAL_REQUIRED', 'BUDGET_EXCEEDS_LIMIT')),   # Reason
    ('string', ('APPROVAL_REQUIRED', 'CHANGE_CONFIRMATION')),   # Reason
    ('string', ('APPROVAL_REQUIRED', 'CREATIVE_DIRECTION_NEEDED', 'ASSET_SELECTION_NEEDED')),   # Reason
    ('string', ('APPROVAL_REQUIRED', 'FEED_VALIDATION', 'ITEM_REVIEW', 'FEED_ACCESS')),   # Reason
    ('string', ('CLARIFICATION_NEEDED', 'BUDGET_REQUIRED')),   # Reason
    ('string', ('access', 'rectification', 'erasure', 'portability', 'objection')),   # RightsItem
    ('string', ('account', 'media_buy', 'creative', 'landing_page', 'targeting', 'delivery', 'format')),   # AppliesToItem
    ('string', ('active', 'suppressed')),   # Availability
    ('string', ('app_behavior', 'app_usage', 'web_usage', 'geo_location', 'email', 'tv_ott_or_stb_device', 'panel', 'online_ecommerce', 'credit_data', 'loyalty_card', 'transaction', 'online_survey', 'offline_survey', 'public_record_census', 'public_record_voter_file', 'public_record_other', 'offline_transaction')),   # DataSourcesItem
    ('string', ('apple', 'google', 'amazon', 'roku', 'fire_tv', 'samsung', 'lg', 'vizio', 'other')),   # Store
    ('string', ('buyer_to_seller', 'seller_to_buyer')),   # DirectionsItem
    ('string', ('canonical', 'legacy')),   # ProductPayloadView
    ('string', ('completed', 'submitted')),   # Status
    ('string', ('composition', 'index', 'reach_estimate')),   # Relationship
    ('string', ('control_media_buy', 'refine_proposals', 'sync_creatives')),   # Task
    ('string', ('cost_per', 'per_ad_spend', 'maximize_value')),   # ConversionTrackingSupportedTargetsItem
    ('string', ('created', 'updated', 'unchanged', 'deleted', 'failed')),   # Action
    ('string', ('created_at', 'updated_at', 'status', 'task_type', 'protocol')),   # SortField
    ('string', ('cumulative', 'period', 'rolling')),   # Kind
    ('string', ('date_range', 'lifetime_only')),   # DateRangeSupport
    ('string', ('decommitment_agreement', 'refund_settlement', 'credit_note', 'makegood_agreement')),   # EvidenceType
    ('string', ('exact_only', 'descendants_supported', 'unknown')),   # ParentMatchBehavior
    ('string', ('explicit_consent', 'manifestly_made_public', 'substantial_public_interest', 'vital_interests')),   # Art9Basis
    ('string', ('first_party_crm', 'panel', 'declared_survey', 'transactional', 'behavioral')),   # SeedSourceType
    ('string', ('fraction', 'ratio', 'count')),   # Unit
    ('string', ('individual', 'household', 'business', 'geography')),   # PreOnboardingPrecisionLevel
    ('string', ('intent', 'execution')),   # CheckType
    ('string', ('lookalike', 'supervised', 'embedding', 'rules')),   # Method
    ('string', ('media-buy', 'signals', 'creative')),   # Domain
    ('string', ('minimal', 'limited', 'high_risk')),   # AiActRiskClass
    ('string', ('mp4', 'webm', 'mov')),   # ContainersItem
    ('string', ('name', 'address', 'email', 'postal', 'lat_long', 'mobile_id', 'cookie_id', 'ip', 'customer_id', 'phone')),   # MatchKeysItem
    ('string', ('observed', 'declared', 'derived', 'inferred', 'modeled')),   # Methodology
    ('string', ('optional', 'required', 'fixed')),   # SelectionMode
    ('string', ('pending_creatives', 'pending_start', 'pending', 'active', 'paused', 'completed', 'rejected', 'canceled', 'failed', 'reporting_delayed')),   # Status
    ('string', ('platform_native', 'agent_approximation')),   # RenderingOrigin
    ('string', ('preserve', 'omit_parameter', 'dialect_sentinel', 'reject')),   # UnavailableBehavior
    ('string', ('products', 'pricing', 'forecast', 'proposals', 'wholesale_feed')),   # Scope
    ('string', ('publisher_ref', 'seller_inline')),   # Kind
    ('string', ('recommendation', 'eligibility', 'package_construction')),   # DecisionUse
    ('string', ('reported', 'verified', 'disputed')),   # AdjustmentState
    ('string', ('rfc9421', 'Bearer', 'HMAC-SHA256')),   # Mode
    ('string', ('scheduled', 'final', 'delayed', 'adjusted', 'window_update')),   # NotificationType
    ('string', ('seconds', 'minutes', 'hours', 'days')),   # Unit
    ('string', ('seller', 'system')),   # Initiator
    ('string', ('seller_statement_copy', 'buyer_measurement')),   # Source
    ('string', ('serve_default', 'do_not_serve')),   # UnmatchedLocaleAction
    ('string', ('soft', 'hard')),   # PurgeKind
    ('string', ('submitted', 'completed', 'input-required', 'rejected')),   # Arm
    ('string', ('suppress', 'restore')),   # Action
    ('string', ('targetable', 'included')),   # Mode
    ('string', ('vertical', 'horizontal', 'square')),   # Orientation
    }
)

#: Value list -> the name the bundle states for it, for the value lists judged ONE SUBJECT
#: whose positions derived different names (30).  The name is in the tree's own convention,
#: because a title is a human string and a type is an identifier (§3a).
JUDGED: Mapping[Vocabulary, str] = {
    ('string', ('jsonl', 'csv', 'parquet', 'avro', 'orc')): 'FileFormat',
    ('string', ('measured', 'forecast', 'seller_declared')): 'EvidenceType',
    ('string', ('primary', 'secondary', 'icon', 'wordmark', 'full-lockup')): 'LogoVariant',
    ('string', ('clicks', 'views', 'completed_views', 'viewed_seconds', 'viewable_rate', 'attention_seconds', 'attention_score', 'engagements', 'follows', 'saves', 'profile_visits', 'reach')): 'OptimizationMetric',
    ('string', ('fsa', 'full')): 'CaPostalCodeSystem',
    ('string', ('legacy', 'spec')): 'GradingProfile',
    ('string', ('outward', 'full')): 'GBPostalCodeSystem',
    ('string', ('product.created', 'product.updated', 'product.priced', 'product.removed', 'signal.created', 'signal.updated', 'signal.priced', 'signal.removed', 'wholesale_feed.bulk_change')): 'WholesaleFeedEventType',
    ('string', ('required', 'preferred')): 'RequirementMode',
    ('string', ('required', 'when_available')): 'EvidencePresence',
    ('string', ('square', 'horizontal', 'vertical', 'stacked')): 'LogoOrientation',
    ('string', ('subsidiary', 'parent', 'property', 'trademark')): 'ClaimType',
    ('string', ('zip', 'zip_plus_four')): 'USPostalCodeSystem',
    ('string', ('brief', 'wholesale')): 'DiscoveryMode',
    ('string', ('brief', 'wholesale', 'refine')): 'BuyingMode',
    ('string', ('consistent', 'measurement_variance', 'disputed', 'unmatched', 'closed_unresolved')): 'DeliveryReconciliationStatus',
    ('string', ('creative_fatigue', 'creative_quality_opportunity')): 'AssignmentIndicatorType',
    ('string', ('description', 'industries', 'keller_type', 'logos', 'colors', 'fonts', 'visual_guidelines', 'tone', 'tagline', 'voice_synthesis', 'assets', 'rights')): 'BrandIdentityField',
    ('string', ('direct', 'delegated', 'ad_network')): 'DelegationType',
    ('string', ('ed25519', 'ecdsa-p256-sha256')): 'WebhookSigningAlgorithm',
    ('string', ('feed_version_not_atomic', 'pricing_version_not_atomic', 'mutation_idempotency_not_guaranteed')): 'LossesItem',
    ('string', ('floor', 'target')): 'RoasStrength',
    ('string', ('h264', 'h265', 'vp8', 'vp9', 'av1', 'prores')): 'VideoCodec',
    ('string', ('keep_all', 'keep_one', 'keep_some')): 'KeepMode',
    ('string', ('linear', 'companion')): 'DaastTarget',
    ('string', ('mcp', 'a2a')): 'ProtocolTransportType',
    ('string', ('mono', 'stereo')): 'AudioChannels',
    ('string', ('normal', 'italic', 'oblique')): 'FontFileStyle',
    ('string', ('spec', 'live')): 'VerificationMode',
    ('integer', (16, 24, 32)): 'AudioBitDepth',
}

#: Value list -> the name the filing ASKS FOR, for the value lists judged plausibly one
#: subject and nameable only from prose (4).  **Never emitted**: the positions keep
#: separate types over one value list until the specification names the concept.
PENDING_A_NAME: Mapping[Vocabulary, str] = {
    ('string', ('cost_per', 'threshold_rate')): 'Target Kind',   # ['MetricOptimizationSupportedTargetsItem', 'SupportedTargetsItem', 'VendorMetricOptimizationSupportedTargetsItem']
    ('string', ('voice', 'theme', 'best_of_n', 'transformer_config', 'custom')): 'VariantAxisDimension',   # ['Dimension', 'VariantDimensionsItem']
    ('string', ('binary', 'quantitative', 'categorical')): 'FeatureValueType',   # ['PropertyFeatureDefinitionType', 'PropertyFeaturesItemType']
    ('string', ('capabilities.changed',)): 'AgentLevelNotificationType',   # ['CapabilityChangeNotificationsSupportedEventTypesItem', 'EventTypesItem']
}

#: Value list -> the names the judgement KEPT APART, for the value lists whose positions
#: are different subjects coinciding on their values (8).  Separate types over one value
#: list, which is §3a's second state.
DISTINCT: Mapping[Vocabulary, tuple[str, ...]] = {
    ('string', ('accepted', 'rejected')): ('BuyerAssetAcceptance', 'HostReceiptStatus', 'Status',),
    ('string', ('include', 'exclude')): ('AllowedTargetingModesItem', 'CollectionListApplicationEffect', 'PropertyListApplicationEffect', 'TargetingMode',),
    ('string', ('open', 'closed')): ('DeliveryPeriodState', 'EntriesItemDeliveryPeriodState', 'GovernedActionsItemDeliveryPeriodState', 'Status',),
    ('string', ('intra_day', 'daily', 'weekly', 'monthly', 'bi_monthly', 'quarterly', 'bi_annually', 'annually')): ('LookbackWindow', 'RefreshCadence',),
    ('string', ('postal_code', 'custom')): ('PostalAreaBranch9System', 'PostalAreaSupportValueItem', 'PostalCountrySystemBranch9System',),
    ('string', ('include', 'omit', 'finalize')): ('ProductRefinementRequestsItemProposalAction', 'RefineItemProposalAction',),
    ('string', ('include', 'omit', 'more_like_this')): ('ProductRefinementRequestsItemProductAction', 'RefineItemProductAction',),
    ('string', ('linear', 'non_linear', 'companion')): ('Target', 'VastTarget',),
}


def one_subject(vocabulary: Vocabulary) -> bool:
    """Is this value list judged ONE SUBJECT, so that one type serves every position?

    :data:`AGREED` or :data:`JUDGED`.  The two are one answer and two evidences, which is
    why they are two collections and one predicate.
    """
    return vocabulary in AGREED or vocabulary in JUDGED


def separate(vocabulary: Vocabulary) -> bool:
    """Is this value list judged to carry MORE THAN ONE type over one value list?

    §3a's other two states, which agree on what is emitted and differ in what is asked
    upstream: :data:`DISTINCT` asks whether the specification means two things, and
    :data:`PENDING_A_NAME` asks for the word.
    """
    return vocabulary in PENDING_A_NAME or vocabulary in DISTINCT


def judged(vocabulary: Vocabulary) -> str | None:
    """The name this judgement states for ``vocabulary``, or ``None`` where §4's own
    derivation at the home position is the name (:data:`AGREED`)."""
    return JUDGED.get(vocabulary)
