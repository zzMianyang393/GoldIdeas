from pathlib import Path
from time import sleep
import os

from ai_jobs import enqueue_ai_report_job
from ai_reports import get_or_create_ai_report
from ai_providers import parse_report_content
from demand_pipeline import analyze_post, run_pipeline
from storage import (
    DB_PATH,
    complete_search_job,
    create_search_job,
    get_opportunity,
    get_opportunity_record,
    get_ai_job,
    get_ai_report,
    get_search_job,
    list_ai_jobs,
    list_ai_reports,
    list_opportunities,
    list_runs,
    list_search_jobs,
    list_sources,
    set_source_enabled,
    upsert_source,
)


def test_tech_redline() -> None:
    item = analyze_post(
        {
            "title": "A tool to bypass API limits with self-hosted LLM and tweet automation",
            "content": "Need a way around platform limits.",
            "url": "https://example.com/1",
            "source": "sample",
            "comments": 0,
        }
    )
    assert item["rating"] == "🔴 RED"
    assert any(redline["id"] == 3 for redline in item["redlines"])


def test_giant_alternative_is_opportunity() -> None:
    item = analyze_post(
        {
            "title": "Looking for an affordable alternative to Notion for client portals",
            "content": "Notion is too expensive and hard to manage. I would pay for a focused tool.",
            "url": "https://example.com/2",
            "source": "sample",
            "comments": 12,
        }
    )
    assert not any(redline["id"] == 1 for redline in item["redlines"])
    assert item["total_score"] >= 5.0


def test_fake_question_without_pain_is_red() -> None:
    item = analyze_post(
        {
            "title": "What do you think about another todo list app?",
            "content": "Just wondering.",
            "url": "https://example.com/3",
            "source": "sample",
            "comments": 1,
        }
    )
    assert any(redline["id"] in {4, 5} for redline in item["redlines"])


def test_fingerprint_is_stable() -> None:
    first = analyze_post(
        {
            "title": "Looking for a simple SaaS dashboard",
            "content": "I need a better dashboard and would pay for it.",
            "url": "https://example.com/stable?utm_source=x",
            "source": "sample",
            "source_group": "sample",
            "comments": 0,
        }
    )
    second = analyze_post(
        {
            "title": "Looking for a simple SaaS dashboard",
            "content": "I need a better dashboard and would pay for it.",
            "url": "https://example.com/stable?utm_source=y",
            "source": "sample",
            "source_group": "sample",
            "comments": 0,
        }
    )
    assert first["opportunity_id"] == second["opportunity_id"]
    assert first["signal_id"] == second["signal_id"]


def test_pipeline_persists_and_ai_report_is_cached() -> None:
    result = run_pipeline(
        fetch=False,
        sample_posts=[
            {
                "title": "Looking for a Shopify returns automation tool",
                "content": "Returns waste time. I would pay monthly for a focused automation tool.",
                "url": "https://example.com/shopify-returns",
                "source": "sample",
                "source_group": "sample",
                "comments": 24,
            }
        ],
        query="returns",
        opportunity_type="ecommerce_tools",
        persist=True,
    )
    opportunity_id = result["opportunities"][0]["opportunity_id"]
    assert Path(DB_PATH).exists()
    assert list_runs(1)
    assert get_opportunity(opportunity_id)["opportunity_id"] == opportunity_id

    first = get_or_create_ai_report(opportunity_id)
    second = get_or_create_ai_report(opportunity_id)
    assert first["input_hash"] == second["input_hash"]
    assert second["cache_hit"] is True


def test_sources_can_be_managed() -> None:
    source = upsert_source(
        {
            "id": "test_source",
            "name": "Test Source",
            "type": "rss",
            "url": "https://example.com/feed",
            "enabled": True,
            "source_pack": "test",
        }
    )
    assert source["enabled"] is True
    disabled = set_source_enabled("test_source", False)
    assert disabled is not None
    assert disabled["enabled"] is False
    assert any(item["id"] == "test_source" for item in list_sources())


