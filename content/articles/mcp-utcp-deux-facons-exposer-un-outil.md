---
title: MCP et UTCP : deux façons d'exposer un outil à un agent
date: 2026-11-03
summary: MCP normalise l'intermédiaire, UTCP le supprime. Derrière l'opposition d'architecture se cache un déplacement du coût — et du risque — vers le client.
tags: agents, protocoles, architecture, mcp
sources:
- Model Context Protocol — Specification 2026-07-28 | https://modelcontextprotocol.io/specification/2026-07-28
- Model Context Protocol — Transports | https://modelcontextprotocol.io/specification/2026-07-28/basic/transports
- Model Context Protocol — Authorization | https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization
- Model Context Protocol — Introduction | https://modelcontextprotocol.io/docs/2026-07-28/getting-started/intro
- Universal Tool Calling Protocol — Introduction (v1.1) | https://www.utcp.io/
- Universal Tool Calling Protocol — UTCP vs MCP | https://www.utcp.io/utcp-vs-mcp
- Universal Tool Calling Protocol — Security Considerations | https://www.utcp.io/security
- GitHub — modelcontextprotocol/servers | https://github.com/modelcontextprotocol/servers
- GitHub — universal-tool-calling-protocol/python-utcp | https://github.com/universal-tool-calling-protocol/python-utcp
- Hacker News — discussion « Universal Tool Calling Protocol » (août 2025) | https://news.ycombinator.com/item?id=44939642
---

Deux protocoles, un même problème : comment un agent apprend-il qu'un outil existe, et comment l'appelle-t-il ? MCP normalise l'intermédiaire ; UTCP supprime l'intermédiaire et décrit l'appel direct. La différence n'est pas une version d'écart, c'est un désaccord sur l'endroit où doit vivre la complexité.

## MCP : un contrat, un serveur

MCP repose sur trois rôles — l'hôte (l'application LLM), le client (le connecteur) et le serveur (ce qui expose les capacités) — et sur des messages JSON-RPC 2.0 [1]. Le transport est un simple binding : soit des messages délimités par des retours à la ligne sur les flux d'un sous-processus lancé par le client, soit un POST HTTP vers un point d'entrée unique, avec réponse JSON ou flux SSE [2].

Le serveur n'est donc pas un détail d'implémentation : c'est le lieu où l'outil est traduit en contrat. Et ce contrat ne se limite pas aux fonctions appelables. Un serveur MCP expose des *resources* (du contexte), des *prompts* (des workflows paramétrés) et des *tools* (des fonctions) ; le client peut en retour solliciter l'utilisateur via *elicitation* [1]. S'y ajoutent des extensions optionnelles négociées à l'initialisation : tâches asynchrones, instructions structurées pour agents, interfaces interactives dans la conversation [1].

L'autorisation est traitée au niveau du transport, selon un sous-ensemble d'OAuth 2.1 : le serveur MCP est un serveur de ressources, le client un client OAuth, et la découverte du serveur d'autorisation fait partie de la spécification [3].

## UTCP : un manuel, pas un serveur

UTCP prend le problème par l'autre bout. Au lieu d'envelopper l'outil, on publie un *manual* — un document JSON qui décrit comment appeler l'outil dans son protocole natif : HTTP, CLI, WebSocket, SSE, gRPC, ou même MCP via un plugin [5]. L'agent découvre le manuel, en déduit les paramètres, puis appelle l'API directement, avec son authentification, son rate limiting et ses codes d'erreur d'origine [5].

Le projet revendique une filiation avec OpenAPI : une spécification existante se convertit en manuel sans modifier l'API, et un point d'entrée `GET /utcp` suffit à rendre un service découvrable [5]. La promesse : zéro serveur à écrire, zéro processus à superviser, zéro saut réseau supplémentaire.

## Ce que la comparaison officielle ne dit pas

Le tableau comparatif le plus cité vient du site d'UTCP lui-même : c'est un plaidoyer [6]. Il est exact sur l'architecture — un serveur et un saut réseau en moins — mais présente la latence et la maintenance comme des coûts intrinsèques de MCP, alors qu'ils dépendent de ce que l'on expose. Envelopper une API interne mal documentée coûte cher ; exposer un service déjà propre coûte peu.

Deux critiques du tableau ont d'ailleurs mal vieilli. La première visait la gestion de session : la révision 2026-07-28 du protocole est stateless, avec négociation de capacités par requête [1]. La seconde visait l'impossibilité de parler d'autres protocoles : MCP définit désormais un mécanisme de transports personnalisés, à condition de préserver le format JSON-RPC et le modèle de métadonnées [2].

## Le coût ne disparaît pas, il change de camp

C'est le point que je retiens de la lecture des deux spécifications. UTCP ne supprime pas la complexité de l'intégration : il la déplace du serveur vers le client. Le client doit gérer plusieurs méthodes d'authentification, la substitution de variables, la validation des réponses et la traduction des erreurs natives [7]. Le projet le reconnaît explicitement : les points d'entrée de découverte deviennent des cibles, et la substitution de variables introduit un risque d'injection [7].

Symétriquement, MCP concentre les secrets dans le serveur. C'est plus simple à auditer — un seul endroit à instrumenter — mais c'est aussi un point de défaillance unique, et un serveur compromis donne accès à tout ce qu'il détient. Aucun des deux modèles n'est « plus sûr » dans l'absolu : l'un répartit les credentials dans le runtime de l'agent, l'autre les centralise dans un processus tiers.

## Le vrai critère : ce que vous possédez déjà

Si vous avez des API propres et documentées, UTCP est cohérent : un fichier de description, rien de plus à maintenir. Si vous avez besoin de contexte structuré, de prompts versionnés, d'interfaces dans la conversation ou de tâches asynchrones, MCP couvre un périmètre qu'UTCP n'a pas vocation à couvrir.

L'écosystème donne un ordre de grandeur, pas un verdict. Le dépôt de serveurs de référence MCP dépasse 91 000 étoiles, avec dix SDK officiels et un registre public [8][4] ; l'implémentation Python d'UTCP en compte environ 650, pour un projet créé à l'été 2025 [9]. Cela mesure la surface d'exposition aux cas limites, pas la qualité du design.

La critique la plus fréquente reste celle du HN de l'époque : encore une abstraction qui éloigne du métal [10]. Elle est partiellement juste — un appel d'outil est un appel de fonction — mais elle ignore ce que l'abstraction règle : parsing des appels, appels invalides, appariement entre réponse et requête d'origine, états d'erreur. Des problèmes communs, pas spécifiques à un projet.

## Ce que je retiens

Trois règles, valables quel que soit le protocole choisi.

1. **Un credential par outil, jamais dans le prompt.** Le manuel UTCP comme le serveur MCP ne doivent contenir que des références à des variables d'environnement, jamais de secret en clair [5][7].
2. **Journaliser chaque appel d'outil.** Sans trace des paramètres et du résultat, un échec d'agent est une trajectoire, pas un bug — donc indébogable.
3. **Traiter la description d'un outil comme non fiable.** La spécification MCP le dit explicitement : les annotations décrivant le comportement d'un outil ne valent que si le serveur est de confiance [1]. C'est une surface d'injection, pas de la documentation.

Le choix par défaut reste MCP, pour l'interopérabilité et la couverture du contexte. UTCP a un vrai cas d'usage : exposer une API existante sans écrire de serveur, et parler plusieurs protocoles natifs. Les deux cohabitent d'ailleurs — un client UTCP peut consommer des serveurs MCP via plugin [5]. La question utile n'est donc pas « lequel est le meilleur », mais « qui détient les credentials, et qui peut les révoquer ».
