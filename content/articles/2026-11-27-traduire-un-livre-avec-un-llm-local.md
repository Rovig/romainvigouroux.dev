---
title: "Traduire un livre entier avec un LLM local ou n'importe quelle API"
description: "Stridon traduit EPUB, PDF illustrés, sous-titres et articles web avec Ollama, Claude, GPT ou DeepL, en gardant la structure du document et en reprenant là où il s'est arrêté."
date: 2026-11-27
slug: traduire-un-livre-avec-un-llm-local
tags: [LLM local, Architecture IA, Agentic coding]
keywords: [traduction automatique, Ollama, LLM, EPUB, PDF, Claude, open source]
tldr: "Traduire un livre avec un LLM n'est pas un problème de prompt mais de document : découper sans casser la structure, garder le contexte, survivre aux coupures et pouvoir changer de modèle. Stridon sépare le moteur, le cache, les traducteurs et les formats pour résoudre chacun de ces points."
problem: "Traduire un livre ou un long PDF illustré avec une IA, sans perdre la mise en page et sans tout recommencer à la moindre coupure."
context: "Outil personnel publié en open source, utilisé en ligne de commande, avec des modèles locaux gratuits ou des API payantes."
constraints:
  - "Garder la structure : chapitres, titres, images, notes, sous-titres horodatés"
  - "Fonctionner avec un modèle local gratuit comme avec une quinzaine de services"
  - "Reprendre une traduction interrompue sans repayer ce qui est déjà traduit"
  - "Garder les noms et le ton cohérents d'un chapitre à l'autre"
stack: [Python, Ollama, Claude, OpenAI, PyMuPDF, BeautifulSoup, Docker, Claude Code]
outcome: "Un outil publié en version 1.0 sur GitHub, avec documentation en français, anglais et chinois, tests automatisés et image Docker. [À CONFIRMER : volume traduit, modèle local préféré, temps pour un livre]"
faq:
  - q: "Peut-on traduire un livre avec un LLM local gratuit ?"
    a: "Oui. Stridon utilise par défaut Ollama sur la machine de l'utilisateur, sans clé ni coût. La même commande fonctionne avec Claude, GPT, Gemini, Mistral, DeepL ou Google Traduction en changeant une option, ce qui permet de comparer la qualité sur un même texte."
  - q: "Comment éviter de perdre une traduction longue en cas de coupure ?"
    a: "Chaque passage traduit est sauvegardé dès qu'il arrive. Si la traduction s'arrête, on relance la même commande : les passages déjà traduits sont réutilisés et ne sont pas renvoyés au service. Changer la présentation, bilingue ou non, ne coûte aucune nouvelle requête."
  - q: "Comment garder les noms de personnages cohérents dans une traduction par IA ?"
    a: "En envoyant au modèle les derniers paragraphes déjà traduits comme contexte. Les chapitres sont alors traduits dans l'ordre, et le modèle voit comment un nom ou un terme a été rendu juste avant."
  - q: "Que fait Stridon des PDF avec images ?"
    a: "Il reconstruit un nouveau PDF où la traduction s'enchaîne de page en page avec les images à leur place et les titres plus grands. En mode bilingue, chaque page d'origine donne une page avec l'original en noir et la traduction en bleu."
linkedin: false
linkedin_post: |
  Traduire un livre avec un LLM, ce n'est pas un problème de prompt. C'est un problème de document.

  Un EPUB a des chapitres, des notes, des images. Un PDF a des colonnes et des numéros de page. Un fichier de sous-titres a des horaires qu'on ne doit pas toucher.

  Et une traduction de 400 pages s'interrompt toujours : coupure réseau, quota dépassé, Ctrl+C.

  J'ai construit Stridon autour de quatre briques séparées : un moteur qui découpe, un cache qui garde chaque passage traduit, des traducteurs interchangeables (Ollama en local, Claude, GPT, DeepL…) et des formats qui reconstruisent le document.

  Relancer la même commande reprend là où on s'était arrêté, sans repayer un seul paragraphe.

  Vous traduisez avec un modèle local ou une API ?

  #LLM #AgenticCoding #OpenSource
