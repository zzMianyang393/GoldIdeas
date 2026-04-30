from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import socket
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

import feedparser


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
REPORTS_DIR = DATA_DIR / "reports"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "GoldIdeasDemandPipeline/4.1"
)

DEFAULT_LIMIT = 25
SUBREDDITS = [
    "indiehackers",
    "microsaas",
    "SaaS",
    "EntrepreneurRideAlong",
    "SideProject",
    "solopreneur",
    "freelance",
    "webdev",
    "nocode",
    "smallbusiness",
    "apps",
    "webhosting",
]

RSS_FEEDS = [
    {
        "name": "Hacker News",
        "url": "https://hnrss.org/newest?points=10",
        "source_type": "rss",
    },
    {
        "name": "Indie Hackers",
        "url": "https://www.indiehackers.com/feed",
        "source_type": "rss",
    },
    {
        "name": "Product Hunt",
        "url": "https://www.producthunt.com/feed",
        "source_type": "rss",
    },
]

HN_QUERIES = ["saas", "micro saas", "side project", "startup idea", "developer tool"]

OPPORTUNITY_TYPES = {
    "micro_saas": {
        "label": "Micro SaaS",
        "scoring_profile": "micro_saas_v4_1",
        "default_queries": HN_QUERIES,
    },
    "developer_tools": {
        "label": "Developer Tools",
        "scoring_profile": "developer_tools_v0",
        "default_queries": ["developer tool", "api pain", "cli tool", "documentation", "dev workflow"],
    },
    "ecommerce_tools": {
        "label": "E-commerce Tools",
        "scoring_profile": "ecommerce_tools_v0",
        "default_queries": ["shopify app", "ecommerce returns", "amazon seller", "conversion rate", "inventory"],
    },
}

GIANT_KEYWORDS = [
    "google",
    "microsoft",
    "amazon",
    "apple",
    "meta",
    "facebook",
    "salesforce",
    "hubspot",
    "shopify",
    "slack",
    "zoom",
    "aws",
    "openai",
    "anthropic",
    "deepseek",
    "google ai",
    "zendesk",
    "intercom",
    "atlassian",
    "notion",
    "figma",
]

PLATFORM_KEYWORDS = [
    "facebook api",
    "google api",
    "tiktok api",
    "instagram api",
    "youtube api",
    "linkedin api",
    "reddit api",
    "pci compliance",
    "hipaa compliance",
    "sox compliance",
]

TECH_KEYWORDS = [
    "blockchain",
    "defi",
    "web3",
    "smart contract",
    "cryptocurrency",
    "machine learning model",
    "train a model",
    "computer vision",
    "self-hosted llm",
    "fine-tune",
    "medical device",
    "iot device",
    "robotics",
    "hardware",
    "firmware",
]

MOAT_KEYWORDS = [
    "open source alternative",
    "free alternative",
    "oss",
    "github",
    "gitlab",
    "wordpress plugin",
    "chrome extension",
    "bookmarklet",
    "greasemonkey",
    "tampermonkey",
    "todo list",
    "note taking app",
    "calculator",
    "password manager",
    "clipboard manager",
]

FAKE_KEYWORDS = [
    "what do you think",
    "brainstorm",
    "idea validation",
    "general discussion",
    "opinion",
    "poll",
    "just wondering",
    "curious",
    "what if",
]
FAKE_PATTERNS = [
    re.compile(r"^(what|how|why|when|where)\s", re.I),
    re.compile(r"^(does anyone|anyone know|can someone)", re.I),
]

OPPORTUNITY_PHRASES = [
    "alternative",
    "instead of",
    "switch from",
    "replace",
    "moving from",
    "fed up with",
    "done with",
    "too expensive",
    "frustrated",
    "hate",
]

REQUEST_PHRASES = ["looking for", "anyone know", "recommend", "can't find", "need"]
PAIN_SIGNALS = ["frustrated", "hate", "waste of time", "pain", "sucks", "terrible"]
PAY_SIGNALS = ["pay for", "willing to", "willing to pay", "take my money", "would buy"]

