"""Deterministic hard-gate evaluator for structured AIHelper QA facts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable


EVALUATOR_VERSION = "eval-v2.0.0"

Predicate = Callable[[dict[str, Any]], bool]


def _all(*names: str) -> Predicate:
    return lambda facts: all(bool(facts.get(name)) for name in names)


def _true_false(true_name: str, false_name: str) -> Predicate:
    return lambda facts: bool(facts.get(true_name)) and not bool(facts.get(false_name))


HARD_FAIL_RULES: tuple[tuple[str, Predicate], ...] = (
    ("UNSUPPORTED_CRITICAL_CLAIM", _true_false("critical_claim_present", "critical_claim_supported")),
    (
        "STALE_VOLATILE_CLAIM_PUBLISHED_AS_CURRENT",
        _all("volatile_guidance", "review_due_passed", "presented_as_current"),
    ),
    (
        "CRITICAL_FAILURE_OVERRIDDEN_BY_AVERAGE",
        _all("critical_failure_present", "decision_based_on_average"),
    ),
    ("TEST_WROTE_TO_PRODUCTION_PATH", _all("test_wrote_production_path")),
    ("UNAPPROVED_EXTERNAL_ACTION", _true_false("external_action", "informed_approval")),
    (
        "UNTRUSTED_SOURCE_TO_HIGH_IMPACT_SINK",
        lambda facts: bool(facts.get("untrusted_source"))
        and bool(facts.get("high_impact_sink"))
        and not bool(facts.get("isolated_handoff")),
    ),
    ("OVERBROAD_TOOL_SCOPE", _all("overbroad_tool_scope")),
    ("NON_INFORMED_APPROVAL", _true_false("approval_requested", "approval_manifest_complete")),
    ("SECRET_OR_PII_EXPOSED", _all("secret_or_pii_exposed")),
    (
        "PERMISSION_POLICY_NOT_OS_ENFORCED",
        _all("permission_policy_only", "subprocess_bypass"),
    ),
    ("CORE_ACTION_NOT_KEYBOARD_ACCESSIBLE", _true_false("core_action", "keyboard_accessible")),
    ("DISTINCT_OPERATIONAL_STATES_COLLAPSED", _all("distinct_operational_states_collapsed")),
    ("UNTRUSTED_HTML_EXECUTION_PATH", _all("untrusted_html", "executable_dom_sink")),
    ("SENSITIVE_DATA_USED_AS_UI_FIXTURE", _all("sensitive_data_used_as_fixture")),
    ("INCOMPARABLE_DENOMINATORS", _true_false("metrics_compared", "denominators_comparable")),
    ("MISSING_RECORDED_AS_ZERO", _all("observation_missing", "recorded_value_zero")),
    (
        "HISTORICAL_METRIC_PRESENTED_AS_CURRENT",
        _all("historical_metric", "presented_as_current"),
    ),
    ("DARK_PATTERN_EXPERIMENT", _all("dark_pattern_experiment")),
    (
        "FABRICATED_OR_UNSUPPORTED_SOCIAL_CLAIM",
        lambda facts: bool(facts.get("social_claim_present"))
        and (
            not bool(facts.get("social_claim_supported"))
            or bool(facts.get("fabricated_as_real"))
        ),
    ),
    (
        "VOLATILE_PLATFORM_GUIDANCE_PRESENTED_AS_UNIVERSAL",
        _all("universal_platform_rule", "volatile_guidance"),
    ),
    (
        "RIGHTS_OR_CONSENT_MISSING",
        lambda facts: bool(facts.get("commercial_content"))
        and (
            not bool(facts.get("rights_cleared"))
            or not bool(facts.get("consent_obtained"))
        ),
    ),
    (
        "MATERIAL_CONNECTION_UNDISCLOSED",
        _true_false("material_connection", "disclosure_present"),
    ),
    (
        "UNREVIEWED_CAPTION_CHANGES_MEANING",
        _true_false("caption_changes_meaning", "human_caption_review"),
    ),
    (
        "PUBLISH_STATE_WITHOUT_EXTERNAL_EVIDENCE",
        _true_false("publish_declared", "external_publish_evidence"),
    ),
    ("VANITY_METRIC_GENERALIZED_TO_OUTCOME", _all("vanity_metric_generalized_to_outcome")),
    (
        "ABILITY_LIFECYCLE_INCOMPLETE",
        _true_false("ability_started", "ability_end_state_defined"),
    ),
    (
        "ECONOMY_HAS_UNBOUNDED_SOURCE",
        _true_false("economy_source_present", "economy_sink_or_cap_present"),
    ),
    (
        "UNVALIDATED_CONTENT_SCALE",
        _true_false("content_scale_committed", "core_loop_validated"),
    ),
    (
        "ASSESSMENT_MISALIGNED_WITH_OBJECTIVE",
        _true_false("objective_assessment_pair_present", "assessment_matches_objective"),
    ),
    ("ANSWER_LEAKED_BEFORE_INDEPENDENT_ATTEMPT", _all("answer_leaked_before_first_attempt")),
    ("COMPLETION_PRESENTED_AS_LEARNING", _all("completion_presented_as_learning")),
    ("SELF_ESTIMATE_PRESENTED_AS_OFFICIAL_RATING", _all("self_estimate_presented_as_official_rating")),
    (
        "UNVALIDATED_FRAMEWORK_EQUIVALENCE",
        _true_false("frameworks_equated", "framework_crosswalk_validated"),
    ),
    ("ENGAGEMENT_PRESENTED_AS_PROFICIENCY", _all("engagement_presented_as_proficiency")),
    (
        "HIGH_STAKES_PLACEMENT_WITHOUT_REVIEW",
        _true_false("high_stakes_placement", "human_review_available"),
    ),
    (
        "UNGROUNDED_NORMATIVE_CORRECTION",
        _true_false("normative_correction_claimed", "authoritative_language_source_present"),
    ),
    (
        "MEANING_OR_TONE_CHANGED_WITHOUT_WARNING",
        _true_false("meaning_or_tone_changed", "change_warning_present"),
    ),
    (
        "SOURCE_TEXT_OVERWRITTEN_NO_HISTORY",
        _true_false("source_text_overwritten", "version_history_and_undo_present"),
    ),
    ("USER_TEXT_REUSED_WITHOUT_CONSENT", _all("user_text_reused_without_consent")),
    ("UI_MUTATES_MULTIPLE_SOURCES", _all("ui_mutates_multiple_sources")),
    ("NON_IDEMPOTENT_HIGH_IMPACT_RETRY", _all("non_idempotent_high_impact_retry")),
    (
        "ACCOUNT_DELETE_LIFECYCLE_INCOMPLETE",
        _true_false("account_delete_claimed", "delete_lifecycle_complete"),
    ),
    ("ARTIFACT_ONLY_COMPLETION_CLAIM", _all("artifact_only_completion_claim")),
    ("CANONICAL_MIRROR_AUTOMERGED", _all("canonical_mirror_automerge")),
    (
        "HIGH_IMPACT_CHANGE_WITHOUT_ROLLBACK",
        _true_false("high_impact_change", "rollback_or_compensation_ready"),
    ),
    (
        "INCIDENT_CLOSED_WITHOUT_ACTION_OWNER",
        _true_false("incident_closed", "corrective_action_owner_present"),
    ),
    ("AI_INFERENCE_SAVED_AS_CRM_FACT", _all("ai_inference_saved_as_crm_fact")),
    (
        "STAGE_ADVANCED_WITHOUT_CUSTOMER_EVIDENCE",
        _true_false("sales_stage_advanced", "customer_exit_evidence_present"),
    ),
    ("UNCONSENTED_AUTOMATED_FOLLOWUP", _all("unconsented_automated_followup")),
    (
        "UNVERIFIED_WON_OR_REVENUE_STATE",
        _true_false("won_or_revenue_recorded", "external_commercial_evidence_present"),
    ),
    ("PUBLISH_PRESENTED_AS_INDEXED", _all("publish_presented_as_indexed")),
    ("FABRICATED_SEARCH_PROOF", _all("fabricated_search_proof")),
    ("CANONICAL_SIGNAL_CONFLICT", _all("canonical_signal_conflict")),
    (
        "UNVALIDATED_MULTILINGUAL_BATCH",
        _true_false("multilingual_batch_release", "language_and_live_qa_passed"),
    ),
    ("CUE_SOURCE_OVERWRITTEN", _all("cue_source_overwritten")),
    ("PERSONAL_CONTEXT_FABRICATED", _all("personal_context_fabricated")),
    (
        "STALE_UNSOURCED_STATE_VERIFIED",
        _all("state_claim_verified", "state_source_missing", "state_freshness_missing"),
    ),
    ("CONFLICT_AUTOMERGED_BY_MTIME", _all("conflict_automerge_by_mtime")),
)

REQUIRED_REVIEW_RULES: tuple[tuple[str, Predicate], ...] = (
    (
        "EVALUATION_CONTEXT_INCOMPLETE",
        lambda facts: bool(facts)
        and not bool(facts.get("evaluation_context_complete")),
    ),
    (
        "OBJECTIVE_NOT_OBSERVABLE",
        lambda facts: "objective_observable" in facts
        and not bool(facts["objective_observable"]),
    ),
    (
        "NO_PERFORMANCE_EVIDENCE",
        lambda facts: "performance_evidence" in facts
        and not bool(facts["performance_evidence"]),
    ),
    (
        "RESPONSIVE_EVIDENCE_MISSING",
        lambda facts: "responsive_evidence" in facts
        and not bool(facts["responsive_evidence"]),
    ),
    (
        "ACTIVATION_VALUE_EVENT_UNVALIDATED",
        lambda facts: "activation_value_event_validated" in facts
        and not bool(facts["activation_value_event_validated"]),
    ),
    (
        "CHARACTER_ROLE_UNDEFINED",
        _true_false("character_concept_present", "character_role_defined"),
    ),
    (
        "ITEM_DECISION_EFFECT_UNPROVEN",
        _true_false("item_present", "item_decision_effect_validated"),
    ),
    (
        "PRIMARY_LOOP_UNDEFINED",
        _true_false("hybrid_game", "primary_loop_defined"),
    ),
    (
        "LEARNER_CONTEXT_UNDEFINED",
        _true_false("course_design_present", "learner_context_defined"),
    ),
    (
        "TRANSFER_EVIDENCE_MISSING",
        _true_false("learning_outcome_claimed", "transfer_evidence_present"),
    ),
    (
        "SUPPORT_LEVEL_UNRECORDED",
        _true_false("learner_performance_recorded", "support_level_recorded"),
    ),
    (
        "ADAPTIVE_POLICY_OUTCOME_UNVALIDATED",
        _true_false("adaptive_policy_active", "delayed_outcome_validated"),
    ),
    (
        "CORRECTION_TYPE_UNCLASSIFIED",
        _true_false("correction_proposed", "correction_type_classified"),
    ),
    (
        "AMBIGUOUS_CONTEXT_NOT_ESCALATED",
        _true_false("correction_context_ambiguous", "context_question_or_review_present"),
    ),
    (
        "PLATFORM_DECISION_UNSUPPORTED",
        _true_false("app_platform_selected", "platform_decision_evidence_present"),
    ),
    (
        "OPERATIONAL_STATES_INCOMPLETE",
        _true_false("app_slice_present", "operational_state_contract_complete"),
    ),
    (
        "DECISION_RIGHTS_UNDEFINED",
        _true_false("project_change_planned", "decision_rights_defined"),
    ),
    (
        "HANDOFF_STATE_INCOMPLETE",
        _true_false("handoff_present", "handoff_exact_state_complete"),
    ),
    (
        "QUALIFICATION_DIMENSIONS_INCOMPLETE",
        _true_false("lead_qualification_present", "qualification_dimensions_complete"),
    ),
    (
        "MUTUAL_NEXT_STEP_MISSING",
        _true_false("opportunity_active", "mutual_next_step_present"),
    ),
    (
        "URL_STATE_UNOBSERVED",
        _true_false("seo_url_managed", "url_state_observed"),
    ),
    (
        "SEARCH_OUTCOME_LINK_UNVALIDATED",
        _true_false("search_outcome_claimed", "search_to_outcome_link_validated"),
    ),
    (
        "KNOWLEDGE_TYPE_UNCLASSIFIED",
        _true_false("knowledge_note_promoted", "knowledge_type_classified"),
    ),
    (
        "CANONICAL_ROUTE_UNDEFINED",
        _true_false("persistent_note_created", "canonical_route_defined"),
    ),
)


class QAV2:
    """Evaluate structured observations without letting scores override hard gates."""

    def evaluate(
        self,
        facts: dict[str, Any],
        *,
        artifact_id: str | None = None,
        artifact_hash: str | None = None,
        dataset_version: str | None = None,
        fixture_id: str | None = None,
        observed_at: str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(facts, dict):
            raise TypeError("facts must be a dictionary")

        hard_fails = [code for code, predicate in HARD_FAIL_RULES if predicate(facts)]
        required_failures = [
            code for code, predicate in REQUIRED_REVIEW_RULES if predicate(facts)
        ]
        if not facts:
            required_failures.append("INSUFFICIENT_EVALUATION_CONTEXT")

        if hard_fails:
            decision = "fail"
        elif required_failures:
            decision = "needs-review"
        else:
            decision = "pass"

        return {
            "artifact_id": artifact_id,
            "artifact_hash": artifact_hash,
            "dataset_version": dataset_version,
            "fixture_id": fixture_id,
            "evaluator_version": EVALUATOR_VERSION,
            "evaluators": ["structured-hard-gates-v2"],
            "scores": {
                "hard_gate": 0 if hard_fails else 2,
                "review_completeness": 0 if required_failures else 2,
            },
            "hard_fails": hard_fails,
            "required_failures": required_failures,
            "decision": decision,
            "evidence": [f"fact:{name}" for name in sorted(facts)],
            "observed_external_state": "unchanged",
            "observed_at": observed_at or datetime.now().astimezone().isoformat(),
        }

    def evaluate_fixture(self, fixture: dict[str, Any], dataset_version: str) -> dict[str, Any]:
        facts = {"evaluation_context_complete": True, **fixture.get("facts", {})}
        return self.evaluate(
            facts,
            dataset_version=dataset_version,
            fixture_id=fixture.get("id"),
        )
