from __future__ import annotations

import csv
import html
import io
import json
import mimetypes
import os
import re
from datetime import datetime
from email.utils import format_datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from demand_pipeline import DATA_DIR, run_pipeline
from ai_jobs import enqueue_ai_report_job
from ai_reports import get_or_create_ai_report
from storage import (
    complete_search_job,
    create_waitlist_signup,
    count_waitlist_signups_by_slug,
    create_search_job,
    fail_search_job,
    get_run,
    get_signal,
    get_latest_ai_report,
    get_ai_report,
    get_ai_job,
    get_opportunity_record,
    get_search_job,
    get_source,
    list_ai_jobs,
    list_ai_reports,
    list_opportunities,
    list_opportunity_signals,
    list_runs,
    list_search_jobs,
    list_signals,
    list_sources,
    list_waitlist_signups,
    set_source_enabled,
    upsert_source,
    waitlist_stats,
)


ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT.parent / "web"
HOST = os.getenv("GOLDIDEAS_HOST", "127.0.0.1")
PORT = int(os.getenv("GOLDIDEAS_PORT", "8765"))


class AppHandler(BaseHTTPRequestHandler):
    server_version = "GoldIdeasServer/4.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            self.send_json(load_status())
            return
        if parsed.path == "/api/config":
            self.send_json({"public_base_url": public_base_url()})
            return
        if parsed.path == "/api/report":
            report = latest_report()
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown; charset=utf-8")
            self.end_headers()
            self.wfile.write(report.encode("utf-8"))
            return
        if parsed.path == "/sitemap.xml":
            self.send_text(build_sitemap(), content_type="application/xml; charset=utf-8")
            return
        if parsed.path == "/robots.txt":
            self.send_text(build_robots_txt(), content_type="text/plain; charset=utf-8")
            return
        if parsed.path == "/llms.txt":
            self.send_text(build_llms_txt(), content_type="text/plain; charset=utf-8")
            return
        if parsed.path == "/public-opportunities.json":
            self.send_json({"opportunities": public_opportunity_feed()})
            return
        if parsed.path == "/opportunities.xml":
            self.send_text(build_opportunities_rss(), content_type="application/rss+xml; charset=utf-8")
            return
        if parsed.path.startswith("/opportunities/") and parsed.path.endswith(".md"):
            slug = parsed.path.removeprefix("/opportunities/").removesuffix(".md").strip("/")
            markdown = public_opportunity_markdown(slug)
            if not markdown:
                self.send_text("Opportunity report not found.\n", content_type="text/markdown; charset=utf-8", status=404)
                return
            self.send_text(markdown, content_type="text/markdown; charset=utf-8")
            return
        if parsed.path == "/api/runs":
            self.send_json({"runs": list_runs()})
            return
        if parsed.path.startswith("/api/runs/"):
            run_id = parsed.path.removeprefix("/api/runs/").strip("/")
            run = get_run(run_id)
            if not run:
                self.send_json({"error": "Run not found"}, status=404)
                return
            self.send_json({"run": run})
            return
        if parsed.path == "/api/signals":
            query = parse_qs(parsed.query)
            result = list_signals(
                limit=parse_int(first_value(query.get("limit")), 50),
                offset=parse_int(first_value(query.get("offset")), 0),
                query=first_value(query.get("q")) or first_value(query.get("query")),
                source=first_value(query.get("source")),
                source_group=first_value(query.get("source_group")),
            )
            self.send_json({"signals": result["items"], "total": result["total"], "limit": result["limit"], "offset": result["offset"]})
            return
        if parsed.path.startswith("/api/signals/"):
            signal_id = parsed.path.removeprefix("/api/signals/").strip("/")
            signal = get_signal(signal_id)
            if not signal:
                self.send_json({"error": "Signal not found"}, status=404)
                return
            self.send_json({"signal": signal})
            return
        if parsed.path == "/api/opportunities":
            query = parse_qs(parsed.query)
            result = list_opportunities(
                limit=parse_int(first_value(query.get("limit")), 50),
                offset=parse_int(first_value(query.get("offset")), 0),
                rating=first_value(query.get("rating")),
                query=first_value(query.get("q")) or first_value(query.get("query")),
                source_group=first_value(query.get("source_group")),
            )
            self.send_json({"opportunities": result["items"], "total": result["total"], "limit": result["limit"], "offset": result["offset"]})
            return
        if parsed.path.startswith("/api/opportunities/") and parsed.path.endswith("/signals"):
            opportunity_id = parsed.path.removeprefix("/api/opportunities/").removesuffix("/signals").strip("/")
            opportunity = get_opportunity_record(opportunity_id)
            if not opportunity:
                self.send_json({"error": "Opportunity not found"}, status=404)
                return
            self.send_json({"opportunity_id": opportunity_id, "signals": list_opportunity_signals(opportunity_id)})
            return
        if parsed.path.startswith("/api/opportunities/"):
            opportunity_id = parsed.path.removeprefix("/api/opportunities/").strip("/")
            opportunity = get_opportunity_record(opportunity_id)
            if not opportunity:
                self.send_json({"error": "Opportunity not found"}, status=404)
                return
            self.send_json({"opportunity": opportunity})
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
        if parsed.path == "/api/waitlist":
            query = parse_qs(parsed.query)
            self.send_json({"waitlist": list_waitlist_signups(limit=parse_int(first_value(query.get("limit")), 50))})
            return
        if parsed.path == "/api/waitlist/stats":
            self.send_json({"stats": waitlist_stats()})
            return
        if parsed.path == "/api/waitlist.csv":
            query = parse_qs(parsed.query)
            self.send_text(
                waitlist_csv(limit=parse_int(first_value(query.get("limit")), 500)),
                content_type="text/csv; charset=utf-8",
            )
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
        if parsed.path == "/api/ai/reports":
            query = parse_qs(parsed.query)
            self.send_json(
                {
                    "ai_reports": list_ai_reports(
                        limit=parse_int(first_value(query.get("limit")), 20),
                        opportunity_id=first_value(query.get("opportunity_id")),
                        report_type=first_value(query.get("report_type")),
                    )
                }
            )
            return
        if parsed.path.startswith("/api/ai/reports/"):
            report_id = parsed.path.removeprefix("/api/ai/reports/").strip("/")
            report = get_ai_report(report_id)
            if not report:
                self.send_json({"error": "AI report not found"}, status=404)
                return
            self.send_json({"report": report})
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
        if parsed.path == "/api/waitlist":
            payload = self.read_json()
            try:
                signup = create_waitlist_signup(payload)
            except ValueError as exc:
                self.send_json({"error": str(exc)}, status=400)
                return
            self.send_json({"signup": signup}, status=201)
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

    def send_text(self, body: str, content_type: str = "text/plain; charset=utf-8", status: int = 200) -> None:
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def serve_static(self, path: str) -> None:
        target = WEB_DIR / (path.lstrip("/") or "index.html")
        public_target = WEB_DIR / "public" / path.lstrip("/")
        if target.is_dir():
            target = target / "index.html"
        try:
            resolved = target.resolve()
            resolved.relative_to(WEB_DIR.resolve())
        except ValueError:
            self.send_error(403)
            return
        if not resolved.exists():
            try:
                public_resolved = public_target.resolve()
                public_resolved.relative_to((WEB_DIR / "public").resolve())
            except ValueError:
                self.send_error(403)
                return
            if public_resolved.exists():
                resolved = public_resolved
            elif "." not in Path(path).name:
                resolved = WEB_DIR / "index.html"
            else:
                self.send_error(404)
                return
        content_type = mimetypes.guess_type(str(resolved))[0] or "application/octet-stream"
        if resolved.name == "index.html":
            body = render_index_html(resolved, path).encode("utf-8")
            content_type = "text/html; charset=utf-8"
        else:
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


