---
title: Pendant qu'un agent attend son outil, 4,8 Go ne font rien
date: 2026-11-09
summary: Le coût d'un agent ne se lit pas dans les tokens produits mais dans la mémoire immobilisée entre deux appels d'outils. Calcul du KV cache sur un modèle 8B, et ce que les chiffres de NVIDIA supposent.
tags: agents, inference, infrastructure, cout
sources:
- NVIDIA — More Performance From Every Byte: How Full-Stack Codesign Solves AI's Memory Challenge (nov. 2026) | https://blogs.nvidia.com/blog/memory-full-stack-codesign/
- Hugging Face — Qwen/Qwen3-8B, config.json | https://huggingface.co/Qwen/Qwen3-8B/blob/main/config.json
- vLLM — Automatic Prefix Caching (documentation) | https://docs.vllm.ai/en/latest/features/automatic_prefix_caching.html
---

Un agent travaille par tours. Il lit, décide, appelle un outil, attend, relit le résultat, recommence. La facture, elle, ne compte que les tokens produits. Entre deux appels, la session existe toujours : son contexte est en mémoire, et cet espace est soit occupé sans rien produire, soit recalculé au tour suivant.

<figure>
  <div class="fig-scroll"><img src="../img/tour-agent-attente.svg" alt="Frise d'un tour d'agent en quatre segments : préremplissage, appel d'outil, génération, nouvel appel d'outil, avec un bandeau indiquant que le KV cache reste alloué de bout en bout."></div>
  <figcaption><b>Figure 1</b> — Le calcul s'arrête pendant l'appel d'outil. La place mémoire, elle, ne se libère pas toute seule.</figcaption>
</figure>

## Le contexte ne disparaît pas quand le calcul s'arrête

Un tour d'agent se décompose en trois temps. Le préremplissage traite le prompt et remplit le cache d'attention, ce qu'on appelle le KV cache. La génération produit les tokens de la réponse. Et entre les deux, à chaque appel d'outil, le modèle attend un résultat qui vient du réseau, d'une base ou d'un script.

Côté serveur d'inférence, un appel d'outil est une frontière. La requête peut se terminer là, et le contexte peut être conservé pour la suite ou jeté. Conserver veut dire immobiliser de la mémoire HBM pendant tout le temps de l'outil. Jeter veut dire recalculer le préfixe au tour suivant. vLLM documente cette mécanique sous le nom de prefix caching : un nouveau prompt qui partage le début d'une requête déjà vue réutilise son cache au lieu de le recalculer [3]. La nuance qui compte, c'est que le cache n'est conservé que s'il n'a pas été évincé, et un cache plein évince.

Vu du budget, les deux options coûtent. L'une paie en mémoire, l'autre en calcul. Aucune des deux n'apparaît dans le compteur de tokens que la plupart des équipes regardent.

## Ce que pèse un contexte, en clair

Le calcul tient en une formule. Le KV cache stocke, pour chaque couche et chaque token, une clé et une valeur par tête KV : deux matrices de `têtes KV × dimension` valeurs, à la précision choisie.

Prenons un modèle 8B courant, Qwen3-8B : 36 couches, 8 têtes KV, dimension de tête 128, en bf16 [2]. Cela donne 147 456 octets par token, soit 144 KiB. Un contexte de 32 000 tokens occupe donc 4,8 Go pour une seule session. Sur un GPU de 80 Go, une fois les poids rangés (16 Go en bf16 pour un 8B), il reste de la place pour environ treize sessions de cette taille. Pas treize mille, treize.

<figure>
  <div class="fig-scroll"><img src="../img/kv-cache-capacite.svg" alt="Graphique en échelle logarithmique : 4,8 Go pour 32k tokens, 19,3 Go pour 128k, 147,5 Go pour un million et 442,4 Go pour trois millions, avec la ligne des 80 Go d'un GPU."></div>
  <figcaption><b>Figure 2</b> — Mémoire KV d'une session selon la longueur du contexte, sur Qwen3-8B. La barre grise est la même mesure avec un cache en 4 bits. Calcul reproductible à partir de la configuration du modèle [2].</figcaption>