def test_search_job_lifecycle() -> None:
    job = create_search_job({"query": "returns", "opportunity_type": "ecommerce_tools", "limit": 1})
    assert job["status"] == "pending"
    result = run_pipeline(
        fetch=False,
        sample_posts=[
            {
                "title": "Need ecommerce return analytics",
                "content": "Returns are expensive and I would pay for analytics.",
                "url": "https://example.com/return-analytics",
                "source": "sample",
                "source_group": "sample",
                "comments": 3,
            }
        ],
        query="returns",
        opportunity_type="ecommerce_tools",
        search_job_id=job["id"],
        persist=True,
    )
    completed = complete_search_job(job["id"], result)
    assert completed is not None
    assert completed["status"] == "completed"
    assert completed["run_id"] == result["metadata"]["run_id"]
    assert get_search_job(job["id"])["result_counts"]
    assert any(item["id"] == job["id"] for item in list_search_jobs())


def test_ai_job_lifecycle() -> None:
    result = run_pipeline(
        fetch=False,
        sample_posts=[
            {
                "title": "Need API changelog monitoring",
                "content": "API changes break our workflow. We would pay monthly for alerts.",
                "url": "https://example.com/api-changelog-monitoring",
                "source": "sample",
                "source_group": "sample",
                "comments": 15,
            }
        ],
        query="api",
        opportunity_type="developer_tools",
        persist=True,
    )
    opportunity_id = result["opportunities"][0]["opportunity_id"]
    job = enqueue_ai_report_job(opportunity_id)
    final_job = None
    for _ in range(20):
        current = get_ai_job(job["id"])
        if current and current["status"] in {"completed", "failed"}:
            final_job = current
            break
        sleep(0.05)
    assert final_job is not None
    assert final_job["status"] == "completed"
    assert final_job["report_id"]
    assert any(item["id"] == job["id"] for item in list_ai_jobs(opportunity_id=opportunity_id))


def test_ai_provider_defaults_to_local_and_parses_json() -> None:
    os.environ.pop("GOLDIDEAS_AI_PROVIDER", None)
    parsed = parse_report_content('{"executive_summary":{"recommendation":"validate"}}')
    assert parsed["executive_summary"]["recommendation"] == "validate"


def test_opportunity_and_report_queries() -> None:
    result = run_pipeline(
        fetch=False,
        sample_posts=[
            {
                "title": "Need a micro SaaS churn dashboard",
                "content": "Churn analysis is painful. I would pay for a simple dashboard.",
                "url": "https://example.com/churn-dashboard",
                "source": "sample",
                "source_group": "sample",
                "comments": 9,
            }
        ],
        query="dashboard",
        persist=True,
    )
    opportunity_id = result["opportunities"][0]["opportunity_id"]
    listed = list_opportunities(query="dashboard", limit=5)
    assert listed["total"] >= 1
    assert any(item["opportunity_id"] == opportunity_id for item in listed["items"])
    assert get_opportunity_record(opportunity_id)["opportunity_id"] == opportunity_id

    report = get_or_create_ai_report(opportunity_id, force=True)
    reports = list_ai_reports(opportunity_id=opportunity_id)
    assert any(item["id"] == report["id"] for item in reports)
    assert get_ai_report(report["id"])["id"] == report["id"]


if __name__ == "__main__":
    test_tech_redline()
    test_giant_alternative_is_opportunity()
    test_fake_question_without_pain_is_red()
    test_fingerprint_is_stable()
    test_pipeline_persists_and_ai_report_is_cached()
    test_sources_can_be_managed()
    test_search_job_lifecycle()
    test_ai_job_lifecycle()
    test_ai_provider_defaults_to_local_and_parses_json()
    test_opportunity_and_report_queries()
    print("All tests passed.")
