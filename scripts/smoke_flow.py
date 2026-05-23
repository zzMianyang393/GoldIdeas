from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVER_DIR = ROOT / "server"
sys.path.insert(0, str(SERVER_DIR))

from app import slugify  # noqa: E402
from demand_pipeline import run_pipeline  # noqa: E402


HOST = "127.0.0.1"
PORT = int(os.getenv("GOLDIDEAS_SMOKE_PORT", "8876"))
BASE_URL = f"http://{HOST}:{PORT}"


def request(path: str, method: str = "GET", payload: dict | None = None) -> tuple[int, bytes]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=12) as response:
        return response.status, response.read()


def request_json(path: str, method: str = "GET", payload: dict | None = None) -> dict:
    status, body = request(path, method=method, payload=payload)
    if status >= 400:
        raise RuntimeError(f"{method} {path} returned {status}")
    return json.loads(body.decode("utf-8"))


def wait_for_server(process: subprocess.Popen[bytes]) -> None:
    deadline = time.time() + 20
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Backend process exited before it became ready")
        try:
            request("/api/status")
            return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.25)
    raise RuntimeError("Backend did not become ready in time")


def seed_opportunity() -> tuple[str, str]:
    result = run_pipeline(
        fetch=False,
        sample_posts=[
            {
                "title": "Need Shopify returns automation reports",
                "content": "Returns waste time and I would pay monthly for automation that handles refund status updates.",
                "url": "https://example.com/smoke-returns-report",
                "source": "sample",
                "source_group": "sample",
                "comments": 14,
            },
            {
                "title": "Shopify refund workflow is too manual",
                "content": "Our support team spends hours on return labels, refund messages, and status follow ups.",
                "url": "https://example.com/smoke-refund-workflow",
                "source": "sample",
                "source_group": "sample",
                "comments": 7,
            },
        ],
        query="shopify returns automation",
        opportunity_type="ecommerce_tools",
        persist=True,
    )
    opportunity = result["opportunities"][0]
    return opportunity["opportunity_id"], slugify(opportunity["title"])


def main() -> None:
    opportunity_id, slug = seed_opportunity()
    env = os.environ.copy()
    env["GOLDIDEAS_HOST"] = HOST
    env["GOLDIDEAS_PORT"] = str(PORT)
    process = subprocess.Popen(
        [sys.executable, str(SERVER_DIR / "app.py")],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        wait_for_server(process)

        status = request_json("/api/status")
        assert status.get("ready") is True

        opportunities = request_json("/api/opportunities?q=shopify")
        assert opportunities.get("total", 0) >= 1

        report = request_json("/api/ai/report", method="POST", payload={"opportunity_id": opportunity_id})
        assert report.get("ready") is True

        for path in [
            "/public-opportunities.json",
            "/opportunities.xml",
            "/llms.txt",
            "/sitemap.xml",
            f"/opportunities/{slug}",
            f"/opportunities/{slug}.md",
        ]:
            status_code, body = request(path)
            assert status_code == 200, path
            assert body, path

        email = f"smoke-{int(time.time())}@example.com"
        signup = request_json(
            "/api/waitlist",
            method="POST",
            payload={
                "email": email,
                "public_slug": slug,
                "query": "shopify returns automation",
                "opportunity_id": opportunity_id,
                "source": "smoke_flow",
            },
        )
        assert signup["signup"]["email"] == email

        stats = request_json("/api/waitlist/stats")
        assert stats["stats"]["total"] >= 1
        print("Smoke flow passed.")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    main()
