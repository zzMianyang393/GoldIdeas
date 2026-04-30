from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from demand_pipeline import DATA_DIR, run_pipeline
from ai_jobs import enqueue_ai_report_job
from ai_reports import get_or_create_ai_report
from storage import (
    complete_search_job,
    create_search_job,
    fail_search_job,
    get_latest_ai_report,
    get_ai_job,
    get_search_job,
    get_source,
    list_ai_jobs,
    list_runs,
    list_search_jobs,
    list_sources,
    set_source_enabled,
    upsert_source,
)


ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT.parent / "web"
HOST = "127.0.0.1"
PORT = 8765


class AppHandler(BaseHTTPRequestHandler):
    server_version = "GoldIdeasServer/4.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            self.send_json(load_status())
            return
        if parsed.path == "/api/report":
            report = latest_report()
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown; charset=utf-8")
            self.end_headers()
            self.wfile.write(report.encode("utf-8"))
            return
        if parsed.path == "/api/runs":
            self.send_json({"runs": list_runs()})
            return
        if parsed.path == "/api/sources":
            query = parse_qs(parsed.query)
            include_disabled = first_value(query.get("include_disabled")) != "false"
            self.send_json({"sources": list_sources(include_disabled=include_disabled)})
            return
        if parsed.path.startswith("/api/sources/"):
            source_id = parsed.path.removeprefix("/api/sources/").strip("/")
            source = get_source(source_id)
            if not source:
                self.send_json({"error": "Source not found"}, status=404)
                return
            self.send_json({"source": source})
            return
        if parsed.path == "/api/search-jobs":
            query = parse_qs(parsed.query)
            self.send_json({"search_jobs": list_search_jobs(limit=parse_int(first_value(query.get("limit")), 20))})
            return
        if parsed.path.startswith("/api/search-jobs/"):
            job_id = parsed.path.removeprefix("/api/search-jobs/").strip("/")
            job = get_search_job(job_id)
            if not job:
                self.send_json({"error": "Search job not found"}, status=404)
                return
            self.send_json({"search_job": job})
            return
        if parsed.path == "/api/ai/report":
            query = parse_qs(parsed.query)
            opportunity_id = first_value(query.get("opportunity_id") or query.get("id"))
            if not opportunity_id:
                self.send_json({"error": "Missing opportunity_id"}, status=400)
                return
            report = get_latest_ai_report(opportunity_id)
            if not report:
                self.send_json({"ready": False, "opportunity_id": opportunity_id})
                return
            self.send_json({"ready": True, "report": report})
            return
        if parsed.path == "/api/ai/jobs":
            query = parse_qs(parsed.query)
            self.send_json(
                {
                    "ai_jobs": list_ai_jobs(
                        limit=parse_int(first_value(query.get("limit")), 20),
                        opportunity_id=first_value(query.get("opportunity_id")),
                    )
                }
            )
            return
        if parsed.path.startswith("/api/ai/jobs/"):
            job_id = parsed.path.removeprefix("/api/ai/jobs/").strip("/")
            job = get_ai_job(job_id)
            if not job:
                self.send_json({"error": "AI job not found"}, status=404)
                return
            self.send_json({"ai_job": job})
            return
        self.serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/scan":
            payload = self.read_json()
            result = run_scan_from_payload(payload)
            self.send_json(slim_result(result))
            return
        if parsed.path == "/api/search-jobs":
            payload = self.read_json()
            job = create_search_job(normalize_scan_payload(payload), status="running")
            try:
                result = run_scan_from_payload(payload, search_job_id=job["id"])
                completed = complete_search_job(job["id"], result)
            except Exception as exc:
                failed = fail_search_job(job["id"], str(exc))
                self.send_json({"error": str(exc), "search_job": failed}, status=500)
                return
            response = slim_result(result)
            response["search_job"] = completed
            self.send_json(response)
            return
        if parsed.path == "/api/sources":
            payload = self.read_json()
            source = upsert_source(payload)
            self.send_json({"source": source})
            return
        if parsed.path.startswith("/api/sources/"):
            source_id = parsed.path.removeprefix("/api/sources/").strip("/")
            payload = self.read_json()
            if "enabled" in payload and len(payload) == 1:
                source = set_source_enabled(source_id, bool(payload["enabled"]))
            else:
                payload["id"] = source_id
                source = upsert_source(payload)
            if not source:
                self.send_json({"error": "Source not found"}, status=404)
                return
            self.send_json({"source": source})
            return
        if parsed.path == "/api/ai/report":
            payload = self.read_json()
            opportunity_id = payload.get("opportunity_id") or payload.get("id")
            if not opportunity_id:
                self.send_json({"error": "Missing opportunity_id"}, status=400)
                return
            try:
                report = get_or_create_ai_report(
                    opportunity_id,
                    force=bool(payload.get("force")),
                    report_type=payload.get("report_type") or "feasibility",
                )
            except ValueError as exc:
                self.send_json({"error": str(exc)}, status=404)
                return
            self.send_json({"ready": True, "report": report})
            return
        if parsed.path == "/api/ai/jobs":
            payload = self.read_json()
            opportunity_id = payload.get("opportunity_id") or payload.get("id")
            if not opportunity_id:
                self.send_json({"error": "Missing opportunity_id"}, status=400)
                return
            try:
                job = enqueue_ai_report_job(
                    opportunity_id,
                    report_type=payload.get("report_type") or "feasibility",
                    force=bool(payload.get("force")),
                    parameters=payload,
                )
            except ValueError as exc:
                self.send_json({"error": str(exc)}, status=404)
                return
            self.send_json({"ready": True, "ai_job": job}, status=202)
            return
        else:
            self.send_error(404)
            return

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length == 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_static(self, path: str) -> None:
        target = WEB_DIR / (path.lstrip("/") or "index.html")
        if target.is_dir():
            target = target / "index.html"
        try:
            resolved = target.resolve()
            resolved.relative_to(WEB_DIR.resolve())
        except ValueError:
            self.send_error(403)
            return
        if not resolved.exists():
            self.send_error(404)
            return
        content_type = mimetypes.guess_type(str(resolved))[0] or "application/octet-stream"
        body = resolved.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def latest_report() -> str:
    reports_dir = DATA_DIR / "reports"
    if not reports_dir.exists():
        return "No report yet. Run a scan first.\n"
    reports = sorted(reports_dir.glob("*.md"), reverse=True)
    if not reports:
        return "No report yet. Run a scan first.\n"
    return reports[0].read_text(encoding="utf-8")