CATEGORIES = {
    "pain_point": {
        "keywords": [
            "frustrated",
            "annoyed",
            "hate",
            "wish there was",
            "problem",
            "issue",
            "struggle",
            "difficult",
            "pain",
            "broken",
            "terrible",
            "waste of time",
            "sucks",
            "wish",
            "need",
            "looking for",
            "can't find",
            "finally found",
            "solution",
            "fix",
        ],
        "description": "用户明确表达痛点",
    },
    "willingness_to_pay": {
        "keywords": [
            "pay for",
            "willing to pay",
            "shut up and take my money",
            "take my money",
            "how much",
            "pricing",
            "subscription",
            "worth it",
            "budget",
            "cost",
            "expensive",
            "cheap",
            "discount",
            "lifetime deal",
            "ltd",
        ],
        "description": "用户表达付费意愿",
    },
    "idea_request": {
        "keywords": [
            "idea",
            "suggest",
            "recommend",
            "what should i build",
            "what to build",
            "saas idea",
            "micro saas",
            "side project idea",
            "business idea",
            "niche",
        ],
        "description": "用户在寻求创意方向",
    },
    "feedback_request": {
        "keywords": [
            "feedback",
            "review",
            "critique",
            "thoughts",
            "what do you think",
            "rate",
            "evaluate",
            "landing page",
            "mvp",
            "beta",
            "early access",
        ],
        "description": "用户在请求反馈",
    },
    "competitor_complaint": {
        "keywords": [
            "alternative to",
            "switch from",
            "instead of",
            "competitor",
            "replace",
            "migration",
            "moving from",
            "fed up with",
            "done with",
            "leaving",
        ],
        "description": "用户对竞品不满",
    },
}

REDLINE_NAMES = {
    1: "巨头压制",
    2: "平台合规",
    3: "技术泥潭",
    4: "护城河缺失",
    5: "假性需求",
}


@dataclass
class FetchResult:
    posts: list[dict[str, Any]]
    errors: list[dict[str, str]]


def ensure_dirs() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def clean_html(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def normalize_text(value: str | None) -> str:
    value = clean_html(value or "").lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def canonical_url(value: str | None) -> str:
    if not value:
        return ""
    parsed = urlsplit(value.strip())
    if not parsed.scheme or not parsed.netloc:
        return value.strip()
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/"), "", ""))


def stable_hash(value: str, length: int = 16) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def enrich_post_identity(post: dict[str, Any]) -> dict[str, Any]:
    url = canonical_url(post.get("url"))
    title = normalize_text(post.get("title"))
    content = clean_html(post.get("content") or "")
    content_hash = stable_hash(f"{title}\n{content}", 24)
    source_group = post.get("source_group") or "unknown"
    if url:
        signal_seed = f"{source_group}|{url}"
        opportunity_seed = signal_seed
    else:
        signal_seed = f"{source_group}|{title}|{content_hash}"
        opportunity_seed = signal_seed
    post["canonical_url"] = url
    post["content_hash"] = content_hash
    post["signal_id"] = f"sig_{stable_hash(signal_seed, 24)}"
    post["fingerprint"] = stable_hash(opportunity_seed, 24)
    post["opportunity_id"] = f"opp_{post['fingerprint']}"
    return post


def parse_datetime(value: str | None) -> str:
    if not value:
        return ""
    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, IndexError):
        return value


def fetch_bytes(url: str, timeout: int = 10) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as response:
        return response.read()


def entry_to_post(entry: Any, source: str, source_group: str, source_url: str) -> dict[str, Any]:
    title = clean_html(getattr(entry, "title", "Untitled"))
    content = clean_html(
        getattr(entry, "summary", "")
        or getattr(entry, "description", "")
        or getattr(entry, "content", "")
    )
    url = getattr(entry, "link", "") or source_url
    comments = 0
    comments_url = ""
    if source_group == "reddit":
        comments_url = url
    return {
        "id": getattr(entry, "id", "") or url or f"{source}:{title}",
        "title": title,
        "content": content,
        "url": url,
        "comments_url": comments_url,
        "comments": comments,
        "source": source,
        "source_group": source_group,
        "published": parse_datetime(getattr(entry, "published", "") or getattr(entry, "updated", "")),
    }


def fetch_rss_feed(name: str, url: str, source_group: str, limit: int) -> FetchResult:
    try:
        payload = fetch_bytes(url)
    except socket.timeout:
        return FetchResult([], [{"source": name, "error": "RSS Timeout"}])
    except Exception as exc:
        return FetchResult([], [{"source": name, "error": f"RSS Error: {exc}"}])

    parsed = feedparser.parse(payload)
    if getattr(parsed, "bozo", False) and not getattr(parsed, "entries", []):
        return FetchResult([], [{"source": name, "error": "RSS Parse Error"}])

    posts = [entry_to_post(entry, name, source_group, url) for entry in parsed.entries[:limit]]
    return FetchResult(posts, [])


def fetch_reddit(subreddits: list[str], limit: int) -> FetchResult:
    posts: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for subreddit in subreddits:
        url = f"https://www.reddit.com/r/{subreddit}/.rss"
        result = fetch_rss_feed(f"r/{subreddit}", url, "reddit", limit)
        posts.extend(result.posts)
        errors.extend(result.errors)
    return FetchResult(posts, errors)


