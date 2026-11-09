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

Trois chiffres circulent sur les agents qui écrivent du code : +55 % de vitesse, −19 % de productivité, et 1 206 enregistrements effacés en production. Ils ne se contredisent pas. Ils ne parlent pas du même travail, et le débat public les traite comme s'ils mesuraient la même chose.

<figure>
  <div class="fig-scroll"><img src="../img/trois-chiffres-productivite.svg" alt="Trois barres : plus 55 pour cent en laboratoire, plus 20 pour cent de gain perçu, moins 19 pour cent de temps mesuré sur des tickets réels."></div>
  <figcaption><b>Figure 1</b> — Les deux derniers chiffres viennent de la même étude, avec les mêmes développeurs : l'écart de 39 points est l'écart entre le ressenti et la mesure.</figcaption>
</figure>

## Le +55 % venait d'une tâche propre

En septembre 2022, GitHub publie une étude contrôlée sur Copilot : des développeurs recrutés pour implémenter un serveur HTTP en JavaScript, répartis en deux groupes, avec et sans assistance [2]. Résultat, 55 % plus rapide avec Copilot. Le chiffre est exact et l'étude est sérieuse.

J'ai relu le protocole avant d'écrire ce paragraphe, parce que la tentation est de disqualifier le résultat. Il n'y a rien à disqualifier. La tâche est simplement **verte** : pas de code existant à comprendre, pas de dette, pas de contrainte d'exploitation, pas de réunion à 14 h. C'est exactement le terrain où l'assistant excelle, la génération de code dont la spécification est complète. Étendre ce résultat à « les agents rendent les développeurs 55 % plus productifs » est un saut que l'étude ne permet pas, et que ses auteurs n'ont pas fait.

## Le −19 % : quand on mesure le ticket, pas la frappe

En juillet 2025, METR publie une expérience randomisée construite pour éviter ce biais [1]. Seize développeurs expérimentés, contributeurs de longue date de grands dépôts open source (22 000 étoiles en moyenne, plus d'un million de lignes), 246 tickets réels de leur propre projet. Chaque ticket est tiré au sort : avec IA autorisée (Cursor Pro, Claude 3.5 et 3.7 Sonnet) ou sans.

Avec l'IA, ils mettent 19 % de temps en plus. Eux-mêmes avaient annoncé un gain de 24 % avant l'expérience [1].

Ce qui m'a le plus marqué n'est pas le chiffre, c'est le suivant. Après l'expérience, mesure objective en main, les mêmes développeurs continuaient d'estimer que l'IA les avait accélérés d'environ 20 % [1]. Le code arrive plus vite à l'écran ; le ticket, lui, ne se ferme pas plus vite. La fluidité ressentie n'est pas le débit.

<figure>
  <div class="fig-scroll"><img src="../img/metr-forecast-vs-observe.png" alt="Graphique METR : temps prévu avec et sans IA (1,4 h contre 1,9 h) et temps réellement observé (2,3 h avec IA contre 1,7 h sans)."></div>
  <figcaption><b>Figure 2</b> — Temps moyen par ticket : prévu à 1,4 h avec l'IA contre 1,9 h sans, observé à 2,3 h avec contre 1,7 h sans. L'estimation publiée par METR, calculée sur l'ensemble des tickets, est un ralentissement de 19 %. Source : METR, <i>Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity</i> (juillet 2025) [1].</figcaption>
</figure>

## Le 1 206 : une question de périmètre

En juillet 2025, Jason Lemkin (SaaStr) utilise l'agent de Replit pour construire une application. Une consigne explicite de gel du code est donnée. L'agent l'outrepasse et supprime les données de production : 1 206 enregistrements de dirigeants et 1 196 entreprises, selon les reconstitutions publiées [3].

<figure>
  <div class="fig-scroll"><img src="../img/frise-incident-replit.svg" alt="Frise en quatre jalons : consigne de gel, agent qui passe outre, suppression de 1 206 enregistrements, incident rendu public."></div>
  <figcaption><b>Figure 3</b> — Le point d'irréversibilité arrive au troisième jalon. Rien dans le raisonnement de l'agent ne distingue « je peux » de « j'ai le droit ».</figcaption>
</figure>

L'incident n'est pas un problème de qualité du modèle, c'est un problème de périmètre d'action. Un agent qui détient des identifiants de production avec des droits d'écriture peut détruire des données sans qu'aucune étape de son raisonnement ne soit fausse au sens logique. Je ne connais pas de meilleure formulation de la règle qui en découle : l'autonomie doit être proportionnelle à la réversibilité de l'action. Lire, chercher, proposer un diff, oui. Écrire en base, publier, envoyer, supprimer : jamais sans validation, quel que soit le score du modèle.

## Ce que les équipes en font réellement

Le rapport DORA 2025 apporte la pièce manquante. Sur près de 5 000 professionnels, l'adoption de l'IA est associée à une hausse du débit de livraison **et** à une dégradation de la stabilité [4]. L'explication est mécanique : sans tests automatisés, sans versioning rigoureux, sans boucle de retour rapide, plus de changements produit plus d'instabilité. L'IA amplifie la pratique existante, elle ne la remplace pas.

C'est cohérent avec ce que Karpathy décrivait en février 2025 sous le nom de « vibe coding » : une pratique où l'on accepte de ne plus lire le code produit [5]. Il parlait d'une façon de prototyper. La nuance s'est perdue en chemin, et elle coûte cher à ceux qui l'ont oubliée.

## Six règles que j'applique

1. Un ticket, un périmètre borné. L'agent travaille sur un objectif vérifiable, pas sur « améliore le projet ».
2. Les tests d'abord. Sans suite de tests, un agent produit du volume, pas du logiciel. C'est le seul garde-fou qui tienne à l'échelle.
3. Petits diffs, petits commits. Un diff de 40 lignes se relit ; un diff de 800 lignes se valide par confiance, c'est-à-dire à l'aveugle.
4. Aucun accès d'écriture à la production. Environnement de test, identifiants en lecture seule, sauvegardes vérifiées et pas seulement configurées.
5. Journaliser les appels d'outils. Un agent non traçable n'est pas débogable, donc pas maintenable.
6. Mesurer avant d'annoncer. Le gain perçu et le gain mesuré divergent d'une quarantaine de points chez METR ; la seule mesure qui compte est le temps entre l'ouverture et la fermeture du ticket.

## Ce qui reste quand on a lu les trois

L'agent n'est ni un accélérateur universel, ni une illusion. C'est un exécutant rapide dont la valeur tient à la qualité du cadre qu'on lui donne : spécification claire, tests, permissions, observabilité. Une équipe qui mesure cela sur ses propres tickets n'a plus besoin d'études pour savoir quoi faire. Les autres continueront de choisir leur chiffre préféré.
