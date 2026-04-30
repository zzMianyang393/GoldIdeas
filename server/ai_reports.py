from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ai_providers import generate_report
from demand_pipeline import stable_hash
from storage import get_cached_ai_report, get_opportunity, save_ai_report


REPORT_TYPE = "feasibility"
PROMPT_VERSION = "provider_v1"
TEMPLATE_VERSION = "feasibility_v1"


def input_hash_for(opportunity: dict[str, Any], report_type: str = REPORT_TYPE) -> str:
    seed = "|".join(
        [
            report_type,
            TEMPLATE_VERSION,
            opportunity.get("opportunity_id", ""),
            opportunity.get("content_hash", ""),
            str(opportunity.get("total_score", "")),
            opportunity.get("rating", ""),
        ]
    )
    return stable_hash(seed, 24)


def get_or_create_ai_report(opportunity_id: str, force: bool = False, report_type: str = REPORT_TYPE) -> dict[str, Any]:
    opportunity = get_opportunity(opportunity_id)
    if not opportunity:
        raise ValueError("Opportunity not found")

    input_hash = input_hash_for(opportunity, report_type=report_type)
    cached = get_cached_ai_report(opportunity_id, report_type, input_hash)
    if cached and not force:
        cached["cache_hit"] = True
        return cached

    fallback_report = build_stub_report(opportunity)
    fallback_markdown = render_markdown_report(opportunity, fallback_report)
    provider_result = generate_report(opportunity, fallback_report, fallback_markdown)
    generated_at = datetime.now(timezone.utc).isoformat()
    report = {
        "id": f"air_{stable_hash(opportunity_id + report_type + input_hash, 24)}",
        "opportunity_id": opportunity_id,
        "report_type": report_type,
        "status": "completed",
        "report_json": provider_result.report_json,
        "report_markdown": provider_result.report_markdown,
        "provider": provider_result.provider,
        "model": provider_result.model,
        "prompt_version": PROMPT_VERSION,
        "report_template_version": TEMPLATE_VERSION,
        "scoring_profile_version": "micro_saas_v4_1",
        "input_hash": input_hash,
        "token_usage": provider_result.token_usage,
        "cost_estimate": provider_result.cost_estimate,
        "created_at": generated_at,
        "generated_at": generated_at,
        "expires_at": "",
    }
    saved = save_ai_report(report)
    saved["cache_hit"] = False
    return saved


def build_stub_report(opportunity: dict[str, Any]) -> dict[str, Any]:
    scores = opportunity.get("scores", {})
    redlines = opportunity.get("redlines", [])
    strongest = max(scores, key=scores.get) if scores else "unknown"
    weakest = min(scores, key=scores.get) if scores else "unknown"
    should_validate = opportunity.get("rating") in {"🟢 GREEN", "🟡 YELLOW"}
    return {
        "executive_summary": {
            "rating": opportunity.get("rating"),
            "total_score": opportunity.get("total_score"),
            "recommendation": "validate" if should_validate else "skip",
            "one_liner": opportunity.get("key_insight") or "",
        },
        "problem_evidence": {
            "summary": opportunity.get("content_summary") or "",
            "source": opportunity.get("source") or "",
            "url": opportunity.get("url") or "",
            "score_reason": opportunity.get("score_reasons", {}).get("痛点强度", ""),
        },
        "build_feasibility": {
            "strongest_dimension": strongest,
            "weakest_dimension": weakest,
            "dev_reason": opportunity.get("score_reasons", {}).get("开发性价比", ""),
        },
        "risk_assessment": {
            "redline_count": len(redlines),
            "redlines": redlines,
            "survival_reason": opportunity.get("score_reasons", {}).get("生存稳定性", ""),
        },
        "validation_plan": {
            "next_step": opportunity.get("action_items") or "",
            "questions": [
                "Who has this pain often enough to pay for a solution?",
                "What workaround are they using today?",
                "What price would make the solution feel obviously worth it?",
            ],
        },
        "ai_notes": {
            "status": "stub",
            "message": "This is a cached local placeholder. Replace this module with a real AI provider when credentials and pricing rules are ready.",
        },
    }


def render_markdown_report(opportunity: dict[str, Any], report: dict[str, Any]) -> str:
    summary = report["executive_summary"]
    evidence = report["problem_evidence"]
    feasibility = report["build_feasibility"]
    risks = report["risk_assessment"]
    validation = report["validation_plan"]
    questions = "\n".join(f"- {item}" for item in validation["questions"])
    return f"""# Feasibility Report: {opportunity.get('title', 'Untitled')}

## Executive Summary

- Rating: {summary.get('rating')}
- Score: {summary.get('total_score')}/10
- Recommendation: {summary.get('recommendation')}
- One-liner: {summary.get('one_liner')}

## Problem Evidence

- Source: {evidence.get('source')}
- URL: {evidence.get('url')}
- Pain evidence: {evidence.get('score_reason')}
- Summary: {evidence.get('summary')}

## Build Feasibility

- Strongest dimension: {feasibility.get('strongest_dimension')}
- Weakest dimension: {feasibility.get('weakest_dimension')}
- Dev evidence: {feasibility.get('dev_reason')}

## Risk Assessment

- Redline count: {risks.get('redline_count')}
- Survival evidence: {risks.get('survival_reason')}

## Validation Plan

- Next step: {validation.get('next_step')}

### Questions

{questions}

## AI Notes

This report is a zero-token local placeholder and is cached by opportunity/input hash.
"""