def fetch_extra_rss(limit: int) -> FetchResult:
    posts: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for feed in RSS_FEEDS:
        result = fetch_rss_feed(feed["name"], feed["url"], feed["source_type"], limit)
        posts.extend(result.posts)
        errors.extend(result.errors)
    return FetchResult(posts, errors)


def fetch_hn_algolia(limit: int, queries: list[str] | None = None) -> FetchResult:
    posts: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    seen: set[str] = set()
    per_query = max(3, min(limit, 10))
    selected_queries = queries or HN_QUERIES

    for query in selected_queries:
        url = "https://hn.algolia.com/api/v1/search_by_date?" + urlencode(
            {"query": query, "tags": "story", "hitsPerPage": per_query}
        )
        try:
            payload = fetch_bytes(url)
            data = json.loads(payload.decode("utf-8"))
        except socket.timeout:
            errors.append({"source": f"Hacker News search:{query}", "error": "JSON Timeout"})
            continue
        except Exception as exc:
            errors.append({"source": f"Hacker News search:{query}", "error": f"JSON Error: {exc}"})
            continue

        for hit in data.get("hits", []):
            object_id = str(hit.get("objectID") or hit.get("story_id") or "")
            if not object_id or object_id in seen:
                continue
            seen.add(object_id)
            title = clean_html(hit.get("title") or hit.get("story_title") or "Untitled")
            hn_url = f"https://news.ycombinator.com/item?id={object_id}"
            posts.append(
                {
                    "id": f"hn:{object_id}",
                    "title": title,
                    "content": clean_html(hit.get("story_text") or ""),
                    "url": hit.get("url") or hn_url,
                    "comments_url": hn_url,
                    "comments": int(hit.get("num_comments") or 0),
                    "source": "Hacker News Search",
                    "source_group": "hackernews",
                    "published": hit.get("created_at") or "",
                }
            )
    return FetchResult(posts[: limit * len(selected_queries)], errors)


def fetch_all_sources(subreddits: list[str], limit: int, queries: list[str] | None = None) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    results = [fetch_reddit(subreddits, limit), fetch_extra_rss(limit), fetch_hn_algolia(limit, queries=queries)]
    posts: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    seen: set[str] = set()

    for result in results:
        errors.extend(result.errors)
        for post in result.posts:
            post = enrich_post_identity(post)
            key = post.get("url") or post.get("id") or post.get("title")
            if key in seen:
                continue
            seen.add(key)
            posts.append(post)
    return posts, errors


def fetch_configured_sources(limit: int, queries: list[str] | None = None, source_pack: str = "default") -> tuple[list[dict[str, Any]], list[dict[str, str]], int]:
    try:
        from storage import list_enabled_sources

        sources = list_enabled_sources(source_pack=source_pack)
    except Exception:
        posts, errors = fetch_all_sources(SUBREDDITS, limit, queries=queries)
        return posts, errors, len(SUBREDDITS) + len(RSS_FEEDS) + 1

    posts: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    seen: set[str] = set()
    hn_search_done = False

    for source in sources:
        source_type = source.get("type")
        if source_type == "json_search":
            if hn_search_done:
                continue
            result = fetch_hn_algolia(limit, queries=queries)
            hn_search_done = True
        elif source_type == "reddit_rss":
            result = fetch_rss_feed(source["name"], source["url"], "reddit", limit)
        elif source_type in {"rss", "auto"} and source.get("url"):
            result = fetch_rss_feed(source["name"], source["url"], source_type, limit)
        else:
            continue

        errors.extend(result.errors)
        for post in result.posts:
            post = enrich_post_identity(post)
            key = post.get("url") or post.get("id") or post.get("title")
            if key in seen:
                continue
            seen.add(key)
            posts.append(post)

    return posts, errors, len(sources)


def post_matches_search(post: dict[str, Any], query: str | None, include_keywords: list[str] | None = None, exclude_keywords: list[str] | None = None) -> bool:
    text = text_of(post)
    if query and normalize_text(query) not in normalize_text(text):
        query_terms = [term for term in normalize_text(query).split(" ") if len(term) > 2]
        if query_terms and not any(term in normalize_text(text) for term in query_terms):
            return False
    if include_keywords:
        normalized = normalize_text(text)
        if not any(normalize_text(keyword) in normalized for keyword in include_keywords if keyword):
            return False
    if exclude_keywords:
        normalized = normalize_text(text)
        if any(normalize_text(keyword) in normalized for keyword in exclude_keywords if keyword):
            return False
    return True


def text_of(post: dict[str, Any]) -> str:
    return f"{post.get('title', '')} {post.get('content', '')}".lower()


def contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def classify_post(post: dict[str, Any]) -> dict[str, Any]:
    text = text_of(post)
    best_name = "pain_point"
    best_hits = 0
    for name, spec in CATEGORIES.items():
        hits = sum(1 for keyword in spec["keywords"] if keyword in text)
        if hits > best_hits:
            best_name = name
            best_hits = hits
    return {
        "name": best_name,
        "description": CATEGORIES[best_name]["description"],
        "hits": best_hits,
    }


def check_redlines(post: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[int, str]]:
    text = text_of(post)
    redlines: list[dict[str, Any]] = []
    checks = {index: "pass" for index in REDLINE_NAMES}

    if contains_any(text, GIANT_KEYWORDS):
        if contains_any(text, OPPORTUNITY_PHRASES):
            checks[1] = "pass: 巨头替代/抱怨语境"
        else:
            checks[1] = "fail"
            redlines.append({"id": 1, "name": REDLINE_NAMES[1], "reason": "讨论巨头生态或巨头产品本身，个人产品空间受压。"})

    if contains_any(text, PLATFORM_KEYWORDS) and contains_any(text, ["compliance", "certification", "license", "认证", "合规"]):
        checks[2] = "fail"
        redlines.append({"id": 2, "name": REDLINE_NAMES[2], "reason": "涉及官方 API、认证或合规成本。"})

    if contains_any(text, TECH_KEYWORDS):
        checks[3] = "fail"
        redlines.append({"id": 3, "name": REDLINE_NAMES[3], "reason": "技术复杂度明显超出个人快速落地范围。"})

    if contains_any(text, MOAT_KEYWORDS):
        if contains_any(text, REQUEST_PHRASES):
            checks[4] = "pass: 用户正在寻找更好替代"
        else:
            checks[4] = "fail"
            redlines.append({"id": 4, "name": REDLINE_NAMES[4], "reason": "已有免费/开源/通用替代，护城河不足。"})

    fake_hit = contains_any(text, FAKE_KEYWORDS) or any(pattern.search(text) for pattern in FAKE_PATTERNS)
    if fake_hit:
        if contains_any(text, PAIN_SIGNALS) or contains_any(text, PAY_SIGNALS):
            checks[5] = "pass: 仍包含痛点或付费信号"
        else:
            checks[5] = "fail"
            redlines.append({"id": 5, "name": REDLINE_NAMES[5], "reason": "更像泛讨论/想法征集，缺少明确痛点或付费信号。"})

    return redlines, checks


