#!/usr/bin/env python3
"""Récupère les flux RSS/Atom listés dans config.json et met à jour data/posts.json.

Stdlib uniquement, aucune dépendance à installer.
Supporte RSS 2.0, RSS 1.0 (RDF), Atom, gzip.
"""
import gzip
import hashlib
import html
import io
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zlib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
POSTS_FILE = ROOT / "data" / "posts.json"
UA = "Mozilla/5.0 (compatible; SignalBlog/1.0; +https://example.pages.dev)"


# ---------- helpers XML (agnostiques du namespace) ----------
def ln(el) -> str:
    return el.tag.rsplit("}", 1)[-1].lower()


def child(el, *names):
    for c in el:
        if ln(c) in names:
            return c
    return None


def text_of(el, *names) -> str:
    c = child(el, *names)
    if c is None:
        return ""
    return "".join(c.itertext()).strip()


def link_of(el) -> str:
    alt = ""
    for c in el:
        if ln(c) != "link":
            continue
        href = c.get("href")
        rel = c.get("rel", "alternate")
        if href and rel == "alternate" and not alt:
            alt = href.strip()
        elif href and not alt:
            alt = href.strip()
        elif not href and (c.text or "").strip() and not alt:
            alt = c.text.strip()
    if alt:
        return alt
    for g in ("guid", "id"):
        v = text_of(el, g)
        if v.startswith("http"):
            return v
    return ""


def clean(text: str, limit: int = 260) -> str:
    if not text:
        return ""
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0].rstrip(",;:.") + "…"
    return text


def to_dt(value: str) -> datetime:
    value = (value or "").strip()
    dt = None
    if value:
        try:
            dt = parsedate_to_datetime(value)
        except Exception:
            try:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except Exception:
                dt = None
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_feed(xml_bytes: bytes):
    root = ET.fromstring(xml_bytes)
    items = []
    for el in root.iter():
        if ln(el) not in ("item", "entry"):
            continue
        items.append({
            "title": text_of(el, "title"),
            "link": link_of(el),
            "summary": text_of(el, "description", "summary", "content", "encoded"),
            "date": text_of(el, "pubdate", "published", "updated", "date", "created"),
            "tags": [c.get("term") or (c.text or "") for c in el if ln(c) == "category"],
        })
    return items


def download(src):
    req = urllib.request.Request(src["url"], headers={
        "User-Agent": UA,
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        "Accept-Encoding": "gzip, deflate",
    })
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read()
            enc = (r.headers.get("Content-Encoding") or "").lower()
        if raw[:2] == b"\x1f\x8b" or "gzip" in enc:
            raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
        elif "deflate" in enc:
            raw = zlib.decompress(raw, -zlib.MAX_WBITS)
        return src, parse_feed(raw), None
    except Exception as exc:  # noqa: BLE001
        return src, [], f"{type(exc).__name__}: {exc}"


def make_id(link: str) -> str:
    return hashlib.sha1(link.encode("utf-8")).hexdigest()[:12]


def topic_tags(text: str):
    low = text.lower()
    return [topic for topic, words in CONFIG["keywords"].items() if any(w in low for w in words)]


def score_of(text: str) -> int:
    return len(topic_tags(text))


def main():
    cfg = CONFIG["fetch"]
    existing = {}
    if POSTS_FILE.exists():
        for p in json.loads(POSTS_FILE.read_text(encoding="utf-8")):
            existing[p["id"]] = p

    added, errors = 0, []
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(download, CONFIG["sources"]))

    for src, items, err in results:
        if err:
            errors.append(f"{src['name']}: {err}")
            continue
        if not items:
            errors.append(f"{src['name']}: flux vide")
            continue
        for it in items[: cfg["max_items_per_source"]]:
            title = html.unescape(re.sub(r"\s+", " ", it["title"])).strip()
            if not title or not it["link"]:
                continue
            pid = make_id(it["link"])
            if pid in existing:
                continue
            summary = clean(it["summary"])
            tags = topic_tags(f"{title} {summary}")
            existing[pid] = {
                "id": pid,
                "title": title,
                "link": it["link"],
                "summary": summary,
                "source": src["name"],
                "lang": src.get("lang", "en"),
                "date": to_dt(it["date"]).isoformat(),
                "tags": tags,
                "score": len(tags),
            }
            added += 1

    posts = sorted(existing.values(), key=lambda p: p["date"], reverse=True)[: cfg["max_posts_total"]]
    POSTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    POSTS_FILE.write_text(json.dumps(posts, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{added} nouveaux articles — {len(posts)} au total")
    for e in errors:
        print("  ! " + e, file=sys.stderr)


if __name__ == "__main__":
    main()
