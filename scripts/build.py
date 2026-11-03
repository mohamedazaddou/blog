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
BASE = SITE["base_url"].rstrip("/")
OG_DIR = ROOT / "assets" / "og"
TWITTER = (SITE.get("links") or {}).get("twitter", "").strip().lstrip("@")


def og_url(slug: str) -> str:
    """Image de partage : celle de l'article si elle existe, sinon celle du site."""
    name = f"{slug}.png" if (OG_DIR / f"{slug}.png").exists() else "index.png"
    return f"{BASE}/og/{name}"


def head_block(title, description, canonical, image, kind="website", extra="", jsonld=None,
               og_title=None):
    """Toutes les balises SEO de la page, en un seul endroit."""
    ogt = og_title or title
    ld = ""
    if jsonld is not None:
        blob = json.dumps(jsonld, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        ld = f'\n<script type="application/ld+json">{blob}</script>'
    tw = ""
    if TWITTER:
        tw = (f'\n<meta name="twitter:site" content="@{e(TWITTER)}">'
              f'\n<meta name="twitter:creator" content="@{e(TWITTER)}">')
    return (
        f"<title>{e(title)}</title>\n"
        f'<meta name="description" content="{e(description)}">\n'
        f'<link rel="canonical" href="{e(canonical)}">\n'
        f'<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">\n'
        f'<meta name="author" content="{e(SITE["author"])}">\n'
        f'<meta property="og:type" content="{kind}">\n'
        f'<meta property="og:site_name" content="{e(SITE["title"])}">\n'
        f'<meta property="og:locale" content="fr_FR">\n'
        f'<meta property="og:title" content="{e(ogt)}">\n'
        f'<meta property="og:description" content="{e(description)}">\n'
        f'<meta property="og:url" content="{e(canonical)}">\n'
        f'<meta property="og:image" content="{e(image)}">\n'
        '<meta property="og:image:type" content="image/png">\n'
        '<meta property="og:image:width" content="1200">\n'
        '<meta property="og:image:height" content="630">\n'
        f'<meta property="og:image:alt" content="{e(ogt)}">\n'
        '<meta name="theme-color" content="#08090b">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        f'<meta name="twitter:title" content="{e(ogt)}">\n'
        f'<meta name="twitter:description" content="{e(description)}">\n'
        f'<meta name="twitter:image" content="{e(image)}">'
        f'{tw}{extra}'
        f'\n<link rel="alternate" type="application/rss+xml" title="{e(SITE["title"])}" href="{BASE}/feed.xml">'
        f"{ld}"
    )


def linkedin_nav(prefix: str = "") -> str:
    if not LINKEDIN:
        return ""
    return (f'<a class="ext" href="{e(LINKEDIN)}" target="_blank" rel="noopener">'
            f'LinkedIn &#8599;</a>')


def domain(url):
    return re.sub(r"^https?://(www\.)?", "", url).split("/")[0]


def md_to_html(text):
    return markdown.Markdown(extensions=["extra", "sane_lists", "smarty", "toc"]).convert(text)


def article_jsonld(a, canonical, image):
    post = {
        "@type": "BlogPosting",
        "headline": a["title"],
        "description": a["summary"],
        "inLanguage": "fr-FR",
        "datePublished": a["date"],
        "dateModified": a["date"],
        "author": {"@type": "Person", "name": SITE["author"],
                   **({"url": LINKEDIN} if LINKEDIN else {})},
        "publisher": {"@type": "Organization", "name": SITE["title"], "url": BASE + "/"},
        "image": [image],
        "url": canonical,
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "isPartOf": {"@type": "Blog", "name": SITE["title"], "url": BASE + "/"},
        **({"keywords": ", ".join(a["tags"])} if a["tags"] else {}),
    }
    crumbs = {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Articles", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": a["title"], "item": canonical},
        ],
    }
    return {"@context": "https://schema.org", "@graph": [post, crumbs]}