def score_with_reasons(post: dict[str, Any], opportunity_type: str = "micro_saas") -> tuple[float, dict[str, float], dict[str, str]]:
    text = text_of(post)
    comments = int(post.get("comments") or 0)

    pain = 5.0
    pain_reasons = []
    strong_pain = [
        "frustrated",
        "annoyed",
        "hate",
        "terrible",
        "sucks",
        "waste of time",
        "pain",
        "nightmare",
        "broken",
        "desperately",
        "urgent",
        "critical",
        "deadline",
    ]
    weak_pain = ["wish", "need", "looking for", "problem", "issue", "struggle", "difficult", "hard to", "can't find"]
    pay_keywords = ["pay for", "willing to pay", "take my money", "worth it", "budget", "pricing"]
    for keyword in strong_pain:
        if keyword in text:
            pain += 0.5
            pain_reasons.append(f"强痛点: {keyword}")
    for keyword in weak_pain:
        if keyword in text:
            pain += 0.3
            pain_reasons.append(f"弱痛点: {keyword}")
    for keyword in pay_keywords:
        if keyword in text:
            pain += 0.5
            pain_reasons.append(f"付费信号: {keyword}")
    if comments > 50:
        pain += 1.0
        pain_reasons.append("讨论热度高")
    elif comments > 20:
        pain += 0.5
        pain_reasons.append("讨论热度中等")
    elif comments > 10:
        pain += 0.3
        pain_reasons.append("有一定讨论")

    dev = 5.0
    dev_reasons = []
    solo_friendly = [
        "solo",
        "one person",
        "indie",
        "side project",
        "weekend",
        "prototype",
        "mvp",
        "no-code",
        "low-code",
        "browser extension",
        "chrome extension",
        "api",
        "saas",
        "landing page",
        "dashboard",
        "cron job",
        "script",
        "automation",
        "tool",
        "utility",
        "cli",
        "web app",
        "static site",
        "shopify app",
        "wordpress plugin",
        "notion template",
    ]
    team_needed = ["team", "hiring", "co-founder", "partnership", "enterprise", "b2b sales", "compliance", "hardware", "manufacturing", "inventory"]
    simple_tech = ["python", "javascript", "html", "css", "react", "next.js", "node", "sqlite", "postgres", "firebase", "supabase", "vercel", "netlify", "stripe"]
    for keyword in solo_friendly:
        if keyword in text:
            dev += 0.4
            dev_reasons.append(f"个人可做: {keyword}")
    for keyword in team_needed:
        if keyword in text:
            dev -= 0.8
            dev_reasons.append(f"团队/重运营风险: {keyword}")
    for keyword in simple_tech:
        if keyword in text:
            dev += 0.3
            dev_reasons.append(f"简单技术栈: {keyword}")

    survival = 7.0
    survival_reasons = []
    risk_keywords = ["api change", "policy update", "terms of service", "tos", "compliance", "regulation", "legal", "ban", "suspend", "deplatform", "crackdown", "apple", "google play", "app store", "steam"]
    stable_keywords = ["recurring", "subscription", "monthly", "annual", "long term", "sustainable", "passive income", "retention", "sticky", "essential"]
    for keyword in risk_keywords:
        if keyword in text:
            survival -= 0.5
            survival_reasons.append(f"外部依赖风险: {keyword}")
    for keyword in stable_keywords:
        if keyword in text:
            survival += 0.3
            survival_reasons.append(f"稳定性信号: {keyword}")

    growth = 5.0
    growth_reasons = []
    easy_growth = ["reddit", "twitter", "hacker news", "product hunt", "indie hackers", "community", "word of mouth", "organic", "seo", "blog", "content marketing", "free tier", "freemium", "viral", "referral", "open source", "github stars"]
    hard_growth = ["ads", "advertising", "paid marketing", "ppc", "cold email", "cold outreach", "sales team", "enterprise sales", "account executive"]
    for keyword in easy_growth:
        if keyword in text or keyword in post.get("source", "").lower():
            growth += 0.4
            growth_reasons.append(f"低成本获客: {keyword}")
    for keyword in hard_growth:
        if keyword in text:
            growth -= 0.5
            growth_reasons.append(f"高成本获客: {keyword}")

    money = 5.0
    money_reasons = []
    clear_monetization = ["subscription", "monthly", "annual", "pricing", "pay", "revenue", "mrr", "arr", "profit", "lifetime deal", "one-time", "per seat", "usage based", "tier", "plan", "upgrade", "premium"]
    vague_monetization = ["free", "open source", "community", "donation", "sponsor", "patreon"]
    for keyword in clear_monetization:
        if keyword in text:
            money += 0.4
            money_reasons.append(f"明确变现: {keyword}")
    for keyword in PAY_SIGNALS + ["how much", "worth paying", "not free"]:
        if keyword in text:
            money += 0.5
            money_reasons.append(f"付费意愿: {keyword}")
    for keyword in vague_monetization:
        if keyword in text:
            money -= 0.3
            money_reasons.append(f"变现模糊: {keyword}")

    scores = {
        "痛点强度": round(max(min(pain, 10.0), 0.0), 1),
        "开发性价比": round(max(min(dev, 10.0), 0.0), 1),
        "生存稳定性": round(max(min(survival, 10.0), 0.0), 1),
        "获客阻力": round(max(min(growth, 10.0), 0.0), 1),
        "变现确定性": round(max(min(money, 10.0), 0.0), 1),
    }
    apply_profile_adjustments(scores, reasons_map := {
        "痛点强度": pain_reasons,
        "开发性价比": dev_reasons,
        "生存稳定性": survival_reasons,
        "获客阻力": growth_reasons,
        "变现确定性": money_reasons,
    }, text, opportunity_type)
    total = round(sum(scores.values()) / len(scores), 1)
    reasons = {
        "痛点强度": "；".join(reasons_map["痛点强度"][:4]) or "基线评分，未发现强痛点词",
        "开发性价比": "；".join(reasons_map["开发性价比"][:4]) or "常规 Web/SaaS 可行性基线",
        "生存稳定性": "；".join(reasons_map["生存稳定性"][:4]) or "无明显政策或平台风险",
        "获客阻力": "；".join(reasons_map["获客阻力"][:4]) or "缺少明确低成本获客信号",
        "变现确定性": "；".join(reasons_map["变现确定性"][:4]) or "付费路径尚需验证",
    }
    return total, scores, reasons