def slugify(value: str) -> str:
    import re

    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return slug[:90] or "opportunity"


def public_base_url() -> str:
    configured = os.getenv("GOLDIDEAS_PUBLIC_BASE_URL") or os.getenv("PUBLIC_BASE_URL")
    if configured:
        return configured.rstrip("/")
    return f"http://{HOST}:{PORT}"


def render_index_html(index_path: Path, request_path: str) -> str:
    body = index_path.read_text(encoding="utf-8")
    meta = metadata_for_path(request_path)
    title = meta["title"]
    body = re.sub(r"<title>.*?</title>", f"<title>{html.escape(title)}</title>", body, flags=re.IGNORECASE | re.DOTALL)
    tags = [
        f'<meta name="description" content="{html.escape(meta["description"])}" />',
        f'<meta property="og:title" content="{html.escape(title)}" />',
        f'<meta property="og:description" content="{html.escape(meta["description"])}" />',
        f'<meta property="og:type" content="{meta["type"]}" />',
        f'<meta property="og:url" content="{html.escape(meta["url"])}" />',
        f'<link rel="canonical" href="{html.escape(meta["url"])}" />',
        '<script type="application/ld+json">'
        + json.dumps(meta["json_ld"], ensure_ascii=False, separators=(",", ":"))
        + "</script>",
    ]
    return body.replace("</head>", "    " + "\n    ".join(tags) + "\n  </head>")


