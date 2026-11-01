#!/usr/bin/env python3
"""Crée un squelette d'article : python3 scripts/new.py "Titre de l'article" """
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "content" / "articles"


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return re.sub(r"-{2,}", "-", text)[:70] or "article"


def main():
    if len(sys.argv) < 2:
        raise SystemExit('Usage : python3 scripts/new.py "Titre de l\'article"')
    title = " ".join(sys.argv[1:]).strip()
    slug = slugify(title)
    path = DIR / f"{slug}.md"
    if path.exists():
        raise SystemExit(f"Existe déjà : {path}")

    path.write_text(f"""---
title: {title}
date: {date.today().isoformat()}
summary: Une phrase de résumé, affichée dans la liste et en chapeau de l'article.
tags: a-completer
sources:
- Nom de la source — titre du document | https://exemple.fr/page
---

Introduction : de quoi parle l'article et pourquoi il vaut la peine d'être lu.

## Premier point

Le corps du texte. Un appel de source s'écrit [1] et renvoie à la liste `sources` de l'en-tête.

## Deuxième point

- une idée ;
- une autre.

> Une citation ou une idée à isoler.

## Ce que je retiens

La conclusion, en deux ou trois phrases.
""", encoding="utf-8")
    print(f"créé : {path}")
    print(f"puis : python3 scripts/build.py")


if __name__ == "__main__":
    main()