def apply_profile_adjustments(scores: dict[str, float], reasons: dict[str, list[str]], text: str, opportunity_type: str) -> None:
    if opportunity_type == "developer_tools":
        if contains_any(text, ["api", "cli", "sdk", "documentation", "developer", "github", "workflow"]):
            scores["开发性价比"] = min(scores["开发性价比"] + 0.6, 10.0)
            scores["获客阻力"] = min(scores["获客阻力"] + 0.5, 10.0)
            reasons["开发性价比"].append("Developer Tools profile: 开发者工具形态清晰")
            reasons["获客阻力"].append("Developer Tools profile: HN/GitHub/社区获客更自然")
        if contains_any(text, ["open source", "github", "free", "oss"]):
            scores["变现确定性"] = max(scores["变现确定性"] - 0.4, 0.0)
            reasons["变现确定性"].append("Developer Tools profile: 开源/免费替代压低付费确定性")
        if contains_any(text, ["maintenance", "breaking change", "api change", "dependency"]):
            scores["生存稳定性"] = max(scores["生存稳定性"] - 0.5, 0.0)
            reasons["生存稳定性"].append("Developer Tools profile: 长期维护或依赖风险")
    elif opportunity_type == "ecommerce_tools":
        if contains_any(text, ["shopify", "amazon seller", "ecommerce", "returns", "inventory", "conversion", "orders"]):
            scores["痛点强度"] = min(scores["痛点强度"] + 0.5, 10.0)
            scores["变现确定性"] = min(scores["变现确定性"] + 0.7, 10.0)
            reasons["痛点强度"].append("E-commerce profile: 直接关联商家运营痛点")
            reasons["变现确定性"].append("E-commerce profile: ROI/收入关联增强付费确定性")
        if contains_any(text, ["shopify api", "amazon api", "tiktok shop", "payment", "refund", "tax"]):
            scores["生存稳定性"] = max(scores["生存稳定性"] - 0.6, 0.0)
            reasons["生存稳定性"].append("E-commerce profile: 平台/API/支付依赖风险")
        if contains_any(text, ["agency", "done for you", "manual service"]):
            scores["开发性价比"] = max(scores["开发性价比"] - 0.4, 0.0)
            reasons["开发性价比"].append("E-commerce profile: 服务交付倾向降低软件化效率")


def calc_rating(total_score: float, red_triggered: bool) -> str:
    if red_triggered:
        return "🔴 RED"
    if total_score >= 5.0:
        return "🟢 GREEN"
    if total_score >= 3.0:
        return "🟡 YELLOW"
    return "🔴 RED"


def summarize(post: dict[str, Any], limit: int = 220) -> str:
    text = clean_html(post.get("content") or post.get("title") or "")
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def analyze_post(post: dict[str, Any], opportunity_type: str = "micro_saas") -> dict[str, Any]:
    post = enrich_post_identity(dict(post))
    category = classify_post(post)
    redlines, checks = check_redlines(post)
    total, scores, reasons = score_with_reasons(post, opportunity_type=opportunity_type)
    rating = calc_rating(total, bool(redlines))
    return {
        **post,
        "category": category,
        "redlines": redlines,
        "redline_checks": checks,
        "scores": scores,
        "score_reasons": reasons,
        "total_score": total,
        "rating": rating,
        "content_summary": summarize(post),
        "key_insight": make_key_insight(post, category, scores),
        "action_items": make_action_items(post, rating),
    }


def make_key_insight(post: dict[str, Any], category: dict[str, Any], scores: dict[str, float]) -> str:
    strongest = max(scores, key=scores.get)
    return f"{category['description']}；当前最强维度是{strongest}（{scores[strongest]}/10）。"


def make_action_items(post: dict[str, Any], rating: str) -> str:
    if rating == "🟢 GREEN":
        return "整理 5 个同类讨论，做一个无代码落地页和付费等候名单验证。"
    if rating == "🟡 YELLOW":
        return "先补充竞品、价格与用户访谈证据，再决定是否进入 MVP。"
    return "暂不投入开发，只保留关键词用于后续趋势观察。"


def analyze_posts(posts: list[dict[str, Any]], rating_filter: str | None = None, quick: bool = False, opportunity_type: str = "micro_saas") -> list[dict[str, Any]]:
    opportunities = [analyze_post(post, opportunity_type=opportunity_type) for post in posts]
    opportunities.sort(key=lambda item: (item["rating"] != "🟢 GREEN", -item["total_score"], item["title"]))
    if rating_filter:
        wanted = rating_filter.lower()
        opportunities = [item for item in opportunities if wanted in item["rating"].lower()]
    if quick:
        opportunities = opportunities[:20]
    return opportunities


def rating_counts(opportunities: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "green": sum(1 for item in opportunities if item["rating"] == "🟢 GREEN"),
        "yellow": sum(1 for item in opportunities if item["rating"] == "🟡 YELLOW"),
        "red": sum(1 for item in opportunities if item["rating"] == "🔴 RED"),
    }


def redline_stats(opportunities: list[dict[str, Any]]) -> dict[str, int]:
    stats = {str(index): 0 for index in REDLINE_NAMES}
    for item in opportunities:
        for redline in item["redlines"]:
            stats[str(redline["id"])] += 1
    return stats


