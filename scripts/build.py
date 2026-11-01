#!/usr/bin/env python3
"""Génère le site statique dans dist/ à partir de data/posts.json + templates/ + assets/."""
import html
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape as xesc

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
SITE = CONFIG["site"]
TEMPLATES = {p.stem: p.read_text(encoding="utf-8") for p in (ROOT / "templates").glob("*.html")}
POSTS = json.loads((ROOT / "data" / "posts.json").read_text(encoding="utf-8"))

FR_MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
             "août", "septembre", "octobre", "novembre", "décembre"]


def render(tpl: str, **kw) -> str:
    out = TEMPLATES[tpl]
    for k, v in kw.items():
        out = out.replace("{{" + k + "}}", str(v))
    return out


def fmt_date(iso: str) -> str:
    dt = datetime.fromisoformat(iso)
    return f"{dt.day} {FR_MONTHS[dt.month - 1]} {dt.year}"


def e(s: str) -> str:
    return html.escape(s or "", quote=True)


def card_html(p, **kw) -> str:
    tags = "".join(f'<span class="tag">{e(t)}</span>' for t in p["tags"][:3])
    return render(
        "card",
        url=kw.get("prefix", "p/") + p["id"] + ".html",
        title=e(p["title"]),
        summary=e(p["summary"]),
        source=e(p["source"]),
        date=fmt_date(p["date"]),
        tags=tags,
        lang=p["lang"],
        search=e((p["title"] + " " + p["summary"]).lower()),
        tag_list=e(",".join(p["tags"])),
        score=p.get("score", 0),
    )


def build_index():
    posts = POSTS
    cards = "\n".join(card_html(p) for p in posts)
    sources = sorted({p["source"] for p in posts})
    chips = '<button class="chip is-active" data-src="">Tout</button>' + "".join(
        f'<button class="chip" data-src="{e(s)}">{e(s)}</button>' for s in sources
    )
    topics = sorted({t for p in posts for t in p["tags"]})
    topic_chips = "".join(f'<button class="chip chip--tag" data-tag="{e(t)}">#{e(t)}</button>' for t in topics)
    html_out = render(
        "index",
        site_title=e(SITE["title"]),
        tagline=e(SITE["tagline"]),
        count=str(len(posts)),
        source_count=str(len(sources)),
        chips=chips,
        topic_chips=topic_chips,
        cards=cards,
        base_url=SITE["base_url"],
        author=e(SITE["author"]),
        year=str(datetime.now().year),
        updated=fmt_date(POSTS[0]["date"]) if POSTS else "",
    )
    (DIST / "index.html").write_text(html_out, encoding="utf-8")


def build_posts():
    outdir = DIST / "p"
    outdir.mkdir(parents=True, exist_ok=True)
    by_tag = {}
    for p in POSTS:
        for t in p["tags"]:
            by_tag.setdefault(t, []).append(p)

    for p in POSTS:
        related = []
        for t in p["tags"]:
            for cand in by_tag.get(t, []):
                if cand["id"] != p["id"] and cand not in related:
                    related.append(cand)
        related = related[:3]
        page = render(
            "post",
            title=e(p["title"]),
            summary=e(p["summary"]),
            source=e(p["source"]),
            date=fmt_date(p["date"]),
            link=e(p["link"]),
            tags="".join(f'<span class="tag">{e(t)}</span>' for t in p["tags"]),
            related="".join(f'<li><a href="{r["id"]}.html">{e(r["title"])}</a> <span>{e(r["source"])}</span></li>' for r in related),
            site_title=e(SITE["title"]),
            base_url=SITE["base_url"],
            author=e(SITE["author"]),
            year=str(datetime.now().year),
        )
        (outdir / (p["id"] + ".html")).write_text(page, encoding="utf-8")


def build_feed():
    items = []
    for p in POSTS[:40]:
        items.append(
            "<item>"
            f"<title>{xesc(p['title'])}</title>"
            f"<link>{xesc(SITE['base_url'].rstrip('/') + '/p/' + p['id'] + '.html')}</link>"
            f"<guid isPermaLink=\"false\">{p['id']}</guid>"
            f"<pubDate>{datetime.fromisoformat(p['date']).strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>"
            f"<description>{xesc(p['summary'])}</description>"
            f"<category>{xesc(p['source'])}</category>"
            "</item>"
        )
    feed = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
            f"<title>{xesc(SITE['title'])}</title>"
            f"<link>{xesc(SITE['base_url'])}</link>"
            f"<description>{xesc(SITE['tagline'])}</description>"
            f"<language>fr</language>{''.join(items)}</channel></rss>")
    (DIST / "feed.xml").write_text(feed, encoding="utf-8")


def main():
    DIST.mkdir(exist_ok=True)
    shutil.copy(ROOT / "assets" / "style.css", DIST / "style.css")
    shutil.copy(ROOT / "assets" / "app.js", DIST / "app.js")
    build_index()
    build_posts()
    build_feed()
    print(f"dist/ généré — {len(POSTS)} articles, {len(list((DIST / 'p').glob('*.html')))} pages")


if __name__ == "__main__":
    main()
