from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "goldideas.db"

DEFAULT_SOURCES = [
    {
        "id": "reddit_indiehackers",
        "name": "r/indiehackers",
        "type": "reddit_rss",
        "url": "https://www.reddit.com/r/indiehackers/.rss",
        "source_pack": "micro_saas",
    },
    {
        "id": "reddit_microsaas",
        "name": "r/microsaas",
        "type": "reddit_rss",
        "url": "https://www.reddit.com/r/microsaas/.rss",
        "source_pack": "micro_saas",
    },
    {
        "id": "reddit_saas",
        "name": "r/SaaS",
        "type": "reddit_rss",
        "url": "https://www.reddit.com/r/SaaS/.rss",
        "source_pack": "micro_saas",
    },
    {
        "id": "reddit_entrepreneurridealong",
        "name": "r/EntrepreneurRideAlong",
        "type": "reddit_rss",
        "url": "https://www.reddit.com/r/EntrepreneurRideAlong/.rss",
        "source_pack": "micro_saas",
    },
    {
        "id": "reddit_sideproject",
        "name": "r/SideProject",
        "type": "reddit_rss",
        "url": "https://www.reddit.com/r/SideProject/.rss",
        "source_pack": "micro_saas",
    },
    {
        "id": "reddit_solopreneur",
        "name": "r/solopreneur",
        "type": "reddit_rss",
        "url": "https://www.reddit.com/r/solopreneur/.rss",
        "source_pack": "micro_saas",
    },
    {
        "id": "reddit_freelance",
        "name": "r/freelance",
        "type": "reddit_rss",
        "url": "https://www.reddit.com/r/freelance/.rss",
        "source_pack": "micro_saas",
    },
    {
        "id": "reddit_webdev",
        "name": "r/webdev",
        "type": "reddit_rss",
        "url": "https://www.reddit.com/r/webdev/.rss",
        "source_pack": "developer_tools",
    },
    {
        "id": "reddit_nocode",
        "name": "r/nocode",
        "type": "reddit_rss",
        "url": "https://www.reddit.com/r/nocode/.rss",
        "source_pack": "micro_saas",
    },
    {
        "id": "reddit_smallbusiness",
        "name": "r/smallbusiness",
        "type": "reddit_rss",
        "url": "https://www.reddit.com/r/smallbusiness/.rss",
        "source_pack": "micro_saas",
    },
    {
        "id": "reddit_apps",
        "name": "r/apps",
        "type": "reddit_rss",
        "url": "https://www.reddit.com/r/apps/.rss",
        "source_pack": "micro_saas",
    },
    {
        "id": "reddit_webhosting",
        "name": "r/webhosting",
        "type": "reddit_rss",
        "url": "https://www.reddit.com/r/webhosting/.rss",
        "source_pack": "developer_tools",
    },
    {
        "id": "hackernews_rss",
        "name": "Hacker News",
        "type": "rss",
        "url": "https://hnrss.org/newest?points=10",
        "source_pack": "default",
    },
    {
        "id": "hackernews_search",
        "name": "Hacker News Search",
        "type": "json_search",
        "url": "https://hn.algolia.com/api/v1/search_by_date",
        "source_pack": "default",
    },
    {
        "id": "producthunt_rss",
        "name": "Product Hunt",
        "type": "rss",
        "url": "https://www.producthunt.com/feed",
        "source_pack": "default",
    },
    {
        "id": "indiehackers_rss",
        "name": "Indie Hackers",
        "type": "rss",
        "url": "https://www.indiehackers.com/feed",
        "source_pack": "micro_saas",
    },
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            generated_at TEXT NOT NULL,
            parameters_json TEXT NOT NULL,
            source_count INTEGER NOT NULL DEFAULT 0,
            raw_count INTEGER NOT NULL DEFAULT 0,
            opportunity_count INTEGER NOT NULL DEFAULT 0,
            green_count INTEGER NOT NULL DEFAULT 0,
            yellow_count INTEGER NOT NULL DEFAULT 0,
            red_count INTEGER NOT NULL DEFAULT 0,
            errors_json TEXT NOT NULL DEFAULT '[]',
            report_path TEXT
        );

        CREATE TABLE IF NOT EXISTS signals (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            source_group TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            url TEXT,
            comments_url TEXT,
            comments INTEGER NOT NULL DEFAULT 0,
            published_at TEXT,
            fetched_at TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            raw_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS opportunities (
            id TEXT PRIMARY KEY,
            fingerprint TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            canonical_summary TEXT,
            primary_source TEXT,
            source_group TEXT,
            url TEXT,
            category TEXT,
            rating TEXT,
            total_score REAL NOT NULL DEFAULT 0,
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            seen_count INTEGER NOT NULL DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'active',
            latest_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS opportunity_signals (
            opportunity_id TEXT NOT NULL,
            signal_id TEXT NOT NULL,
            relation_type TEXT NOT NULL DEFAULT 'primary',
            confidence REAL NOT NULL DEFAULT 1.0,
            PRIMARY KEY (opportunity_id, signal_id),
            FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE,
            FOREIGN KEY (signal_id) REFERENCES signals(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opportunity_id TEXT NOT NULL,
            run_id TEXT NOT NULL,
            scoring_profile TEXT NOT NULL,
            scores_json TEXT NOT NULL,
            reasons_json TEXT NOT NULL,
            redlines_json TEXT NOT NULL,
            rating TEXT NOT NULL,
            total_score REAL NOT NULL,
            generated_at TEXT NOT NULL,
            FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE,
            FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ai_reports (
            id TEXT PRIMARY KEY,
            opportunity_id TEXT NOT NULL,
            report_type TEXT NOT NULL,
            status TEXT NOT NULL,
            report_json TEXT,
            report_markdown TEXT,
            provider TEXT,
            model TEXT,
            prompt_version TEXT,
            report_template_version TEXT,
            scoring_profile_version TEXT,
            input_hash TEXT NOT NULL,
            token_usage INTEGER NOT NULL DEFAULT 0,
            cost_estimate REAL NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            generated_at TEXT,
            expires_at TEXT,
            UNIQUE (opportunity_id, report_type, input_hash),
            FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ai_jobs (
            id TEXT PRIMARY KEY,
            opportunity_id TEXT NOT NULL,
            report_type TEXT NOT NULL,
            status TEXT NOT NULL,
            force INTEGER NOT NULL DEFAULT 0,
            input_hash TEXT,
            report_id TEXT,
            error TEXT NOT NULL DEFAULT '',
            parameters_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            started_at TEXT,
            completed_at TEXT,
            FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS search_jobs (
            id TEXT PRIMARY KEY,
            query TEXT,
            mode TEXT NOT NULL,
            source_pack TEXT,
            scoring_profile TEXT,
            ai_depth TEXT,
            run_id TEXT,
            result_counts_json TEXT NOT NULL DEFAULT '{}',
            parameters_json TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            completed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS sources (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            url TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            source_pack TEXT NOT NULL DEFAULT 'default',
            config_json TEXT NOT NULL DEFAULT '{}',
            last_status TEXT NOT NULL DEFAULT 'unknown',
            last_error TEXT NOT NULL DEFAULT '',
            last_fetched_at TEXT,
            last_item_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )
    ensure_column(conn, "search_jobs", "run_id", "TEXT")
    ensure_column(conn, "search_jobs", "result_counts_json", "TEXT NOT NULL DEFAULT '{}'")
    seed_default_sources(conn)
    conn.commit()


def ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    if any(row["name"] == column for row in rows):
        return
    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def seed_default_sources(conn: sqlite3.Connection) -> None:
    timestamp = now_iso()
    for source in DEFAULT_SOURCES:
        conn.execute(
            """
            INSERT OR IGNORE INTO sources (
                id, name, type, url, enabled, source_pack, config_json,
                last_status, last_error, last_fetched_at, last_item_count,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, 1, ?, '{}', 'unknown', '', '', 0, ?, ?)
            """,
            (
                source["id"],
                source["name"],
                source["type"],
                source["url"],
                source["source_pack"],
                timestamp,
                timestamp,
            ),
        )


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def loads(value: str | None, fallback: Any = None) -> Any:
    if value is None:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def persist_pipeline_result(result: dict[str, Any]) -> None:
    metadata = result["metadata"]
    opportunities = result["opportunities"]
    posts = result["posts"]
    counts = result["counts"]
    run_id = metadata["run_id"]
    generated_at = metadata["generated_at"]

    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO runs (
                id, generated_at, parameters_json, source_count, raw_count,
                opportunity_count, green_count, yellow_count, red_count,
                errors_json, report_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                generated_at,
                dumps(metadata.get("parameters", {})),
                int(metadata.get("source_count") or 0),
                int(metadata.get("raw_count") or 0),
                len(opportunities),
                int(counts.get("green") or 0),
                int(counts.get("yellow") or 0),
                int(counts.get("red") or 0),
                dumps(metadata.get("errors", [])),
                result.get("report_path"),
            ),
        )

        for post in posts:
            conn.execute(
                """
                INSERT OR REPLACE INTO signals (
                    id, source, source_group, title, content, url, comments_url,
                    comments, published_at, fetched_at, content_hash, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    post["signal_id"],
                    post.get("source") or "",
                    post.get("source_group") or "",
                    post.get("title") or "",
                    post.get("content") or "",
                    post.get("url") or "",
                    post.get("comments_url") or "",
                    int(post.get("comments") or 0),
                    post.get("published") or "",
                    generated_at,
                    post["content_hash"],
                    dumps(post),
                ),
        )

        update_sources_from_run(conn, posts, metadata.get("errors", []), generated_at)

        for item in opportunities:
            existing = conn.execute(
                "SELECT first_seen_at, seen_count FROM opportunities WHERE id = ?",
                (item["opportunity_id"],),
            ).fetchone()
            first_seen_at = existing["first_seen_at"] if existing else generated_at
            seen_count = int(existing["seen_count"]) + 1 if existing else 1
            conn.execute(
                """
                INSERT INTO opportunities (
                    id, fingerprint, title, canonical_summary, primary_source,
                    source_group, url, category, rating, total_score,
                    first_seen_at, last_seen_at, seen_count, status, latest_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    canonical_summary = excluded.canonical_summary,
                    primary_source = excluded.primary_source,
                    source_group = excluded.source_group,
                    url = excluded.url,
                    category = excluded.category,
                    rating = excluded.rating,
                    total_score = excluded.total_score,
                    last_seen_at = excluded.last_seen_at,
                    seen_count = excluded.seen_count,
                    latest_json = excluded.latest_json
                """,
                (
                    item["opportunity_id"],
                    item["fingerprint"],
                    item.get("title") or "",
                    item.get("content_summary") or "",
                    item.get("source") or "",
                    item.get("source_group") or "",
                    item.get("url") or "",
                    item.get("category", {}).get("name", ""),
                    item.get("rating") or "",
                    float(item.get("total_score") or 0),
                    first_seen_at,
                    generated_at,
                    seen_count,
                    "active",
                    dumps(item),
                ),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO opportunity_signals (
                    opportunity_id, signal_id, relation_type, confidence
                ) VALUES (?, ?, 'primary', 1.0)
                """,
                (item["opportunity_id"], item["signal_id"]),
            )
            conn.execute(
                """
                INSERT INTO scores (
                    opportunity_id, run_id, scoring_profile, scores_json,
                    reasons_json, redlines_json, rating, total_score, generated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["opportunity_id"],
                    run_id,
                    metadata.get("scoring_profile") or "micro_saas_v4_1",
                    dumps(item.get("scores", {})),
                    dumps(item.get("score_reasons", {})),
                    dumps(item.get("redlines", [])),
                    item.get("rating") or "",
                    float(item.get("total_score") or 0),
                    generated_at,
                ),
            )
        conn.commit()


def update_sources_from_run(conn: sqlite3.Connection, posts: list[dict[str, Any]], errors: list[dict[str, Any]], timestamp: str) -> None:
    counts: dict[str, int] = {}
    for post in posts:
        source = post.get("source") or "unknown"
        counts[source] = counts.get(source, 0) + 1

    for source, count in counts.items():
        source_id = source_id_for(source)
        conn.execute(
            """
            INSERT INTO sources (
                id, name, type, url, enabled, source_pack, config_json,
                last_status, last_error, last_fetched_at, last_item_count,
                created_at, updated_at
            ) VALUES (?, ?, 'auto', '', 1, 'default', '{}', 'ok', '', ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                last_status = 'ok',
                last_error = '',
                last_fetched_at = excluded.last_fetched_at,
                last_item_count = excluded.last_item_count,
                updated_at = excluded.updated_at
            """,
            (source_id, source, timestamp, count, timestamp, timestamp),
        )

    for error in errors:
        source = error.get("source") or "unknown"
        source_id = source_id_for(source)
        conn.execute(
            """
            INSERT INTO sources (
                id, name, type, url, enabled, source_pack, config_json,
                last_status, last_error, last_fetched_at, last_item_count,
                created_at, updated_at
            ) VALUES (?, ?, 'auto', '', 1, 'default', '{}', 'error', ?, ?, 0, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                last_status = 'error',
                last_error = excluded.last_error,
                last_fetched_at = excluded.last_fetched_at,
                updated_at = excluded.updated_at
            """,
            (source_id, source, error.get("error") or "Unknown error", timestamp, timestamp, timestamp),
        )


def source_id_for(name: str) -> str:
    from demand_pipeline import stable_hash

    normalized = name.lower().replace("/", "_").replace(" ", "_")
    normalized = "".join(ch for ch in normalized if ch.isalnum() or ch == "_").strip("_")
    return normalized or f"source_{stable_hash(name, 12)}"


def list_runs(limit: int = 20) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM runs ORDER BY generated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [row_to_run(row) for row in rows]


def get_run(run_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    return row_to_run(row) if row else None


def row_to_run(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["parameters"] = loads(data.pop("parameters_json"), {})
    data["errors"] = loads(data.pop("errors_json"), [])
    return data


def list_signals(
    limit: int = 50,
    offset: int = 0,
    query: str | None = None,
    source: str | None = None,
    source_group: str | None = None,
) -> dict[str, Any]:
    clauses: list[str] = []
    params: list[Any] = []
    if query:
        clauses.append("(lower(title) LIKE ? OR lower(content) LIKE ?)")
        value = f"%{query.lower()}%"
        params.extend([value, value])
    if source:
        clauses.append("source = ?")
        params.append(source)
    if source_group:
        clauses.append("source_group = ?")
        params.append(source_group)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    with connect() as conn:
        total_row = conn.execute(f"SELECT COUNT(*) AS count FROM signals {where}", tuple(params)).fetchone()
        rows = conn.execute(
            f"""
            SELECT * FROM signals
            {where}
            ORDER BY fetched_at DESC, published_at DESC
            LIMIT ? OFFSET ?
            """,
            tuple(params + [limit, offset]),
        ).fetchall()
    return {
        "items": [row_to_signal(row) for row in rows],
        "total": int(total_row["count"] if total_row else 0),
        "limit": limit,
        "offset": offset,
    }


def get_signal(signal_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM signals WHERE id = ?", (signal_id,)).fetchone()
    return row_to_signal(row) if row else None


def list_opportunity_signals(opportunity_id: str) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT s.*, os.relation_type, os.confidence
            FROM opportunity_signals os
            JOIN signals s ON s.id = os.signal_id
            WHERE os.opportunity_id = ?
            ORDER BY os.confidence DESC, s.fetched_at DESC
            """,
            (opportunity_id,),
        ).fetchall()
    return [row_to_signal(row) for row in rows]


def row_to_signal(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    raw = loads(data.pop("raw_json"), {})
    data["raw"] = raw if isinstance(raw, dict) else {}
    return data


def list_sources(include_disabled: bool = True) -> list[dict[str, Any]]:
    query = "SELECT * FROM sources"
    params: tuple[Any, ...] = ()
    if not include_disabled:
        query += " WHERE enabled = 1"
    query += " ORDER BY source_pack, name"
    with connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [row_to_source(row) for row in rows]


def list_enabled_sources(source_pack: str | None = None) -> list[dict[str, Any]]:
    params: list[Any] = []
    query = "SELECT * FROM sources WHERE enabled = 1"
    if source_pack and source_pack != "default":
        query += " AND source_pack IN ('default', ?)"
        params.append(source_pack)
    query += " ORDER BY source_pack, name"
    with connect() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()
    return [row_to_source(row) for row in rows]


def get_source(source_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
    return row_to_source(row) if row else None


def upsert_source(payload: dict[str, Any]) -> dict[str, Any]:
    timestamp = now_iso()
    source_id = payload.get("id") or source_id_for(payload.get("name") or payload.get("url") or timestamp)
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO sources (
                id, name, type, url, enabled, source_pack, config_json,
                last_status, last_error, last_fetched_at, last_item_count,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'unknown', '', '', 0, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                type = excluded.type,
                url = excluded.url,
                enabled = excluded.enabled,
                source_pack = excluded.source_pack,
                config_json = excluded.config_json,
                updated_at = excluded.updated_at
            """,
            (
                source_id,
                payload.get("name") or source_id,
                payload.get("type") or "rss",
                payload.get("url") or "",
                1 if payload.get("enabled", True) else 0,
                payload.get("source_pack") or "default",
                dumps(payload.get("config", {})),
                timestamp,
                timestamp,
            ),
        )
        conn.commit()
    source = get_source(source_id)
    if not source:
        raise RuntimeError("Failed to upsert source")
    return source


def set_source_enabled(source_id: str, enabled: bool) -> dict[str, Any] | None:
    with connect() as conn:
        conn.execute(
            "UPDATE sources SET enabled = ?, updated_at = ? WHERE id = ?",
            (1 if enabled else 0, now_iso(), source_id),
        )
        conn.commit()
    return get_source(source_id)


def row_to_source(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["enabled"] = bool(data["enabled"])
    data["config"] = loads(data.pop("config_json"), {})
    return data


def create_search_job(parameters: dict[str, Any], status: str = "pending") -> dict[str, Any]:
    from demand_pipeline import OPPORTUNITY_TYPES, stable_hash

    timestamp = now_iso()
    mode = parameters.get("opportunity_type") or parameters.get("mode") or "micro_saas"
    if mode not in OPPORTUNITY_TYPES:
        mode = "micro_saas"
    scoring_profile = OPPORTUNITY_TYPES[mode]["scoring_profile"]
    seed = dumps({"ts": timestamp, "parameters": parameters})
    job_id = f"job_{stable_hash(seed, 20)}"
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO search_jobs (
                id, query, mode, source_pack, scoring_profile, ai_depth,
                run_id, result_counts_json, parameters_json, status,
                created_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, '', '{}', ?, ?, ?, '')
            """,
            (
                job_id,
                parameters.get("query") or "",
                mode,
                parameters.get("source_pack") or "default",
                scoring_profile,
                parameters.get("ai_depth") or "none",
                dumps(parameters),
                status,
                timestamp,
            ),
        )
        conn.commit()
    job = get_search_job(job_id)
    if not job:
        raise RuntimeError("Failed to create search job")
    return job


def complete_search_job(job_id: str, result: dict[str, Any]) -> dict[str, Any] | None:
    metadata = result.get("metadata", {})
    with connect() as conn:
        conn.execute(
            """
            UPDATE search_jobs
            SET status = 'completed',
                run_id = ?,
                result_counts_json = ?,
                completed_at = ?
            WHERE id = ?
            """,
            (
                metadata.get("run_id") or "",
                dumps(result.get("counts", {})),
                now_iso(),
                job_id,
            ),
        )
        conn.commit()
    return get_search_job(job_id)


def fail_search_job(job_id: str, message: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT parameters_json FROM search_jobs WHERE id = ?", (job_id,)).fetchone()
        parameters = loads(row["parameters_json"], {}) if row else {}
        parameters["error"] = message
        conn.execute(
            """
            UPDATE search_jobs
            SET status = 'failed',
                parameters_json = ?,
                completed_at = ?
            WHERE id = ?
            """,
            (dumps(parameters), now_iso(), job_id),
        )
        conn.commit()
    return get_search_job(job_id)


def list_search_jobs(limit: int = 20) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM search_jobs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [row_to_search_job(row) for row in rows]


def get_search_job(job_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM search_jobs WHERE id = ?", (job_id,)).fetchone()
    return row_to_search_job(row) if row else None


def row_to_search_job(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["parameters"] = loads(data.pop("parameters_json"), {})
    data["result_counts"] = loads(data.pop("result_counts_json", "{}"), {})
    return data


def create_ai_job(
    opportunity_id: str,
    report_type: str = "feasibility",
    force: bool = False,
    parameters: dict[str, Any] | None = None,
    input_hash: str | None = None,
) -> dict[str, Any]:
    from demand_pipeline import stable_hash

    timestamp = now_iso()
    seed = dumps(
        {
            "ts": timestamp,
            "opportunity_id": opportunity_id,
            "report_type": report_type,
            "force": force,
            "input_hash": input_hash or "",
        }
    )
    job_id = f"aij_{stable_hash(seed, 20)}"
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO ai_jobs (
                id, opportunity_id, report_type, status, force, input_hash,
                report_id, error, parameters_json, created_at, started_at, completed_at
            ) VALUES (?, ?, ?, 'pending', ?, ?, '', '', ?, ?, '', '')
            """,
            (
                job_id,
                opportunity_id,
                report_type,
                1 if force else 0,
                input_hash or "",
                dumps(parameters or {}),
                timestamp,
            ),
        )
        conn.commit()
    job = get_ai_job(job_id)
    if not job:
        raise RuntimeError("Failed to create AI job")
    return job


def mark_ai_job_running(job_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        conn.execute(
            "UPDATE ai_jobs SET status = 'running', started_at = ? WHERE id = ?",
            (now_iso(), job_id),
        )
        conn.commit()
    return get_ai_job(job_id)


def complete_ai_job(job_id: str, report: dict[str, Any]) -> dict[str, Any] | None:
    with connect() as conn:
        conn.execute(
            """
            UPDATE ai_jobs
            SET status = 'completed',
                input_hash = ?,
                report_id = ?,
                error = '',
                completed_at = ?
            WHERE id = ?
            """,
            (
                report.get("input_hash") or "",
                report.get("id") or "",
                now_iso(),
                job_id,
            ),
        )
        conn.commit()
    return get_ai_job(job_id)


def fail_ai_job(job_id: str, message: str) -> dict[str, Any] | None:
    with connect() as conn:
        conn.execute(
            """
            UPDATE ai_jobs
            SET status = 'failed',
                error = ?,
                completed_at = ?
            WHERE id = ?
            """,
            (message, now_iso(), job_id),
        )
        conn.commit()
    return get_ai_job(job_id)


def get_ai_job(job_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM ai_jobs WHERE id = ?", (job_id,)).fetchone()
    return row_to_ai_job(row) if row else None


def list_ai_jobs(limit: int = 20, opportunity_id: str | None = None) -> list[dict[str, Any]]:
    params: list[Any] = []
    query = "SELECT * FROM ai_jobs"
    if opportunity_id:
        query += " WHERE opportunity_id = ?"
        params.append(opportunity_id)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()
    return [row_to_ai_job(row) for row in rows]


def row_to_ai_job(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["force"] = bool(data["force"])
    data["parameters"] = loads(data.pop("parameters_json"), {})
    return data


def get_opportunity(opportunity_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT latest_json FROM opportunities WHERE id = ?",
            (opportunity_id,),
        ).fetchone()
    if not row:
        return None
    return loads(row["latest_json"], None)


def get_opportunity_record(opportunity_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM opportunities WHERE id = ?",
            (opportunity_id,),
        ).fetchone()
    return row_to_opportunity(row) if row else None


def list_opportunities(
    limit: int = 50,
    offset: int = 0,
    rating: str | None = None,
    query: str | None = None,
    source_group: str | None = None,
) -> dict[str, Any]:
    clauses: list[str] = []
    params: list[Any] = []
    if rating:
        clauses.append("lower(rating) LIKE ?")
        params.append(f"%{rating.lower()}%")
    if query:
        clauses.append("(lower(title) LIKE ? OR lower(canonical_summary) LIKE ?)")
        value = f"%{query.lower()}%"
        params.extend([value, value])
    if source_group:
        clauses.append("source_group = ?")
        params.append(source_group)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    with connect() as conn:
        total_row = conn.execute(f"SELECT COUNT(*) AS count FROM opportunities {where}", tuple(params)).fetchone()
        rows = conn.execute(
            f"""
            SELECT * FROM opportunities
            {where}
            ORDER BY total_score DESC, last_seen_at DESC
            LIMIT ? OFFSET ?
            """,
            tuple(params + [limit, offset]),
        ).fetchall()
    return {
        "items": [row_to_opportunity(row) for row in rows],
        "total": int(total_row["count"] if total_row else 0),
        "limit": limit,
        "offset": offset,
    }


def row_to_opportunity(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    latest = loads(data.pop("latest_json"), {})
    if isinstance(latest, dict):
        latest.update(
            {
                "first_seen_at": data["first_seen_at"],
                "last_seen_at": data["last_seen_at"],
                "seen_count": data["seen_count"],
                "status": data["status"],
            }
        )
        return latest
    return data


def get_cached_ai_report(opportunity_id: str, report_type: str, input_hash: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM ai_reports
            WHERE opportunity_id = ? AND report_type = ? AND input_hash = ?
            ORDER BY generated_at DESC, created_at DESC
            LIMIT 1
            """,
            (opportunity_id, report_type, input_hash),
        ).fetchone()
    if not row:
        return None
    return row_to_ai_report(row)


def get_latest_ai_report(opportunity_id: str, report_type: str = "feasibility") -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM ai_reports
            WHERE opportunity_id = ? AND report_type = ?
            ORDER BY generated_at DESC, created_at DESC
            LIMIT 1
            """,
            (opportunity_id, report_type),
        ).fetchone()
    if not row:
        return None
    return row_to_ai_report(row)


def get_ai_report(report_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM ai_reports WHERE id = ?", (report_id,)).fetchone()
    return row_to_ai_report(row) if row else None


def list_ai_reports(
    limit: int = 20,
    opportunity_id: str | None = None,
    report_type: str | None = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if opportunity_id:
        clauses.append("opportunity_id = ?")
        params.append(opportunity_id)
    if report_type:
        clauses.append("report_type = ?")
        params.append(report_type)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM ai_reports
            {where}
            ORDER BY generated_at DESC, created_at DESC
            LIMIT ?
            """,
            tuple(params + [limit]),
        ).fetchall()
    return [row_to_ai_report(row) for row in rows]


def save_ai_report(report: dict[str, Any]) -> dict[str, Any]:
    created_at = report.get("created_at") or now_iso()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO ai_reports (
                id, opportunity_id, report_type, status, report_json,
                report_markdown, provider, model, prompt_version,
                report_template_version, scoring_profile_version, input_hash,
                token_usage, cost_estimate, created_at, generated_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(opportunity_id, report_type, input_hash) DO UPDATE SET
                status = excluded.status,
                report_json = excluded.report_json,
                report_markdown = excluded.report_markdown,
                provider = excluded.provider,
                model = excluded.model,
                prompt_version = excluded.prompt_version,
                report_template_version = excluded.report_template_version,
                scoring_profile_version = excluded.scoring_profile_version,
                token_usage = excluded.token_usage,
                cost_estimate = excluded.cost_estimate,
                generated_at = excluded.generated_at,
                expires_at = excluded.expires_at
            """,
            (
                report["id"],
                report["opportunity_id"],
                report.get("report_type") or "feasibility",
                report.get("status") or "completed",
                dumps(report.get("report_json", {})),
                report.get("report_markdown") or "",
                report.get("provider") or "",
                report.get("model") or "",
                report.get("prompt_version") or "",
                report.get("report_template_version") or "",
                report.get("scoring_profile_version") or "",
                report["input_hash"],
                int(report.get("token_usage") or 0),
                float(report.get("cost_estimate") or 0),
                created_at,
                report.get("generated_at") or created_at,
                report.get("expires_at") or "",
            ),
        )
        conn.commit()
    cached = get_cached_ai_report(report["opportunity_id"], report.get("report_type") or "feasibility", report["input_hash"])
    return cached or report


def row_to_ai_report(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["report_json"] = loads(data.get("report_json"), {})
    return data