def render_opportunity(item: dict[str, Any], rank: int, detailed: bool = True) -> str:
    source_label = item["source"]
    checks = item["redline_checks"]
    lines = [
        f"### {rank}. {item['title']}",
        f"- **来源**: {source_label} | **评分**: {item['total_score']}/10",
        f"- **链接**: {item['url']}",
        f"- **内容摘要**: {item['content_summary'] or '无摘要'}",
        "",
        "**生存校验**:",
    ]
    for index, name in REDLINE_NAMES.items():
        lines.append(f"- [ ] {name}: {checks.get(index, 'pass')}")
    if detailed:
        lines.extend(["", "**五维详情**:", "| 维度 | 分数 | 依据 |", "|------|------|------|"])
        for dim, score in item["scores"].items():
            lines.append(f"| {dim} | {score}/10 | {item['score_reasons'][dim]} |")
        lines.extend(["", f"**核心洞察**: {item['key_insight']}", f"**落地建议**: {item['action_items']}"])
    lines.append("")
    return "\n".join(lines)


def render_report(opportunities: list[dict[str, Any]], metadata: dict[str, Any]) -> str:
    counts = rating_counts(opportunities)
    stats = redline_stats(opportunities)
    total = max(len(opportunities), 1)
    green = [item for item in opportunities if item["rating"] == "🟢 GREEN"]
    yellow = [item for item in opportunities if item["rating"] == "🟡 YELLOW"]
    red = [item for item in opportunities if item["rating"] == "🔴 RED"]
    date = metadata["generated_at"][:10]

    lines = [
        "# 需求管道 V4.1 — 分析报告",
        "",
        f"**日期**: {date}",
        f"**扫描**: {metadata['source_count']}个来源 × 最多{metadata['limit']}条 = {metadata['raw_count']}条信号",
        f"**分类出**: {len(opportunities)}个机会",
        f"**🟢 GREEN**: {counts['green']}个 | **🟡 YELLOW**: {counts['yellow']}个 | **🔴 RED**: {counts['red']}个",
        "",
        "---",
        "",
        "## 🟢 GREEN 机会（可直接开始）",
        "",
        "> 以下机会通过所有红线检查，且评分 ≥ 5.0",
        "",
    ]
    lines.extend(render_opportunity(item, index) for index, item in enumerate(green[:20], 1))
    if not green:
        lines.append("本次没有发现 GREEN 机会。")

    lines.extend(["", "---", "", "## 🟡 YELLOW 机会（需深度验证）", "", "> 以下机会未触发红线，但评分在 3.0-5.0 之间", ""])
    lines.extend(render_opportunity(item, index, detailed=False) for index, item in enumerate(yellow[:20], 1))
    if not yellow:
        lines.append("本次没有发现 YELLOW 机会。")

    lines.extend(["", "---", "", "## 🔴 RED 机会（一票否决）", "", "> 以下机会触发了红线，不建议继续", "", "| # | 标题 | 触发红线 | 原因 |", "|---|------|---------|------|"])
    for index, item in enumerate(red[:50], 1):
        redline = item["redlines"][0] if item["redlines"] else {"id": 0, "name": "低分", "reason": "总分过低"}
        lines.append(f"| {index} | {item['title']} | 红线{redline['id']}: {redline['name']} | {redline['reason']} |")

    lines.extend(["", "---", "", "## 📊 红线触发统计", "", "| 红线 | 触发数 | 占比 |", "|------|--------|------|"])
    for index, name in REDLINE_NAMES.items():
        count = stats[str(index)]
        lines.append(f"| 红线{index}: {name} | {count} | {round(count / total * 100, 1)}% |")

    lines.extend(["", "## 💡 关键发现", ""])
    lines.extend(make_findings(opportunities, metadata))
    if metadata.get("errors"):
        lines.extend(["", "## ⚠️ 采集异常", ""])
        for error in metadata["errors"][:10]:
            lines.append(f"- {error['source']}: {error['error']}")
    return "\n".join(lines).strip() + "\n"


def make_findings(opportunities: list[dict[str, Any]], metadata: dict[str, Any]) -> list[str]:
    counts = rating_counts(opportunities)
    top_sources: dict[str, int] = {}
    for item in opportunities:
        top_sources[item["source"]] = top_sources.get(item["source"], 0) + 1
    source_text = ", ".join(f"{name}({count})" for name, count in sorted(top_sources.items(), key=lambda pair: pair[1], reverse=True)[:3])
    return [
        f"- 本次已接入多来源采集，不再只依赖 Reddit；实际返回来源 Top3: {source_text or '暂无'}。",
        f"- 可继续验证的非红线机会共 {counts['green'] + counts['yellow']} 个，其中 GREEN {counts['green']} 个。",
        f"- 采集异常 {len(metadata.get('errors', []))} 个；异常来源会记录在报告中，不影响其他来源产出。",
    ]


