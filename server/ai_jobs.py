from __future__ import annotations

import threading
from typing import Any

from ai_reports import get_or_create_ai_report, input_hash_for
from storage import (
    complete_ai_job,
    create_ai_job,
    fail_ai_job,
    get_ai_job,
    get_opportunity,
    list_ai_jobs,
    mark_ai_job_running,
)


def enqueue_ai_report_job(
    opportunity_id: str,
    report_type: str = "feasibility",
    force: bool = False,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    opportunity = get_opportunity(opportunity_id)
    if not opportunity:
        raise ValueError("Opportunity not found")

    input_hash = input_hash_for(opportunity, report_type=report_type)
    job = create_ai_job(
        opportunity_id=opportunity_id,
        report_type=report_type,
        force=force,
        parameters=parameters or {},
        input_hash=input_hash,
    )
    thread = threading.Thread(target=run_ai_report_job, args=(job["id"],), daemon=True)
    thread.start()
    return job


def run_ai_report_job(job_id: str) -> None:
    job = get_ai_job(job_id)
    if not job:
        return

    mark_ai_job_running(job_id)
    try:
        report = get_or_create_ai_report(
            job["opportunity_id"],
            force=job["force"],
            report_type=job["report_type"],
        )
    except Exception as exc:
        fail_ai_job(job_id, str(exc))
        return

    complete_ai_job(job_id, report)


__all__ = ["enqueue_ai_report_job", "get_ai_job", "list_ai_jobs"]