def load_status() -> dict:
    path = DATA_DIR / "opportunities.json"
    if not path.exists():
        return {"ready": False, "message": "No scan data yet.", "counts": {"green": 0, "yellow": 0, "red": 0}, "opportunities": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {"ready": True, **data}


def slim_result(result: dict) -> dict:
    return {
        "ready": True,
        "metadata": result["metadata"],
        "counts": result["counts"],
        "redline_stats": result["redline_stats"],
        "opportunities": result["opportunities"],
        "report_path": result["report_path"],
    }


def first_value(values: list[str] | None) -> str | None:
    if not values:
        return None
    return values[0]


def parse_int(value: str | None, default: int) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


def normalize_scan_payload(payload: dict) -> dict:
    return {
        "limit": int(payload.get("limit") or 25),
        "subreddits": payload.get("subreddits") or None,
        "rating": payload.get("rating") or None,
        "quick": bool(payload.get("quick")),
        "query": payload.get("query") or None,
        "opportunity_type": payload.get("opportunity_type") or payload.get("type") or "micro_saas",
        "include_keywords": payload.get("include_keywords") or None,
        "exclude_keywords": payload.get("exclude_keywords") or None,
        "source_pack": payload.get("source_pack") or "default",
        "ai_depth": payload.get("ai_depth") or "none",
    }


def run_scan_from_payload(payload: dict, search_job_id: str | None = None) -> dict:
    normalized = normalize_scan_payload(payload)
    return run_pipeline(
        limit=normalized["limit"],
        subreddits=normalized["subreddits"],
        rating_filter=normalized["rating"],
        quick=normalized["quick"],
        query=normalized["query"],
        opportunity_type=normalized["opportunity_type"],
        include_keywords=normalized["include_keywords"],
        exclude_keywords=normalized["exclude_keywords"],
        source_pack=normalized["source_pack"],
        ai_depth=normalized["ai_depth"],
        search_job_id=search_job_id,
    )


def main() -> None:
    httpd = ThreadingHTTPServer((HOST, PORT), AppHandler)
    print(f"GoldIdeas server running at http://{HOST}:{PORT}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
