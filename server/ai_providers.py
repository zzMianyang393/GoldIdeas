from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


DEFAULT_PROVIDER = "local"
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


@dataclass
class ProviderResult:
    provider: str
    model: str
    report_json: dict[str, Any]
    report_markdown: str
    token_usage: int = 0
    cost_estimate: float = 0.0


def generate_report(opportunity: dict[str, Any], fallback_report: dict[str, Any], fallback_markdown: str) -> ProviderResult:
    provider = os.getenv("GOLDIDEAS_AI_PROVIDER", DEFAULT_PROVIDER).strip().lower()
    if provider in {"", "local", "stub"}:
        return ProviderResult(
            provider="local",
            model="local-rule-summary",
            report_json=fallback_report,
            report_markdown=fallback_markdown,
            token_usage=0,
            cost_estimate=0.0,
        )
    if provider in {"openai", "openai_compatible"}:
        return generate_openai_compatible_report(opportunity, provider)
    raise ValueError(f"Unsupported AI provider: {provider}")


def generate_openai_compatible_report(opportunity: dict[str, Any], provider: str) -> ProviderResult:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GOLDIDEAS_AI_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY or GOLDIDEAS_AI_API_KEY")

    base_url = (os.getenv("OPENAI_BASE_URL") or os.getenv("GOLDIDEAS_AI_BASE_URL") or DEFAULT_OPENAI_BASE_URL).rstrip("/")
    model = os.getenv("OPENAI_MODEL") or os.getenv("GOLDIDEAS_AI_MODEL") or DEFAULT_OPENAI_MODEL
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": "You write concise SaaS opportunity feasibility reports. Return valid JSON only.",
            },
            {
                "role": "user",
                "content": build_prompt(opportunity),
            },
        ],
    }
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        f"{base_url}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"AI provider HTTP {exc.code}: {detail[:500]}") from exc

    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    report_json = parse_report_content(content)
    markdown = render_provider_markdown(opportunity, report_json)
    usage = data.get("usage") or {}
    return ProviderResult(
        provider=provider,
        model=model,
        report_json=report_json,
        report_markdown=markdown,
        token_usage=int(usage.get("total_tokens") or 0),
        cost_estimate=0.0,
    )


def build_prompt(opportunity: dict[str, Any]) -> str:
    compact = {
        "title": opportunity.get("title"),
        "source": opportunity.get("source"),
        "url": opportunity.get("url"),
        "rating": opportunity.get("rating"),
        "total_score": opportunity.get("total_score"),
        "category": opportunity.get("category"),
        "summary": opportunity.get("content_summary"),
        "scores": opportunity.get("scores"),
        "score_reasons": opportunity.get("score_reasons"),
        "redlines": opportunity.get("redlines"),
        "key_insight": opportunity.get("key_insight"),
        "action_items": opportunity.get("action_items"),
    }
    return (
        "Create a feasibility report for this SaaS opportunity. "
        "Return JSON with keys: executive_summary, problem_evidence, audience_icp, "
        "market_signal, competition, build_feasibility, distribution, monetization, "
        "risk_assessment, validation_plan, ai_notes. "
        "Keep values concise and actionable.\n\n"
        + json.dumps(compact, ensure_ascii=False, indent=2)
    )


def parse_report_content(content: str) -> dict[str, Any]:
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.lower().startswith("json"):
            content = content[4:].strip()
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    return {
        "executive_summary": {"one_liner": content[:500]},
        "ai_notes": {
            "status": "unstructured",
            "message": "Provider returned non-JSON content; stored as summary text.",
        },
    }


def render_provider_markdown(opportunity: dict[str, Any], report: dict[str, Any]) -> str:
    lines = [f"# Feasibility Report: {opportunity.get('title', 'Untitled')}", ""]
    for key, value in report.items():
        title = key.replace("_", " ").title()
        lines.extend([f"## {title}", ""])
        if isinstance(value, dict):
            for inner_key, inner_value in value.items():
                lines.append(f"- **{inner_key.replace('_', ' ').title()}**: {format_value(inner_value)}")
        elif isinstance(value, list):
            for item in value:
                lines.append(f"- {format_value(item)}")
        else:
            lines.append(format_value(value))
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def format_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)