</figure>

NVIDIA cite des trajectoires d'agents allant jusqu'à trois millions de tokens [1]. À cette échelle, le cache fait 442 Go en bf16 et 110 Go en 4 bits : aucun GPU ne le contient, quel que soit le modèle d'architecture. C'est l'argument que je trouve le plus solide du dossier, et il ne vient pas d'un benchmark. Il vient d'une multiplication.

## Ce que NVIDIA mesure, et sur quel workload

L'entreprise avance un chiffre qui circule beaucoup : jusqu'à 30 fois plus de débit par dollar sur la plateforme Vera Rubin NVL72 par rapport à GB300 NVL72, à 125 tokens par seconde et par utilisateur, avec environ 3 % de capacité HBM en plus par GPU [1]. Plus haut dans la gamme, GB300 NVL72 est donné à 10 fois H200 à 100 tokens par seconde, avec une capacité doublée.

Ce sont des chiffres d'éditeur, sur un workload nommé (SemiAnalysis AgentX DeepSeek V4 Pro) et à un point de fonctionnement précis. Ils ne disent pas ce que gagnera un service qui fait des résumés de 2 000 tokens. Ils disent qu'à débit utilisateur constant, la génération de plateforme compte plus que la génération de mémoire brute.

Les leviers sont nommés, et deux concernent directement le temps d'attente : un cache KV en 4 bits, et le déplacement du contexte inactif vers un palier de stockage partagé, puis son retour avant réutilisation.

<figure>
  <div class="fig-scroll"><img src="../img/nvidia-pile-memoire.jpg" alt="Schéma NVIDIA en trois colonnes : poids du modèle (réduire et distribuer, NVFP4 et NVL72), cache KV (réduire et déporter le contexte inactif, Dynamo, CMX, Vera), données RAG (compacter et garder hors HBM)."></div>
  <figcaption><b>Figure 3</b> — Les trois sources de pression mémoire et les leviers associés. Source : NVIDIA, <i>More Performance From Every Byte</i> (novembre 2026) [1].</figcaption>
</figure>

Ce que j'en retiens de concret : le contexte d'une session en pause devient un objet que l'on planifie. NVIDIA le formule sans détour, un CPU plus rapide raccourcit le temps pendant lequel le cache reste inactif pendant un appel d'outil, et sa mémoire LPDDR sert de salle d'attente à proximité du GPU [1]. C'est la première fois que je vois la latence d'un outil traitée comme un paramètre de capacité mémoire.

## Ce que je n'ai pas pu mesurer

Je n'ai pas de GPU sur la machine où j'écris ceci, donc aucun chiffre de débit ci-dessus ne vient de moi. Le calcul de la figure 2, en revanche, se refait en dix lignes à partir du `config.json` du modèle. Le protocole que j'appliquerais sur un serveur réel tient en trois compteurs par session : temps passé dans l'outil, tokens de contexte effectivement résidents, et tokens produits. Le ratio qui compte est celui des secondes où la mémoire est occupée sans qu'un token sorte.

Ce ratio a une conséquence directe sur la conception. Un outil qui répond en 200 millisecondes et un outil qui répond en 40 secondes n'ont pas le même coût d'infrastructure, même s'ils renvoient le même JSON. Le second immobilise une place treize fois plus longtemps au minimum, et parfois la libère en forçant un recalcul.

## Ce que je retiens

Un budget mémoire par session, pas par requête. Dimensionner un agent sur son nombre d'appels simultanés revient à ignorer la moitié du problème.

La durée des outils est un paramètre de capacité. Un timeout généreux se paie en mémoire, pas seulement en latence perçue.

Et les « fois 30 » sont des points de mesure sur un workload nommé. Ils indiquent une direction, pas une promesse applicable à votre trafic.
