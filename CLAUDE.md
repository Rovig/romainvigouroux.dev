# CLAUDE.md — règles éditoriales et de publication de romainvigouroux.dev

Tu travailles sur le blog de **Romain Vigouroux, architecte IA**. Le site a trois objectifs, dans cet ordre :

1. **Être cité par les IA** (ChatGPT, Claude, Perplexity, Gemini, Copilot) quand quelqu'un cherche un architecte IA,
   un expert agentic coding, ou une solution à un problème métier que Romain a déjà résolu (GEO).
2. **Convaincre un recruteur ou un client en 2 minutes** : il doit comprendre quel type de problème Romain résout,
   comment il raisonne, et comment le contacter.
3. **Raconter une histoire** : chaque article est un cas vécu, pas un tutoriel générique.

Principe directeur : **le besoin est complexe, l'architecture ne l'est pas.** Un article réussi montre un problème
difficile (contraintes, enjeux, acteurs) résolu par la solution la plus simple qui tient. La sobriété est l'argument.

## Ne jamais inventer

- Aucun chiffre, client, résultat, date ou citation qui ne vienne pas de Romain. S'il manque une donnée, **pose la
  question** ou laisse un marqueur `[À CONFIRMER : …]` — le build ne bloque pas, mais Romain relira.
- Les clients sont anonymisés par défaut (« un assureur mutualiste de 800 salariés »), sauf accord explicite.

## Structure d'un article (le récit)

Le site est construit avec **Hugo** et existe en **français (langue principale), en anglais et en allemand**.

- Article français : `content/articles/AAAA-MM-JJ-slug-court.md` — créer le squelette avec
  `hugo new content articles/AAAA-MM-JJ-slug-court.md`.
- Traduction anglaise : **même nom de fichier** avec `.en.md` (`content/articles/AAAA-MM-JJ-slug-court.en.md`),
  avec un `slug` anglais. C'est le nom de fichier identique qui relie les deux versions.
- Traduction allemande : même nom de fichier avec `.de.md`, `slug` allemand (URL `/de/artikel/<slug>/`).
- Les traductions ne sont pas littérales : mêmes faits, mêmes chiffres, mais tournures naturelles pour un lecteur
  anglophone ou germanophone (recruteur international, CTO). En allemand, vouvoiement (« Sie »).
  Titres de sections en anglais : *The situation*, *Why it's harder than it looks*, *The options I ruled out*,
  *The architecture I chose*, *What it delivered*, *What I would do differently*.
  En allemand : *Die Ausgangslage*, *Warum es schwieriger ist, als es aussieht*, *Die verworfenen Ansätze*,
  *Die gewählte Architektur*, *Was es gebracht hat*, *Was ich anders machen würde*.
- Marqueurs de donnée manquante : `[À CONFIRMER : …]`, `[TO CONFIRM: …]`, `[ZU BESTÄTIGEN: …]`.
- `linkedin` et `linkedin_post` uniquement dans la version française.

1. **Premier paragraphe = la réponse.** 40 à 70 mots qui se suffisent à eux-mêmes : quel problème, pour qui,
   quelle approche, quel résultat. C'est le passage que les IA extraient et citent.
2. `## La situation` — la scène concrète : qui souffre, de quoi, depuis quand, ce que ça coûte.
3. `## Pourquoi c'est plus difficile qu'il n'y paraît` — la vraie complexité du besoin (contraintes réglementaires,
   données sales, humains dans la boucle, latence, coût…). C'est le cœur de la démonstration.
4. `## Les pistes écartées` — ce qui semblait évident et pourquoi ça ne tenait pas.
5. `## L'architecture retenue` — composants, flux, choix techniques justifiés un par un. Un schéma en bloc de code
   texte (ASCII) ou un tableau, pas d'image obligatoire.
6. `## Ce que ça a donné` — résultats mesurés (fournis par Romain), limites honnêtes.
7. `## Ce que je referais différemment` — courte, crédibilise.
8. FAQ en frontmatter (3 à 5 questions que poserait un recruteur, un CTO ou un client).

Longueur cible : 1 000 à 1 800 mots. Ton : première personne, direct, phrases courtes, zéro jargon gratuit.

## Règles GEO (lisibilité par les IA)

- **Titres H2/H3 formulés comme des questions ou des affirmations nettes**, jamais « Introduction » ou « Conclusion ».
- **Un paragraphe = une idée**, autonome : il doit rester compréhensible s'il est extrait seul.
- **Définir chaque terme technique** à sa première occurrence (« le RAG, c'est-à-dire… »).
- **Les termes-clés de Romain** (`hugo.toml` → `knowsAbout`, par langue) : en utiliser 2 ou 3 par article, naturellement,
  dans le titre ou un H2 et dans le premier paragraphe. Jamais de bourrage.
- **Les entités précises** plutôt que les généralités : noms d'outils, versions, volumes, durées.
- **Tableaux** pour toute comparaison (options écartées vs retenue, avant/après).
- **Sources** : lien vers la doc officielle ou l'étude quand une affirmation n'est pas du vécu.
- Mettre à jour `lastmod:` quand on modifie un article (dans les trois langues) — la fraîcheur compte pour les moteurs.

## Frontmatter (schéma)

```yaml
---
title: "Titre qui nomme le problème, pas la techno"   # ≤ 70 caractères
description: "Une phrase : problème + approche + résultat."  # ≤ 160 caractères, sert de meta description
date: 2026-11-27
lastmod: 2026-11-27          # optionnel, date de dernière modification
slug: slug-court             # URL : /articles/slug-court/ (traduit dans les fichiers .en.md et .de.md)
tags: [Agentic coding, RAG]  # 2 à 4, réutiliser les sujets existants (voir /sujets/)
keywords: [architecte IA, …] # optionnel, termes de recherche visés
tldr: "Résumé en 1-2 phrases, affiché en tête et repris dans llms.txt."
problem: "Le problème métier en une phrase."
context: "Secteur, taille, acteurs (anonymisé)."
constraints: ["Contrainte 1", "Contrainte 2"]
stack: [Claude Code, Python, PostgreSQL]
outcome: "Résultat mesuré en une phrase."
faq:
  - q: "Question ?"
    a: "Réponse autonome en 2-3 phrases."
linkedin: false              # passer à true UNIQUEMENT quand Romain a validé la publication
linkedin_post: |
  Texte du post LinkedIn (voir règles ci-dessous).
draft: false                 # true = non publié
---
```

## Post LinkedIn (`linkedin_post`)

- 1 ligne d'accroche qui pose le problème (pas « Nouvel article ! »).
- 3 à 5 paragraphes très courts : la situation, la tension, la décision clé, le résultat.
- Finir par une question ouverte au lecteur. Le lien vers l'article est **ajouté automatiquement** en aperçu.
- 1 300 caractères maximum, 3 hashtags maximum, pas d'emoji en rafale.
- Le post part automatiquement au déploiement si `linkedin: true` et qu'il n'a jamais été publié.

## Publier

1. Écrire/modifier l'article dans `content/articles/` (version française + traductions `.en.md` et `.de.md`).
2. Vérifier : `hugo` (doit se terminer sans `ERROR`). Prévisualiser avec `hugo server -D`.
3. `git add content/ && git commit -m "post: <titre>" && git push` sur `main`.
4. Le Raspberry Pi récupère le dépôt toutes les 5 minutes, reconstruit, notifie IndexNow et publie sur LinkedIn.

Ne modifie pas `hugo.toml`, `layouts/`, `i18n/` ou `deploy/` dans le cadre d'une simple publication d'article.