def metadata_for_path(request_path: str) -> dict:
    base_url = public_base_url()
    default = {
        "title": "GoldIdeas - Source-backed SaaS validation",
        "description": "Validate SaaS opportunities with live evidence, buyer signals, risks, and GO / PIVOT / KILL reports.",
        "type": "website",
        "url": f"{base_url}/",
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": "GoldIdeas",
            "applicationCategory": "BusinessApplication",
            "description": "Source-backed SaaS opportunity validation workspace.",
        },
    }
    if not request_path.startswith("/opportunities/"):
        return default

    slug = request_path.removeprefix("/opportunities/").strip("/")
    page = next((item for item in public_opportunity_feed() if item["slug"] == slug), None)
    title = page.get("title") if page else query_from_slug(slug).title()
    description = (page.get("summary") if page else "") or f"Source-backed validation report for {title}."
    url = f"{base_url}/opportunities/{slug}"
    return {
        "title": f"{title} - GoldIdeas opportunity report",
        "description": description[:220],
        "type": "article",
        "url": url,
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description[:220],
            "url": url,
            "isPartOf": {"@type": "WebSite", "name": "GoldIdeas", "url": f"{base_url}/"},
        },
    }


def query_from_slug(slug: str) -> str:
    return slug.replace("-", " ").strip() or "SaaS opportunity"


def public_opportunity_feed(limit: int = 100) -> list[dict]:
    base_url = public_base_url()
    result = list_opportunities(limit=limit)
    lead_counts = count_waitlist_signups_by_slug()
    items = []
    for item in result.get("items", []):
        slug = slugify(item.get("title") or item.get("opportunity_id") or "opportunity")
        path = f"/opportunities/{slug}"
        markdown_path = f"{path}.md"
        items.append(
            {
                "id": item.get("opportunity_id") or item.get("id"),
                "slug": slug,
                "path": path,
                "url": f"{base_url}{path}",
                "markdown_path": markdown_path,
                "markdown_url": f"{base_url}{markdown_path}",
                "title": item.get("title"),
                "summary": item.get("content_summary"),
                "rating": item.get("rating"),
                "total_score": item.get("total_score"),
                "evidence_count": item.get("evidence_count") or 1,
                "source_count": item.get("source_count") or 1,
                "lead_count": lead_counts.get(slug, 0),
                "last_seen_at": item.get("last_seen_at"),
            }
        )
    return items


