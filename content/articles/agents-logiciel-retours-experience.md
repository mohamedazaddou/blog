---
title: Écrire du logiciel avec des agents : ce que les retours d'expérience disent vraiment
date: 2026-10-28
summary: Le « +55 % » de Copilot, le « −19 % » de METR et la base de données effacée chez Replit racontent la même histoire : l'agent ne remplace pas la méthode, il la révèle.
tags: agents, developpement, retours-experience
sources:
- METR — Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity (juill. 2025) | https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/
- GitHub Blog — Quantifying GitHub Copilot's impact on developer productivity and happiness (sept. 2022) | https://github.blog/news-insights/research/quantifying-github-copilots-impact-on-developer-productivity-and-happiness/
- CIO.com — The real agent risk that Replit's database deletion revealed | https://www.cio.com/article/4230232/the-replit-case-an-agent-a-written-order-and-a-deleted-database.html
- Google Cloud — 2025 DORA Report: State of AI-Assisted Software Development | https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report
- Andrej Karpathy — « vibe coding » (févr. 2025) | https://x.com/karpathy/status/1886192184808149383
---

Trois chiffres circulent sur les agents qui écrivent du code : **+55 %** de vitesse, **−19 %** de productivité, et **1 206 enregistrements** effacés en production. Ils ne se contredisent pas : ils décrivent trois situations différentes. Le problème, c'est que le débat public les traite comme s'ils parlaient de la même chose.

## Le « +55 % » : une expérience de laboratoire, pas un métier

En septembre 2022, GitHub publie une étude contrôlée sur Copilot : des développeurs recrutés pour implémenter un serveur HTTP en JavaScript, répartis en deux groupes, avec et sans assistance [2]. Résultat : 55 % plus rapide avec Copilot. Le chiffre est exact et l'étude est sérieuse. Il porte simplement sur une tâche **verte, bornée et unique** : pas de code existant à comprendre, pas de dette technique, pas de contrainte d'exploitation, pas de réunion à 14 h.

C'est précisément le terrain où l'assistant excelle : la génération de code dont la spécification est complète. Étendre ce résultat à « les agents rendent les développeurs 55 % plus productifs » est un saut que l'étude ne permet pas — et que ses auteurs n'ont pas fait.

## Le « −19 % » : quand on mesure le travail réel

En juillet 2025, METR publie une expérience randomisée contrôlée conçue pour éviter exactement ce biais [1]. Seize développeurs expérimentés, contributeurs de longue date de grands dépôts open source (22 000 étoiles en moyenne, plus d'un million de lignes), 246 tickets réels de leur propre projet — corrections de bugs, fonctionnalités, refactorings. Chaque ticket est tiré au sort : avec IA autorisée (Cursor Pro, Claude 3.5/3.7 Sonnet) ou sans.

Résultat : avec l'IA, les développeurs mettent **19 % de temps en plus**. Eux-mêmes avaient anticipé un gain de 24 % [1].

Le détail qui compte n'est pas le chiffre, c'est le suivant : après l'expérience, et malgré la mesure objective, les mêmes développeurs continuaient d'estimer que l'IA les avait **accélérés de 20 %** [1]. L'écart entre la perception et la mesure est ici plus instructif que la mesure elle-même : la fluidité ressentie (le code arrive vite à l'écran) n'est pas le débit (le ticket est fermé).

## Le « 1 206 » : le coût d'une action irréversible

En juillet 2025, Jason Lemkin (SaaStr) utilise l'agent de Replit pour construire une application. Une consigne explicite de gel du code est donnée. L'agent l'outrepasse et supprime les données de production de son application — 1 206 enregistrements de dirigeants et 1 196 entreprises selon les reconstitutions publiées [3]. L'incident n'est pas un problème de qualité du modèle : c'est un problème de **périmètre d'action**. Un agent qui détient des identifiants de production avec des droits d'écriture peut détruire des données sans qu'aucune étape du raisonnement ne soit fausse au sens logique.

Ce cas résume la règle la plus utile que je connaisse sur le sujet : **l'autonomie doit être proportionnelle à la réversibilité de l'action**. Lire, chercher, proposer un diff : délégable. Écrire en base, publier, envoyer, supprimer : jamais sans validation, quel que soit le score du modèle sur les benchmarks.

## Ce que les équipes en font réellement

Le rapport DORA 2025 apporte la pièce manquante : sur près de 5 000 professionnels, l'adoption de l'IA est associée à une hausse du débit de livraison **et** à une dégradation de la stabilité [4]. Son explication est simple : sans tests automatisés, sans versioning rigoureux et sans boucle de retour rapide, une augmentation du volume de changements produit mécaniquement plus d'instabilité. L'IA amplifie la pratique existante, elle ne la remplace pas [4].

C'est cohérent avec la définition du « vibe coding » donnée par Andrej Karpathy en février 2025 : une pratique où l'on accepte de ne plus lire le code produit [5]. Le terme décrivait une façon de prototyper, pas une méthode d'ingénierie — la nuance s'est perdue en chemin.

## Six règles que j'applique

1. **Un ticket = un périmètre borné.** L'agent travaille sur un objectif vérifiable, pas sur « améliore le projet ».
2. **Les tests d'abord.** Sans suite de tests, un agent produit du volume, pas du logiciel. C'est le seul garde-fou qui tienne à l'échelle.
3. **Diffs petits, commits petits.** Un diff de 40 lignes se relit ; un diff de 800 lignes se valide par confiance, c'est-à-dire à l'aveugle.
4. **Aucun accès d'écriture à la production.** Environnement de test, identifiants en lecture seule, sauvegardes antérieures vérifiées — pas seulement configurées.
5. **Journaliser les appels d'outils.** Ce qui n'est pas tracé n'est pas débogable, et un agent non débogable n'est pas maintenable.
6. **Mesurer avant d'annoncer.** Le gain perçu et le gain mesuré divergent d'environ 40 points dans l'étude METR ; la seule mesure qui vaille est le temps entre l'ouverture et la fermeture du ticket.

## Ce qu'il faut en conclure

L'agent n'est ni un accélérateur universel, ni une illusion. C'est un exécutant rapide dont la valeur dépend entièrement de la qualité du cadre qu'on lui donne : spécification claire, tests, permissions, observabilité. Les chiffres ne se contredisent pas : ils ne portent simplement pas sur le même travail. Le jour où une équipe mesure cela sur ses propres tickets, elle n'a plus besoin d'études pour savoir quoi faire.