---
Traduire un livre avec un LLM pose surtout des problèmes de document : découper sans casser la structure, garder
la cohérence d'un chapitre à l'autre, survivre aux coupures et pouvoir changer de modèle. J'ai écrit Stridon, un
outil open source en ligne de commande, qui traduit EPUB, PDF illustrés, Markdown, sous-titres et articles web avec
un modèle local via Ollama ou une quinzaine de services, et qui reprend là où il s'est arrêté.

## La situation

Lire un livre sans DRM, un rapport en PDF plein de figures ou un article web dans une autre langue que celle de
sa publication reste laborieux. Les traducteurs de documents en ligne traitent un fichier à la fois, perdent souvent
la mise en page et imposent leur moteur. [À CONFIRMER : le besoin personnel ou client qui a déclenché le projet]

Les LLM traduisent bien mieux qu'il y a quelques années, y compris en local. Mais coller un chapitre dans une
conversation ne fait pas un livre traduit.

## Pourquoi c'est plus difficile qu'il n'y paraît

**La structure est fragile.** Un EPUB mélange paragraphes, titres, appels de notes, code et légendes d'images. Un
PDF n'a pas de paragraphes du tout, seulement des blocs de texte sur des pages. Un fichier SRT impose de garder les
numéros et les horaires intacts.

**Les longues traductions s'interrompent.** Sur des centaines de pages, il y aura une coupure réseau, un quota
dépassé ou un refus ponctuel du modèle. Recommencer depuis le début coûte du temps et de l'argent.

**La cohérence se perd entre les requêtes.** Chaque requête ignore les précédentes : un nom propre ou un terme
technique peut changer de traduction d'un chapitre à l'autre.

**Aucun modèle ne gagne partout.** Un modèle local est gratuit et privé, une API est souvent meilleure ou plus
rapide, un service spécialisé comme DeepL excelle sur certaines paires de langues. Il faut pouvoir choisir.

## Les pistes écartées

| Option | Pourquoi je l'ai écartée |
|---|---|
| Copier-coller dans un assistant IA | Ne passe pas à l'échelle d'un livre, perd la structure |
| Un service de traduction de documents en ligne | Un seul moteur, mise en page souvent dégradée, documents envoyés à un tiers |
| Un script lié à une seule API | Impossible de comparer ou de basculer vers un modèle local |

## L'architecture retenue

```text
fichier ─► format (EPUB, PDF, TXT, MD, SRT, web) ─► passages
                                                     │
                     cache des traductions ◄────────►│ moteur : regroupement, contexte, parallélisme
                                                     │
                       traducteur interchangeable ◄──┘ Ollama, Claude, OpenAI, Gemini, Mistral, DeepL…
                                                     │
                                       format ─► document reconstruit (traduit ou bilingue)
```

**Les formats** savent extraire des passages traduisibles et reconstruire le document : balises choisies pour
l'EPUB, images replacées dans le PDF, horaires conservés dans le SRT, code laissé intact dans le Markdown.

**Le moteur** regroupe les paragraphes par bloc ou par nombre de tokens, envoie plusieurs requêtes en parallèle et
peut joindre au modèle les derniers paragraphes traduits pour garder le ton et les noms cohérents.

**Le cache** enregistre chaque passage dès qu'il est traduit. Relancer la même commande reprend là où on s'était
arrêté ; une option permet de retraduire un seul passage puis de reconstruire tout le fichier depuis le cache.

**Les traducteurs** partagent une même interface. Ollama est le service par défaut, en local et sans clé. Tout
serveur compatible OpenAI (LM Studio, vLLM, une passerelle d'entreprise) se déclare dans un simple fichier JSON. Pour
les gros volumes, l'API Batch d'OpenAI divise le coût par deux.

## Ce que ça a donné

Stridon est publié en version 1.0 sur GitHub, avec une documentation en français, anglais et chinois, un guide
d'architecture qui explique comment ajouter un service ou un format, des tests automatisés et une image Docker. Le
développement s'est fait en agentic coding avec Claude Code.

[À CONFIRMER : volume déjà traduit, modèle local préféré, temps typique pour un livre.]

## Ce que je referais différemment

Le choix du modèle reste empirique : Stridon permet de traduire un même texte avec plusieurs services, mais ne mesure
pas la qualité lui-même. C'est la limite de l'outil aujourd'hui ; le correcteur de copies que j'ai construit ensuite
pose justement la question de la mesure avec un banc d'essai.
