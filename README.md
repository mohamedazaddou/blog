# Signal — blog agrégé IA / tech

Génération statique : aucun CMS, aucun compte à créer. Le design vit dans `assets/style.css`
et les gabarits dans `templates/` ; le contenu est produit automatiquement depuis les flux RSS
listés dans `config.json`.

## Utilisation

```bash
cd ~/blog-ia
python3 scripts/fetch.py     # récupère les nouveaux articles (data/posts.json)
python3 scripts/build.py     # régénère dist/ (site complet)
```

Ou les deux d'un coup :

```bash
bash scripts/run.sh
```

Prévisualisation locale :

```bash
cd dist && python3 -m http.server 8080   # http://localhost:8080
```

## Personnaliser

- **Sources** : `config.json` → `sources` (nom, url RSS, langue). N'importe quel flux RSS/Atom.
- **Mots-clés / tags** : `config.json` → `keywords`. Les articles reçoivent un tag quand le titre
  ou le résumé contient un des mots ; les puces de filtre du site sont générées automatiquement.
- **Volume** : `max_items_per_source` (12 par source) et `max_posts_total` (600 en base).
- **Design** : `assets/style.css` (variables de couleur en haut) et `templates/*.html`.
  Les gabarits sont des fichiers HTML avec des marqueurs `{{titre}}` — modifiables sans toucher au code.
- **Titre / auteur / URL** : `config.json` → `site`.

## Fichiers

```
config.json          réglages + sources
scripts/fetch.py     lecture des flux RSS → data/posts.json
scripts/build.py     data/posts.json + templates → dist/
templates/index.html accueil
templates/card.html  carte d'article
templates/post.html  page article
assets/style.css     design (tout le style est ici)
assets/app.js        recherche, filtres, pagination (côté navigateur)
data/posts.json      base des articles
dist/                site généré, prêt à publier
```

## Déploiement gratuit

Le dossier `dist/` est un site statique complet : il suffit de le publier.

**Cloudflare Pages** (recommandé, bande passante illimitée)
1. Pousser le dépôt sur GitHub.
2. Cloudflare Dashboard → Workers & Pages → Create → Pages → Connect to Git.
3. Build command : `python3 scripts/build.py` — Output directory : `dist`.
   (Ou build command vide si `dist/` est commité.)
4. Domaine perso : ajout gratuit du domaine, ou sous-domaine `xxx.pages.dev`.

Alternatives : Netlify, GitHub Pages, ou n'importe quel hébergement statique / serveur perso.

## Automatisation

`bash scripts/run.sh` fait fetch + build + commit/push si le dépôt git est configuré.
À planifier (cron système, systemd timer, GitHub Actions ou tâche planifiée Hermes) — par exemple
toutes les 3 heures :

```
0 */3 * * * cd $HOME/blog-ia && bash scripts/run.sh >> $HOME/blog-ia/run.log 2>&1
```

## Note éditoriale

Les résumés affichés sont ceux fournis par les flux ; chaque carte renvoie à l'article original.
Rien n'est recopié intégralement.
