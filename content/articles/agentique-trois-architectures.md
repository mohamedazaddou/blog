---
title: « Agentique » : trois architectures différentes derrière un seul mot
date: 2026-11-01
summary: Le mot « agent » recouvre des systèmes qui n'ont ni les mêmes coûts, ni les mêmes modes de panne. Distinguer workflow et agent change les choix d'architecture — et le budget.
tags: agents, architecture, llm
sources:
- Anthropic — Building effective agents (déc. 2024) | https://www.anthropic.com/research/building-effective-agents
- Google Cloud — 2025 DORA Report: State of AI-Assisted Software Development | https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report
- Stack Overflow — Developer Survey 2025, section AI | https://survey.stackoverflow.co/2025/ai
---

On ne vend plus des modèles, on vend des « agents ». Le mot est devenu un argument commercial : il suffit qu'une application appelle un LLM deux fois de suite pour qu'on parle d'« agent autonome ». Derrière ce vocabulaire unique se cachent pourtant des systèmes aux propriétés très différentes — et surtout, aux modes de panne incompatibles.

## Le mot recouvre deux choses distinctes

Anthropic a posé la distinction la plus utile dès décembre 2024, dans *Building effective agents* : un **workflow** est un système où les LLM et les outils sont orchestrés par des chemins de code prédéfinis ; un **agent**, en revanche, est un système où le modèle dirige lui-même son processus et l'usage de ses outils, en gardant la main sur la manière d'accomplir la tâche [1].

La différence n'est pas sémantique, elle est structurelle :

- dans un workflow, **le graphe d'exécution est connu à l'avance** : je peux le tester, le borner, prévoir son coût maximal ;
- dans un agent, **le graphe est découvert à l'exécution** : je ne peux garantir que la boucle d'outils, les bornes de temps et le format de sortie.

Anthropic ajoute une recommandation qui a mal vieilli dans le discours ambiant : commencer par la solution la plus simple possible, et n'augmenter la complexité qu'en cas de besoin. Pour beaucoup d'applications, un appel unique au modèle enrichi de contexte suffit [1]. Autrement dit : la plupart des produits qui se disent « agents » sont des workflows, et c'est très bien ainsi.

## Pourquoi la confusion coûte cher

Choisir un agent là où un workflow suffirait se paie sur quatre plans : la latence (boucle d'outils = plusieurs allers-retours), le coût par requête (variable, non borné sans garde-fou), la testabilité (une sortie non déterministe se teste par échantillonnage, pas par assertion), et l'observabilité (il faut tracer chaque décision d'outil pour comprendre un échec).

Inversement, imposer un workflow à un problème ouvert — navigation dans un dépôt inconnu, correction d'un bug dont on ignore la cause — revient à écrire le chemin en dur et à le maintenir à chaque cas nouveau. L'agent existe pour ces cas-là : quand l'espace des chemins possibles est trop large pour être cartographié.

> La bonne question n'est jamais « agent ou pas agent ? », mais « où est le dernier point de contrôle humain, et que se passe-t-il s'il est franchi par erreur ? »

## Ce que les données terrain disent du phénomène

Trois sources récentes donnent la mesure du décalage entre le discours et l'usage réel.

**L'adoption est massive.** Le rapport DORA 2025, construit sur près de 5 000 professionnels, mesure 90 % d'usage de l'IA au travail et plus de 80 % de personnes qui déclarent une productivité accrue [2]. Ce n'est plus un marché émergent, c'est l'état par défaut.

**La confiance, elle, recule.** Dans l'enquête Stack Overflow 2025, 46 % des développeurs déclarent se méfier activement de l'exactitude des outils d'IA, contre 33 % qui leur font confiance, et 3 % seulement déclarent une confiance élevée [3]. Les profils les plus expérimentés sont les plus prudents : 20 % de méfiance forte chez eux [3]. Ce n'est pas un rejet — c'est un ajustement du niveau de vérification.

**L'effet amplificateur.** La conclusion centrale de DORA 2025 est que l'IA n'améliore pas une équipe, elle amplifie ce qui existe déjà : les équipes qui ont des tests automatisés, du versioning propre et des boucles de retour rapides gagnent en débit ; celles qui n'en ont pas voient surtout leur instabilité augmenter [2]. L'IA n'est donc pas un correctif d'organisation, c'est un multiplicateur.

## Trois questions avant de dire « agent »

Si vous devez trancher pour un projet, ces trois filtres suffisent dans la majorité des cas.

1. **L'action est-elle réversible ?** Lecture de fichiers, recherche, génération de patch : réversible. Suppression de données, envoi d'e-mail, paiement, `git push --force` : irréversible, donc workflow obligatoire avec validation explicite avant l'action.
2. **Le chemin est-il connaissable à l'avance ?** Si oui, écrivez-le. Un agent qui redécouvre à chaque exécution un chemin que vous connaissez déjà est un générateur de latence et de facture.
3. **Que m'apprend un échec ?** Sur un workflow, la trace est lisible : l'étape N a échoué. Sur un agent, l'échec est une trajectoire ; sans journalisation des appels d'outils, il est indébogable — et donc inexploitable en production.

## Ce que je retiens

« Agentique » ne désigne pas un niveau d'intelligence, mais une **répartition du contrôle** : qui décide de la prochaine étape, du code ou du modèle. Tant que cette frontière n'est pas explicite dans l'architecture, le mot reste un argument marketing, et la facture d'API devient la seule mesure de l'autonomie réelle du système.

La suite logique de ce raisonnement — ce que les agents produisent vraiment quand on les met au service de l'écriture de logiciel — fait l'objet du second article de ce blog.
