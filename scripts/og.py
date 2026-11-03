#!/usr/bin/env python3
"""Génère les images de partage (Open Graph) 1200×630 pour chaque article.

À lancer après ajout/modification d'un article :
    python3 scripts/og.py

Sortie : assets/og/<slug>.png + assets/og/index.png, committés dans le dépôt
(sinon GitHub Pages n'a rien à servir). Le build ne dépend pas de ce script.
"""
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build  # noqa: E402  (réutilise le parseur d'en-tête)

OUT = ROOT / "assets" / "og"
FONT_DIR = Path(os.environ.get("OG_FONT_DIR", Path.home() / ".hermes/tools/fonts"))
CHROME = Path(os.environ.get("CHROME_BIN", Path.home() / ".hermes/tools/chromium-1208/chrome-linux64/chrome"))
DEPS = Path.home() / ".hermes/tools/chromium-deps"

W, H = 1200, 630
WIN_H = H + 80  # chrome headless perd ~80 px de hauteur de fenêtre


def e(s):
    return html.escape(s or "", quote=True)


def figure_of(body: str):
    m = re.search(r'\.\./img/([^"\s]+)', body)
    if not m:
        return None
    p = ROOT / "assets" / "img" / m.group(1)
    return p if p.exists() else None


def card(meta: dict) -> str:
    title = meta["title"]
    summary = meta["summary"]
    title_class = "xlong" if len(title) > 78 else ("long" if len(title) > 52 else "")
    summary_class = "short" if len(summary) < 95 else ""
    fig = figure_of(meta.get("body", ""))
    if fig:
        figure = f'<img src="file://{fig}" alt="">'
    else:
        figure = ('<svg class="mark" viewBox="0 0 120 120" fill="none">'
                  '<circle cx="60" cy="60" r="46" stroke="#1d2127" stroke-width="1"/>'
                  '<circle cx="60" cy="60" r="26" stroke="#2c5a49" stroke-width="1"/>'
                  '<circle cx="60" cy="60" r="6" fill="#6ef2bd"/></svg>')

    tags = meta.get("tags") or []
    tag_html = "".join(
        f'<span class="sep"></span><span class="tag">{e(t)}</span>' for t in tags[:2]
    )
    return build.render(
        "og",
        site_title=e(build.SITE["title"]),
        host=e(re.sub(r"^https?://", "", build.SITE["base_url"]).rstrip("/")),
        title=e(title),
        title_class=title_class,
        summary=e(summary),
        summary_class=summary_class,
        date=e(build.fmt_date(meta["date"])) if meta.get("date") else "",
        read_time=(f'<span class="sep"></span><span>{meta["minutes"]} min de lecture</span>'
                   if meta.get("minutes") else ""),
        tag_html=tag_html,
        figure=figure,
        font_dir=f"file://{FONT_DIR}",
    )


def shoot(page_html: str, out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="og-"))
    page = tmp / "card.html"
    page.write_text(page_html, encoding="utf-8")
    env = dict(os.environ)
    env["LD_LIBRARY_PATH"] = str(DEPS / "lib")
    env["FONTCONFIG_FILE"] = str(DEPS / "fonts.conf")
    raw = tmp / "raw.png"
    subprocess.run(
        [str(CHROME), "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
         "--force-device-scale-factor=1", f"--window-size={W},{WIN_H}",
         f"--screenshot={raw}", f"file://{page}"],
        check=True, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    from PIL import Image
    im = Image.open(raw).convert("RGB")
    if im.size != (W, WIN_H):
        im = im.resize((W, WIN_H))
    im.crop((0, 0, W, H)).save(out, "PNG", optimize=True)
    shutil.rmtree(tmp, ignore_errors=True)


def main():
    if not CHROME.exists():
        sys.exit(f"Chromium introuvable : {CHROME}")
    articles = sorted((build.parse_article(p) for p in build.ARTICLES_DIR.glob("*.md")),
                      key=lambda a: a["date"], reverse=True)
    for a in articles:
        out = OUT / f"{a['slug']}.png"
        shoot(card(a), out)
        print(f"  · {out.relative_to(ROOT)}")
    # carte du site
    home = {
        "title": build.SITE["tagline"],
        "summary": "Agents, protocoles d'outils, retours d'expérience : des notes sourcées, pas de la veille.",
        "date": articles[0]["date"] if articles else None,
        "tags": [],
        "minutes": 0,
        "body": "",
    }
    h = dict(home)
    shoot(card(h), OUT / "index.png")
    print(f"  · {(OUT / 'index.png').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