def public_opportunity_markdown(slug: str) -> str | None:
    page = next((item for item in public_opportunity_feed() if item["slug"] == slug), None)
    if not page:
        return None
    opportunity = get_opportunity_record(page["id"])
    if not opportunity:
        return None
    signals = list_opportunity_signals(page["id"])[:8]
    lines = [
        f"# {opportunity.get('title') or page['slug']}",
        "",
        f"- Public URL: {page['url']}",
        f"- Rating: {opportunity.get('rating') or 'UNRATED'}",
        f"- Score: {float(opportunity.get('total_score') or 0):.1f}/10",
        f"- Evidence signals: {opportunity.get('evidence_count') or page.get('evidence_count') or 1}",
        f"- Sources: {opportunity.get('source_count') or page.get('source_count') or 1}",
        f"- Leads captured: {page.get('lead_count') or 0}",
        "",
        "## Summary",
        "",
        markdown_text(opportunity.get("content_summary") or page.get("summary") or "No summary available yet."),
        "",
        "## Key Insight",
        "",
        markdown_text(opportunity.get("key_insight") or "No key insight has been generated yet."),
        "",
        "## Validation Action",
        "",
        markdown_text(opportunity.get("action_items") or "Run a validation scan and interview buyers before building."),
        "",
        "## Cluster Keywords",
        "",
    ]
    keywords = opportunity.get("cluster_keywords") or []
    lines.append(", ".join(keywords) if keywords else "No keywords available.")
    lines.extend(["", "## Score Breakdown", ""])
    scores = opportunity.get("scores") if isinstance(opportunity.get("scores"), dict) else {}
    if scores:
        for name, value in scores.items():
            try:
                lines.append(f"- {name}: {float(value):.1f}/10")
            except (TypeError, ValueError):
                lines.append(f"- {name}: {value}")
    else:
        lines.append("- No score breakdown available.")
    lines.extend(["", "## Evidence Signals", ""])
    if signals:
        for signal in signals:
            title = signal.get("title") or "Untitled signal"
            source = signal.get("source") or signal.get("source_group") or "source"
            url = signal.get("url") or signal.get("comments_url") or ""
            if url:
                lines.append(f"- [{markdown_link_text(title)}]({url}) - {markdown_text(source)}")
            else:
                lines.append(f"- {markdown_text(title)} - {markdown_text(source)}")
    else:
        lines.append("- No linked evidence signals are available yet.")
    lines.extend(
        [
            "",
            "## Agent Notes",
            "",
            "- Treat this as a validation lead, not a build order.",
            "- Confirm willingness to pay, alternatives, platform risk, and MVP scope before implementation.",
            "- Use the public JSON feed for structured discovery and this Markdown page for citation-friendly summaries.",
            "",
        ]
    )
    return "\n".join(lines)


def markdown_text(value: object) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()
    return re.sub(r"\s+", " ", text)


def markdown_link_text(value: object) -> str:
    return markdown_text(value).replace("[", "(").replace("]", ")")


def build_sitemap() -> str:
    base_url = public_base_url()
    urls = [
        (f"{base_url}/", ""),
        (f"{base_url}/public-opportunities.json", ""),
        (f"{base_url}/opportunities.xml", ""),
    ]
    for item in public_opportunity_feed():
        lastmod = item.get("last_seen_at") or ""
        urls.append((item["url"], lastmod[:10] if lastmod else ""))
        urls.append((item["markdown_url"], lastmod[:10] if lastmod else ""))
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{html.escape(loc)}</loc>")
        if lastmod:
            lines.append(f"    <lastmod>{html.escape(lastmod)}</lastmod>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def build_opportunities_rss(limit: int = 50) -> str:
    base_url = public_base_url()
    feed = public_opportunity_feed(limit=limit)
    latest = next((item.get("last_seen_at") for item in feed if item.get("last_seen_at")), "")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        "  <channel>",
        "    <title>GoldIdeas Public Opportunities</title>",
        f"    <link>{html.escape(base_url + '/')}</link>",
        "    <description>Source-backed SaaS opportunity reports generated from live market signals.</description>",
        f"    <atom:link href=\"{html.escape(base_url + '/opportunities.xml')}\" rel=\"self\" type=\"application/rss+xml\" />",
    ]
    if latest:
        lines.append(f"    <lastBuildDate>{html.escape(rss_date(latest))}</lastBuildDate>")
    for item in feed:
        title = item.get("title") or item.get("slug") or "Opportunity"
        summary = item.get("summary") or "Source-backed SaaS opportunity report."
        pub_date = item.get("last_seen_at") or ""
        description = (
            f"{summary} Rating: {item.get('rating') or 'UNRATED'}. "
            f"Evidence: {item.get('evidence_count') or 1} signals across {item.get('source_count') or 1} sources. "
            f"Markdown: {item.get('markdown_url') or ''}"
        )
        lines.extend(
            [
                "    <item>",
                f"      <title>{html.escape(title)}</title>",
                f"      <link>{html.escape(item['url'])}</link>",
                f"      <guid isPermaLink=\"true\">{html.escape(item['url'])}</guid>",
                f"      <description>{html.escape(description)}</description>",
            ]
        )
        if pub_date:
            lines.append(f"      <pubDate>{html.escape(rss_date(pub_date))}</pubDate>")
        lines.append("    </item>")
    lines.extend(["  </channel>", "</rss>", ""])
    return "\n".join(lines)