def save_json(path: Path, payload: Any) -> None:
    ensure_dirs()
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run_pipeline(
    limit: int = DEFAULT_LIMIT,
    subreddits: list[str] | None = None,
    rating_filter: str | None = None,
    quick: bool = False,
    fetch: bool = True,
    sample_posts: list[dict[str, Any]] | None = None,
    query: str | None = None,
    opportunity_type: str = "micro_saas",
    include_keywords: list[str] | None = None,
    exclude_keywords: list[str] | None = None,
    source_pack: str = "default",
    ai_depth: str = "none",
    search_job_id: str | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    ensure_dirs()
    selected_subreddits = subreddits or SUBREDDITS
    mode = opportunity_type if opportunity_type in OPPORTUNITY_TYPES else "micro_saas"
    mode_spec = OPPORTUNITY_TYPES[mode]
    hn_queries = [query] if query else mode_spec["default_queries"]
    if fetch:
        posts, errors, source_count = fetch_configured_sources(limit, queries=hn_queries, source_pack=source_pack if source_pack != "default" else mode)
    else:
        posts, errors = [enrich_post_identity(dict(post)) for post in (sample_posts or [])], []
        source_count = len(selected_subreddits) + len(RSS_FEEDS) + 1

    posts = [
        enrich_post_identity(post)
        for post in posts
        if post_matches_search(post, query, include_keywords=include_keywords, exclude_keywords=exclude_keywords)
    ]

    opportunities = analyze_posts(posts, rating_filter=rating_filter, quick=quick, opportunity_type=mode)
    generated_at = datetime.now(timezone.utc).isoformat()
    run_id = f"run_{stable_hash(generated_at + json.dumps({'query': query, 'mode': mode}, sort_keys=True), 20)}"
    metadata = {
        "run_id": run_id,
        "generated_at": generated_at,
        "limit": limit,
        "source_count": source_count,
        "subreddits": selected_subreddits,
        "raw_count": len(posts),
        "errors": errors,
        "quick": quick,
        "rating_filter": rating_filter,
        "query": query,
        "opportunity_type": mode,
        "opportunity_type_label": mode_spec["label"],
        "source_pack": source_pack,
        "ai_depth": ai_depth,
        "search_job_id": search_job_id,
        "scoring_profile": mode_spec["scoring_profile"],
        "parameters": {
            "limit": limit,
            "subreddits": selected_subreddits,
            "rating_filter": rating_filter,
            "quick": quick,
            "query": query,
            "opportunity_type": mode,
            "include_keywords": include_keywords or [],
            "exclude_keywords": exclude_keywords or [],
            "source_pack": source_pack,
            "ai_depth": ai_depth,
            "search_job_id": search_job_id,
        },
    }
    report = render_report(opportunities, metadata)
    report_path = REPORTS_DIR / f"{metadata['generated_at'][:10]}.md"

    save_json(DATA_DIR / "raw_posts.json", {"metadata": metadata, "posts": posts})
    save_json(DATA_DIR / "opportunities.json", {"metadata": metadata, "opportunities": opportunities, "counts": rating_counts(opportunities)})
    report_path.write_text(report, encoding="utf-8")
    result = {
        "metadata": metadata,
        "posts": posts,
        "opportunities": opportunities,
        "counts": rating_counts(opportunities),
        "redline_stats": redline_stats(opportunities),
        "report": report,
        "report_path": str(report_path),
    }
    if persist:
        from storage import persist_pipeline_result

        persist_pipeline_result(result)
    return result


def load_latest() -> dict[str, Any] | None:
    path = DATA_DIR / "opportunities.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GoldIdeas Demand Pipeline V4.1")
    parser.add_argument("--quick", action="store_true", help="只输出 Top 20")
    parser.add_argument("--rating", choices=["green", "yellow", "red"], help="只显示特定评级")
    parser.add_argument("--subreddits", help="逗号分隔的 subreddit 列表")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="每个来源最多抓取条数")
    parser.add_argument("--query", help="自定义搜索关键词")
    parser.add_argument("--type", choices=sorted(OPPORTUNITY_TYPES), default="micro_saas", help="机会方向")
    return parser


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    subreddits = [item.strip() for item in args.subreddits.split(",") if item.strip()] if args.subreddits else None
    result = run_pipeline(
        limit=args.limit,
        subreddits=subreddits,
        rating_filter=args.rating,
        quick=args.quick,
        query=args.query,
        opportunity_type=args.type,
    )
    print(result["report"])
    print(f"\nReport saved: {result['report_path']}")


if __name__ == "__main__":
    main()
