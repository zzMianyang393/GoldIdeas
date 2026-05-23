from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ai_providers import generate_report
from demand_pipeline import stable_hash
from storage import get_cached_ai_report, get_opportunity, save_ai_report


REPORT_TYPE = "feasibility"
PROMPT_VERSION = "provider_v2"
TEMPLATE_VERSION = "validation_v2"


def input_hash_for(opportunity: dict[str, Any], report_type: str = REPORT_TYPE) -> str:
    seed = "|".join(
        [
            report_type,
            TEMPLATE_VERSION,
            opportunity.get("opportunity_id", ""),
            opportunity.get("content_hash", ""),
            str(opportunity.get("evidence_count", "")),
            ",".join(opportunity.get("cluster_keywords", [])[:8]),
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


def decide_verdict(opportunity: dict[str, Any]) -> str:
    rating = opportunity.get("rating") or ""
    score = float(opportunity.get("total_score") or 0)
    evidence_count = int(opportunity.get("evidence_count") or 1)
    redlines = opportunity.get("redlines", [])
    if redlines or "RED" in rating:
        return "KILL"
    if score >= 6.5 and evidence_count >= 2:
        return "GO"
    if "GREEN" in rating or score >= 5.0:
        return "PIVOT"
    return "KILL"


def decision_reason(verdict: str, opportunity: dict[str, Any]) -> str:
    evidence_count = int(opportunity.get("evidence_count") or 1)
    score = opportunity.get("total_score")
    if verdict == "GO":
        return f"Score {score}/10 with {evidence_count} linked evidence signals; validate buyer urgency and pricing before building."
    if verdict == "PIVOT":
        return "Signal exists, but the evidence is not strong enough for an immediate build. Narrow the ICP or problem statement first."
    return "Redlines or weak score make this a poor build candidate unless new evidence changes the risk profile."


def collect_evidence(opportunity: dict[str, Any]) -> list[dict[str, Any]]:
    signals = opportunity.get("representative_signals") or []
    if not signals:
        signals = [
            {
                "title": opportunity.get("title"),
                "source": opportunity.get("source"),
                "url": opportunity.get("url"),
                "content_summary": opportunity.get("content_summary"),
            }
        ]
    evidence: list[dict[str, Any]] = []
    for signal in signals[:8]:
        evidence.append(
            {
                "title": signal.get("title") or "Untitled signal",
                "source": signal.get("source") or signal.get("source_group") or "unknown",
                "url": signal.get("url") or signal.get("comments_url") or "",
                "summary": signal.get("content_summary") or "",
                "comments": signal.get("comments") or 0,
            }
        )
    return evidence


def infer_icp(opportunity: dict[str, Any]) -> dict[str, Any]:
    text = f"{opportunity.get('title', '')} {opportunity.get('content_summary', '')} {' '.join(opportunity.get('cluster_keywords', []))}".lower()
    if any(keyword in text for keyword in ["shopify", "ecommerce", "returns", "refund", "inventory", "orders"]):
        return {
            "primary_segment": "Small and mid-sized ecommerce operators",
            "buyer": "Founder, ops lead, or support manager at a DTC/Shopify store",
            "trigger": "Manual operations are consuming support time or hurting retention.",
        }
    if any(keyword in text for keyword in ["api", "developer", "cli", "sdk", "github", "documentation"]):
        return {
            "primary_segment": "Developer teams and technical founders",
            "buyer": "Engineering lead, platform team, or indie developer selling to developers",
            "trigger": "A recurring workflow breakage or tooling gap is wasting engineering time.",
        }
    return {
        "primary_segment": "Indie founders and small software teams with the repeated pain described in the evidence",
        "buyer": "Founder or operator who owns the workflow and budget",
        "trigger": "The workaround is frequent, manual, and visible enough to justify a paid tool.",
    }


def market_confidence(opportunity: dict[str, Any]) -> str:
    evidence_count = int(opportunity.get("evidence_count") or 1)
    source_count = int(opportunity.get("source_count") or 1)
    score = float(opportunity.get("total_score") or 0)
    if evidence_count >= 3 and source_count >= 2 and score >= 6:
        return "medium-high"
    if evidence_count >= 2 and score >= 5:
        return "medium"
    return "low-medium"


def infer_distribution(opportunity: dict[str, Any]) -> list[str]:
    text = f"{opportunity.get('source_group', '')} {' '.join(opportunity.get('cluster_keywords', []))}".lower()
    channels = [
        "Reply manually to high-intent source discussions with a useful mini-report, not a product pitch.",
        "Publish an indexed opportunity page targeting the exact problem phrase from the cluster.",
        "Run 10 direct interviews using the evidence list as the outreach reason.",
    ]
    if "shopify" in text or "ecommerce" in text:
        channels.insert(1, "Seed the first users through Shopify Community, app-store competitor reviews, and agency operators.")
    elif "api" in text or "developer" in text or "github" in text:
        channels.insert(1, "Seed the first users through Hacker News, GitHub issues, and developer communities.")
    return channels[:4]


def summarize_competition(opportunity: dict[str, Any]) -> dict[str, Any]:
    keywords = opportunity.get("cluster_keywords", [])
    named_risks = [redline.get("name", "redline") for redline in opportunity.get("redlines", []) if isinstance(redline, dict)]
    return {
        "likely_alternatives": [
            "Manual spreadsheet or internal workflow workaround",
            "Generic automation platforms such as Zapier or Make",
            "Existing category leaders mentioned in source discussions",
        ],
        "gap_hypothesis": f"Win by narrowing around {', '.join(keywords[:3]) or 'the repeated workflow'} instead of competing as a broad platform.",
        "known_risks": named_risks or ["No confirmed competitor research yet; validate with search and review mining before building."],
    }


def pricing_hypothesis(opportunity: dict[str, Any]) -> str:
    text = f"{opportunity.get('title', '')} {opportunity.get('content_summary', '')} {' '.join(opportunity.get('cluster_keywords', []))}".lower()
    if any(keyword in text for keyword in ["shopify", "ecommerce", "returns", "refund", "inventory"]):
        return "$29-$99/month per store, with higher tiers tied to order volume or saved support time."
    if any(keyword in text for keyword in ["developer", "api", "cli", "github", "sdk"]):
        return "$15-$49/month for indie developers, or $99+/month for small teams if it saves engineering time."
    return "$19-$49/month for a focused solo-user workflow; validate willingness to pay before building a team plan."


def build_stub_report(opportunity: dict[str, Any]) -> dict[str, Any]:
    scores = opportunity.get("scores", {})
    redlines = opportunity.get("redlines", [])
    strongest = max(scores, key=scores.get) if scores else "unknown"
    weakest = min(scores, key=scores.get) if scores else "unknown"
    verdict = decide_verdict(opportunity)
    evidence = collect_evidence(opportunity)
    return {
        "executive_summary": {
            "verdict": verdict,
            "rating": opportunity.get("rating"),
            "total_score": opportunity.get("total_score"),
            "evidence_count": opportunity.get("evidence_count") or 1,
            "source_count": opportunity.get("source_count") or 1,
            "one_liner": opportunity.get("key_insight") or opportunity.get("content_summary") or "",
            "decision_reason": decision_reason(verdict, opportunity),
        },
        "problem_evidence": {
            "summary": opportunity.get("content_summary") or "",
            "cluster_keywords": opportunity.get("cluster_keywords", []),
            "sources": opportunity.get("sources") or [opportunity.get("source") or ""],
            "evidence": evidence,
            "score_reason": opportunity.get("score_reasons", {}).get("痛点强度")
            or opportunity.get("score_reasons", {}).get("鐥涚偣寮哄害", ""),
        },
        "audience_icp": infer_icp(opportunity),
        "market_signal": {
            "willingness_to_pay": opportunity.get("score_reasons", {}).get("变现确定性")
            or opportunity.get("score_reasons", {}).get("鍙樼幇纭畾鎬?", ""),
            "frequency_signal": f"{opportunity.get('evidence_count') or 1} linked signal(s) found in the current scan.",
            "confidence": market_confidence(opportunity),
        },
        "competition": summarize_competition(opportunity),
        "build_feasibility": {
            "strongest_dimension": strongest,
            "weakest_dimension": weakest,
            "dev_reason": opportunity.get("score_reasons", {}).get("开发性价比")
            or opportunity.get("score_reasons", {}).get("寮€鍙戞€т环姣?", ""),
            "mvp_scope": [
                "One narrow workflow only; avoid broad platform positioning.",
                "Manual concierge backend is acceptable for the first 5 users.",
                "Ship a landing page plus a thin workflow prototype before deep automation.",
            ],
        },
        "distribution": {
            "recommended_channels": infer_distribution(opportunity),
            "first_20_user_plan": [
                "Collect the top evidence links and identify users with direct pain.",
                "Send a concise note offering to solve or research the exact workflow.",
                "Convert positive replies into interviews before writing production code.",
            ],
        },
        "monetization": {
            "pricing_hypothesis": pricing_hypothesis(opportunity),
            "charge_event": "Charge when the product saves recurring operational time or unlocks measurable revenue.",
            "free_tier_warning": "Avoid a broad free tool; use a limited diagnostic or report as the free entry point.",
        },
        "risk_assessment": {
            "redline_count": len(redlines),
            "redlines": redlines,
            "survival_reason": opportunity.get("score_reasons", {}).get("生存稳定性")
            or opportunity.get("score_reasons", {}).get("鐢熷瓨绋冲畾鎬?", ""),
            "kill_criteria": [
                "No target users agree to a follow-up interview.",
                "Existing alternatives solve the core workflow at a low switching cost.",
                "The workflow requires compliance, platform access, or manual service beyond the team's capacity.",
            ],
        },
        "validation_plan": {
            "next_step": opportunity.get("action_items") or "",
            "questions": [
                "Who has this pain often enough to pay for a solution?",
                "What workaround are they using today?",
                "What price would make the solution feel obviously worth it?",
            ],
            "seven_day_plan": [
                "Day 1: Review evidence and write one narrow problem statement.",
                "Day 2-3: Contact 10 users from matching communities or adjacent discussions.",
                "Day 4: Run 5 interviews and collect exact workflow language.",
                "Day 5: Publish a fake-door landing page with pricing.",
                "Day 6-7: Decide whether to prototype based on replies, waitlist signups, and price resistance.",
            ],
        },
        "ai_notes": {
            "status": "local_validation_template",
            "message": "Zero-token local report generated from scored evidence. A real provider can enrich competitor research and copywriting later.",
        },
    }


def render_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- Not enough evidence yet."


def render_evidence(items: list[dict[str, Any]]) -> str:
    lines = []
    for item in items:
        title = item.get("title") or "Untitled signal"
        url = item.get("url") or ""
        source = item.get("source") or "unknown"
        summary = item.get("summary") or "Source evidence"
        link = f"[{title}]({url})" if url else title
        lines.append(f"- **{source}**: {link} - {summary}")
    return "\n".join(lines) if lines else "- No evidence attached."


def render_markdown_report(opportunity: dict[str, Any], report: dict[str, Any]) -> str:
    summary = report["executive_summary"]
    evidence = report["problem_evidence"]
    icp = report["audience_icp"]
    market = report["market_signal"]
    competition = report["competition"]
    feasibility = report["build_feasibility"]
    distribution = report["distribution"]
    monetization = report["monetization"]
    risks = report["risk_assessment"]
    validation = report["validation_plan"]
    return f"""# Opportunity Validation Report: {opportunity.get('title', 'Untitled')}

## Verdict: {summary.get('verdict')}

- Rating: {summary.get('rating')}
- Score: {summary.get('total_score')}/10
- Evidence: {summary.get('evidence_count')} signal(s) across {summary.get('source_count')} source(s)
- One-liner: {summary.get('one_liner')}
- Decision reason: {summary.get('decision_reason')}

## Problem Evidence

- Summary: {evidence.get('summary')}
- Keywords: {", ".join(evidence.get('cluster_keywords', []))}
- Pain evidence: {evidence.get('score_reason')}

{render_evidence(evidence.get('evidence', []))}

## Target ICP

- Segment: {icp.get('primary_segment')}
- Buyer: {icp.get('buyer')}
- Trigger: {icp.get('trigger')}

## Market Signal

- Confidence: {market.get('confidence')}
- Willingness to pay: {market.get('willingness_to_pay')}
- Frequency: {market.get('frequency_signal')}

## Competition And Gaps

- Gap hypothesis: {competition.get('gap_hypothesis')}

### Likely Alternatives

{render_list(competition.get('likely_alternatives', []))}

### Known Risks

{render_list(competition.get('known_risks', []))}

## Build Feasibility

- Strongest dimension: {feasibility.get('strongest_dimension')}
- Weakest dimension: {feasibility.get('weakest_dimension')}
- Dev evidence: {feasibility.get('dev_reason')}

### MVP Scope

{render_list(feasibility.get('mvp_scope', []))}

## Distribution

### Recommended Channels

{render_list(distribution.get('recommended_channels', []))}

### First 20 Users

{render_list(distribution.get('first_20_user_plan', []))}

## Monetization

- Pricing hypothesis: {monetization.get('pricing_hypothesis')}
- Charge event: {monetization.get('charge_event')}
- Free tier warning: {monetization.get('free_tier_warning')}

## Risk Assessment

- Redline count: {risks.get('redline_count')}
- Survival evidence: {risks.get('survival_reason')}

### Kill Criteria

{render_list(risks.get('kill_criteria', []))}

## Validation Plan

- Next step: {validation.get('next_step')}

### Interview Questions

{render_list(validation.get('questions', []))}

### Seven-Day Plan

{render_list(validation.get('seven_day_plan', []))}

## AI Notes

This report is a zero-token local validation report and is cached by opportunity/input hash.
"""
