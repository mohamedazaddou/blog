# Signal — blog tech (articles rédigés + sources citées)

Blog statique : vous écrivez des articles en Markdown, le site est généré en HTML.
Aucun CMS, aucune base de données, aucun framework — le dépôt git **est** le site.

## Écrire un article

```bash
python3 scripts/new.py "Titre de l'article"     # crée content/articles/<slug>.md
```

Le fichier contient un en-tête à remplir :

```
---
title: Titre de l'article
date: 2026-11-01
summary: Une phrase de résumé (affichée dans la liste et en chapeau).
tags: agents, architecture
sources:
- Nom de la source — titre du document | https://url-de-la-source
---

Le corps en Markdown : ## titres, **gras**, listes, > citations, `code`.
Les appels [1], [2] dans le texte renvoient à la liste `sources`, affichée en bas de page.
```

Puis :

```bash
python3 scripts/build.py        # régénère dist/
bash scripts/serve.sh           # http://192.168.1.131:8080
```

## Structure

```
config.json            titre du site, tagline, auteur, URL de base
content/articles/*.md  les articles (un fichier = un article)
templates/index.html   page d'accueil (liste)
templates/row.html     une ligne de la liste
templates/article.html page article
assets/style.css       tout le design (variables de couleur en tête de fichier)
scripts/build.py       Markdown + gabarits → dist/
scripts/new.py         squelette de nouvel article
scripts/serve.sh       serveur local sur le réseau
dist/                  site généré (index.html, articles/, feed.xml)
```

## Généré automatiquement

- accueil trié par date, temps de lecture calculé depuis le nombre de mots ;
- une page par article : chapeau, tags, corps, bloc **Sources** numéroté ;
- `feed.xml` (RSS) pour que le blog soit lui-même une source ;
- la build échoue si un gabarit contient un marqueur `{{...}}` non résolu.

## Personnaliser

- **Nom / tagline / auteur** : `config.json`.
- **Design** : `assets/style.css`, variables `--bg`, `--accent`, `--measure` (largeur de lecture).
- **Structure HTML** : `templates/*.html`, simples marqueurs `{{...}}`.
- **URL publique** : `config.json` → `site.base_url` (utilisée par le flux RSS).

## Publier

`dist/` est un site statique complet : Cloudflare Pages (gratuit, bande passante illimitée),
Netlify, GitHub Pages, ou n'importe quel serveur — il suffit de copier `dist/`.
Avec Cloudflare Pages : build command `python3 scripts/build.py`, output directory `dist`.