def rss_date(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
    return format_datetime(parsed)


def build_robots_txt() -> str:
    base_url = public_base_url()
    return "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            f"Sitemap: {base_url}/sitemap.xml",
            f"Host: {base_url}",
            "",
        ]
    )


def build_llms_txt(limit: int = 20) -> str:
    base_url = public_base_url()
    lines = [
        "# GoldIdeas",
        "",
        "GoldIdeas is a source-backed SaaS opportunity validation workspace. It turns live community signals into evidence-backed opportunity reports with pain patterns, buyer intent, competitor gaps, distribution paths, and GO / PIVOT / KILL verdicts.",
        "",
        "## Primary URLs",
        f"- Home: {base_url}/",
        f"- Public opportunity feed: {base_url}/public-opportunities.json",
        f"- RSS feed: {base_url}/opportunities.xml",
        f"- Sitemap: {base_url}/sitemap.xml",
        f"- AI manifest: {base_url}/.well-known/ai.json",
        "",
        "## API Entry Points",
        f"- List opportunities: {base_url}/api/opportunities?limit=50&q={{query}}",
        f"- Run validation scan: POST {base_url}/api/scan",
        f"- Create report: POST {base_url}/api/ai/report",
        f"- Join waitlist: POST {base_url}/api/waitlist",
        "",
        "## Public Opportunity Pages",
    ]
    feed = public_opportunity_feed(limit=limit)
    if not feed:
        lines.append("- No public opportunity pages have been generated yet.")
    for item in feed:
        summary = (item.get("summary") or "").replace("\n", " ").strip()
        if len(summary) > 180:
            summary = summary[:177].rstrip() + "..."
        lines.append(
            f"- [{item.get('title') or item.get('slug')}]({item['url']}): "
            f"{item.get('rating') or 'UNRATED'}, {item.get('evidence_count') or 1} evidence signals, "
            f"{item.get('lead_count') or 0} leads. Markdown: {item['markdown_url']}. {summary}"
        )
    lines.extend(
        [
            "",
            "## Guidance For Agents",
            "- Prefer public opportunity pages for human-readable summaries.",
            "- Use /public-opportunities.json for structured discovery.",
            "- When validating a new idea, call /api/scan with a concise query and opportunity_type.",
            "- Do not assume an opportunity is build-ready until the report verdict and cited evidence are reviewed.",
            "",
        ]
    )
    return "\n".join(lines)


def waitlist_csv(limit: int = 500) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "email",
            "query",
            "public_slug",
            "opportunity_id",
            "source",
            "utm",
            "created_at",
        ],
    )
    writer.writeheader()
    for item in list_waitlist_signups(limit=limit):
        writer.writerow(
            {
                "email": item.get("email") or "",
                "query": item.get("query") or "",
                "public_slug": item.get("public_slug") or "",
                "opportunity_id": item.get("opportunity_id") or "",
                "source": item.get("source") or "",
                "utm": json.dumps(item.get("utm") or {}, ensure_ascii=False),
                "created_at": item.get("created_at") or "",
            }
        )
    return buffer.getvalue()


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
