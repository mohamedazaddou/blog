#!/usr/bin/env python3
"""Blog statique : content/articles/*.md + templates/ + assets/ → dist/.

Un article = un fichier Markdown avec un en-tête (title, date, summary, tags, sources).
Aucune base de données, aucun CMS : le dépôt EST le site.
"""
import html
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape as xesc

import markdown

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
ARTICLES_DIR = ROOT / "content" / "articles"
PAGES_DIR = ROOT / "content" / "pages"
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
SITE = CONFIG["site"]
TEMPLATES = {p.stem: p.read_text(encoding="utf-8") for p in (ROOT / "templates").glob("*.html")}

FR_MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
             "août", "septembre", "octobre", "novembre", "décembre"]


def render(tpl, **kw):
    out = TEMPLATES[tpl]
    for k, v in kw.items():
        out = out.replace("{{" + k + "}}", str(v))
    leftover = re.findall(r"\{\{\w+\}\}", out)
    if leftover:
        raise SystemExit(f"Placeholder non résolu dans {tpl}: {leftover}")
    return out


def e(s):
    return html.escape(s or "", quote=True)


def fmt_date(iso):
    dt = datetime.fromisoformat(iso)
    return f"{dt.day} {FR_MONTHS[dt.month - 1]} {dt.year}"


def parse_article(path: Path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
    if not m:
        raise SystemExit(f"En-tête manquant (---) dans {path.name}")
    head, body = m.group(1), m.group(2)

    meta = {"tags": [], "sources": []}
    current = None
    for line in head.splitlines():
        if line.startswith("- "):
            val = line[2:].strip()
            if current == "sources":
                title, _, url = val.partition("|")
                meta["sources"].append({"title": title.strip(), "url": url.strip()})
            elif current == "tags":
                meta["tags"].append(val)
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            current = key.strip()
            val = val.strip()
            if current in ("sources", "tags") and not val:
                continue
            meta[current] = val

    if isinstance(meta.get("tags"), str):
        meta["tags"] = [t.strip() for t in meta["tags"].split(",") if t.strip()]

    words = len(re.findall(r"\w+", body))
    meta.update({
        "slug": path.stem,
        "body": body,
        "minutes": max(1, round(words / 220)),
        "words": words,
    })
    return meta


LINKEDIN = (SITE.get("links") or {}).get("linkedin", "").strip()


def linkedin_nav(prefix: str = "") -> str:
    if not LINKEDIN:
        return ""
    return (f'<a class="ext" href="{e(LINKEDIN)}" target="_blank" rel="noopener">'
            f'LinkedIn &#8599;</a>')


def domain(url):
    return re.sub(r"^https?://(www\.)?", "", url).split("/")[0]


def md_to_html(text):
    return markdown.Markdown(extensions=["extra", "sane_lists", "smarty", "toc"]).convert(text)


def build_article(a):
    content = md_to_html(a["body"])
    sources = "\n".join(
        f'<li><a href="{e(s["url"])}" target="_blank" rel="noopener">{e(s["title"])}</a>'
        f'<span class="src-domain">{e(domain(s["url"]))}</span></li>'
        for s in a["sources"]
    )
    sources_block = (
        f'<section class="sources"><h2>Sources</h2><ol>{sources}</ol></section>'
        if a["sources"] else ""
    )
    page = render(
        "article",
        title=e(a["title"]),
        summary=e(a["summary"]),
        date=fmt_date(a["date"]),
        iso_date=a["date"],
        minutes=a["minutes"],
        tags="".join(f'<span class="tag">{e(t)}</span>' for t in a["tags"]),
        content=content,
        sources=sources_block,
        site_title=e(SITE["title"]),
        author=e(SITE["author"]),
        year=str(datetime.now().year),
        linkedin=linkedin_nav(),
        about_url="../about.html",
    )
    out = DIST / "articles" / (a["slug"] + ".html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")


def build_index(articles):
    rows = [
        render(
            "row",
            url=f"articles/{a['slug']}.html",
            title=e(a["title"]),
            summary=e(a["summary"]),
            date=fmt_date(a["date"]),
            iso_date=a["date"],
            minutes=a["minutes"],
            tags=" · ".join(a["tags"]),
        )
        for a in articles
    ]
    page = render(
        "index",
        site_title=e(SITE["title"]),
        tagline=e(SITE["tagline"]),
        articles="\n".join(rows),
        count=str(len(articles)),
        author=e(SITE["author"]),
        year=str(datetime.now().year),
        linkedin=linkedin_nav(),
        about_url=("about.html" if (PAGES_DIR / "about.md").exists() else ""),
    )
    (DIST / "index.html").write_text(page, encoding="utf-8")


def build_pages():
    built = []
    for path in sorted(PAGES_DIR.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
        if not m:
            raise SystemExit(f"En-tête manquant (---) dans pages/{path.name}")
        head, body = m.group(1), m.group(2)
        meta = {}
        for line in head.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        page = render(
            "page",
            title=e(meta.get("title", path.stem)),
            summary=e(meta.get("summary", "")),
            content=md_to_html(body),
            site_title=e(SITE["title"]),
            author=e(SITE["author"]),
            year=str(datetime.now().year),
            linkedin=linkedin_nav(),
        )
        (DIST / (path.stem + ".html")).write_text(page, encoding="utf-8")
        built.append(path.stem)
    return built


def build_feed(articles):
    items = "".join(
        "<item>"
        f"<title>{xesc(a['title'])}</title>"
        f"<link>{xesc(SITE['base_url'].rstrip('/') + '/articles/' + a['slug'] + '.html')}</link>"
        f'<guid isPermaLink="false">{a["slug"]}</guid>'
        f"<pubDate>{datetime.fromisoformat(a['date']).strftime('%a, %d %b %Y 08:00:00 +0000')}</pubDate>"
        f"<description>{xesc(a['summary'])}</description>"
        "</item>"
        for a in articles
    )
    feed = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
            f"<title>{xesc(SITE['title'])}</title><link>{xesc(SITE['base_url'])}</link>"
            f"<description>{xesc(SITE['tagline'])}</description><language>fr</language>"
            f"{items}</channel></rss>")
    (DIST / "feed.xml").write_text(feed, encoding="utf-8")


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copy(ROOT / "assets" / "style.css", DIST / "style.css")

    articles = sorted((parse_article(p) for p in ARTICLES_DIR.glob("*.md")),
                      key=lambda a: a["date"], reverse=True)
    for a in articles:
        build_article(a)
    build_index(articles)
    pages = build_pages()
    build_feed(articles)
    print(f"dist/ — {len(articles)} article(s) publié(s), {len(pages)} page(s)")
    for a in articles:
        print(f"  · {a['slug']} ({a['words']} mots, {len(a['sources'])} sources)")


if __name__ == "__main__":
    main()