def build_article(a):
    content = md_to_html(a["body"])
    canonical = f"{BASE}/articles/{a['slug']}.html"
    image = og_url(a["slug"])
    head = head_block(
        f"{a['title']} — {SITE['title']}", a["summary"], canonical, image, kind="article",
        extra=(
            f'\n<meta property="article:published_time" content="{a["date"]}">'
            f'\n<meta property="article:author" content="{e(SITE["author"])}">'
            + "".join(f'\n<meta property="article:tag" content="{e(t)}">' for t in a["tags"])
        ),
        jsonld=article_jsonld(a, canonical, image), og_title=a["title"],
    )
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
        head=head,
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
    canonical = BASE + "/"
    image = og_url("index")
    jsonld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebSite", "name": SITE["title"], "url": canonical,
             "description": SITE["tagline"], "inLanguage": "fr-FR"},
            {"@type": "Blog", "name": SITE["title"], "url": canonical,
             "description": SITE["tagline"], "inLanguage": "fr-FR",
             "author": {"@type": "Person", "name": SITE["author"]},
             "blogPost": [
                 {"@type": "BlogPosting", "headline": a["title"],
                  "url": f"{BASE}/articles/{a['slug']}.html", "datePublished": a["date"]}
                 for a in articles
             ]},
        ],
    }
    head = head_block(
        f"{SITE['title']} — {SITE['tagline']}",
        f"{SITE['tagline']} — {len(articles)} articles par {SITE['author']}.",
        canonical, image, kind="website", jsonld=jsonld, og_title=SITE["title"],
    )
    page = render(
        "index",
        head=head,
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
        canonical = f"{BASE}/{path.stem}.html"
        head = head_block(
            f"{meta.get('title', path.stem)} — {SITE['title']}",
            meta.get("summary", ""), canonical, og_url("index"), kind="website",
            og_title=meta.get("title", path.stem),
            jsonld={
                "@context": "https://schema.org",
                "@type": "AboutPage",
                "name": meta.get("title", path.stem),
                "url": canonical,
                "inLanguage": "fr-FR",
                "isPartOf": {"@type": "WebSite", "name": SITE["title"], "url": BASE + "/"},
            },
        )
        page = render(
            "page",
            head=head,
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


def build_sitemap(articles, pages):
    entries = [(BASE + "/", articles[0]["date"] if articles else None, "1.0")]
    entries += [(f"{BASE}/articles/{a['slug']}.html", a["date"], "0.9") for a in articles]
    entries += [(f"{BASE}/{name}.html", None, "0.5") for name in pages]
    body = ""
    for loc, lastmod, prio in entries:
        body += f"<url><loc>{xesc(loc)}</loc>"
        if lastmod:
            body += f"<lastmod>{lastmod}</lastmod>"
        body += f"<priority>{prio}</priority></url>"
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + body + "</urlset>")
    (DIST / "sitemap.xml").write_text(xml, encoding="utf-8")


def build_robots():
    (DIST / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\n"
        f"Sitemap: {BASE}/sitemap.xml\n", encoding="utf-8")


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    for asset in ("style.css", "favicon.svg", "apple-touch-icon.png"):
        src = ROOT / "assets" / asset
        if src.exists():
            shutil.copy(src, DIST / asset)
    for folder in ("img", "og"):
        src = ROOT / "assets" / folder
        if src.exists():
            shutil.copytree(src, DIST / folder)

    articles = sorted((parse_article(p) for p in ARTICLES_DIR.glob("*.md")),
                      key=lambda a: a["date"], reverse=True)
    for a in articles:
        build_article(a)
    build_index(articles)
    pages = build_pages()
    build_feed(articles)
    build_sitemap(articles, pages)
    build_robots()
    print(f"dist/ — {len(articles)} article(s) publié(s), {len(pages)} page(s)")
    for a in articles:
        print(f"  · {a['slug']} ({a['words']} mots, {len(a['sources'])} sources)")


if __name__ == "__main__":
    main()
