---
title: "Exister dans les réponses des IA avec un blog sur Raspberry Pi"
description: "Comment je rends mon expertise d'architecte IA lisible par ChatGPT, Claude et Perplexity avec un site statique auto-hébergé, mesuré chaque semaine."
date: 2026-11-27
tags: [GEO, Architecture IA, Agentic coding]
keywords: [GEO, generative engine optimization, llms.txt, architecte IA, Raspberry Pi]
tldr: "Pour être cité par les IA, il faut des contenus structurés, une identité cohérente et une mesure des visites des robots. Un générateur statique de quelques centaines de lignes, un Raspberry Pi et un tunnel Cloudflare suffisent."
problem: "Quand un recruteur demande à une IA « quel architecte IA connaît l'agentic coding ? », mon nom n'apparaît pas."
context: "Profil indépendant, contenus dispersés entre LinkedIn et Medium, aucune maîtrise de la façon dont les IA lisent ces plateformes."
constraints:
  - "Aucun coût d'hébergement récurrent"
  - "Publier depuis une conversation avec Claude, sans back-office"
  - "Mesurer si les robots d'IA lisent vraiment le site"
  - "Zéro port ouvert sur la box internet"
stack: [Python, Jinja2, Caddy, Cloudflare Tunnel, Raspberry Pi 4, schema.org, llms.txt]
outcome: "Un site entièrement lisible par les machines, publié par un simple git push, avec un rapport hebdomadaire des visites humaines et des robots d'IA. [À CONFIRMER : premiers chiffres après 4 semaines]"
faq:
  - q: "Qu'est-ce que le GEO ?"
    a: "Le GEO (Generative Engine Optimization) consiste à rendre un contenu facile à trouver, comprendre et citer par les moteurs génératifs comme ChatGPT, Claude, Perplexity ou Gemini. Il prolonge le SEO : on optimise pour être repris dans une réponse, pas seulement pour un classement de liens."
  - q: "Pourquoi héberger un blog sur un Raspberry Pi plutôt que sur Medium ?"
    a: "Parce qu'on maîtrise tout ce que lisent les robots : données structurées, llms.txt, robots.txt, versions Markdown. Sur une plateforme tierce, ces leviers n'existent pas, et on ne voit pas quels robots d'IA passent. Un Pi 4 consomme quelques watts, soit moins de 10 € d'électricité par an, et Cloudflare absorbe la charge."
  - q: "Le fichier llms.txt sert-il vraiment ?"
    a: "C'est une convention récente, pas un standard imposé : certains outils d'IA le lisent, d'autres non. Son coût est nul puisqu'il est généré automatiquement, et il offre aux agents un index propre du site. Le rapport hebdomadaire indique s'il est effectivement consulté."
  - q: "Comment savoir si une IA cite mon site ?"
    a: "Deux signaux dans les journaux du serveur : les visites de robots comme GPTBot, ClaudeBot ou PerplexityBot (lecture), et les visiteurs qui arrivent depuis chatgpt.com, perplexity.ai ou claude.ai (citation suivie d'un clic). Les deux sont comptés chaque semaine."
linkedin: false
linkedin_post: |
  Demandez à ChatGPT de vous recommander un architecte IA. Mon nom n'apparaissait pas.

  Pas faute de contenu : j'écris sur LinkedIn et Medium. Mais je ne maîtrise pas la façon dont les IA lisent ces plateformes, ni si elles les lisent.

  Le vrai problème n'était pas technique. Il fallait une identité cohérente, des contenus structurés pour les machines, et surtout une mesure : est-ce que les robots d'IA passent ?

  La réponse tient dans un Raspberry Pi, un générateur statique de quelques centaines de lignes et un tunnel Cloudflare. Je publie depuis une conversation avec Claude, et chaque lundi je reçois le décompte des visites de GPTBot, ClaudeBot et PerplexityBot.

  Vous mesurez votre visibilité dans les réponses des IA, vous ?

  #GEO #ArchitectureIA #AgenticCoding
---
Quand un recruteur ou un client demande à une IA de lui recommander un architecte IA, la réponse se construit à
partir de ce que les modèles ont lu et de ce qu'ils peuvent récupérer en direct. Pour y figurer, j'ai monté un
blog statique auto-hébergé sur un Raspberry Pi 4 : contenus structurés pour les machines, identité cohérente
sur tous mes profils, et un rapport hebdomadaire qui compte les visites des robots d'IA.

## La situation

J'écris régulièrement sur l'agentic coding et l'architecture IA, sur LinkedIn et sur Medium. Pourtant, quand je
pose la question à un assistant IA, mon nom ne ressort pas. Ces plateformes ne me laissent aucun contrôle sur ce
que lisent les robots, et aucune visibilité sur leur passage.

Pour un architecte IA, c'est un comble : mon métier est de rendre l'information exploitable par des modèles, et
la mienne ne l'est pas.

## Pourquoi c'est plus difficile qu'il n'y paraît

Le GEO (Generative Engine Optimization, l'optimisation pour les moteurs génératifs) n'a pas de tableau de bord
comme la Search Console. Trois difficultés se cumulent.

**L'identité doit être sans ambiguïté.** Un modèle doit pouvoir relier « Romain Vigouroux », « architecte IA »,
mon profil LinkedIn et mes articles à une seule et même personne. Sans balisage explicite, ce lien reste une
supposition.

**Les robots ne se valent pas.** Certains collectent pour l'entraînement (GPTBot, ClaudeBot), d'autres récupèrent
une page en direct pour répondre à une question (ChatGPT-User, Perplexity-User). Un CDN mal réglé peut bloquer les
uns ou les autres sans prévenir.

**La mesure est indirecte.** Une citation dans une réponse d'IA ne laisse aucune trace chez moi, sauf si
l'utilisateur clique. Il faut donc lire les journaux du serveur, pas un script de suivi dans le navigateur — les
robots n'exécutent pas le JavaScript.

## Les pistes écartées

| Option | Pourquoi je l'ai écartée |
|---|---|
| Rester sur Medium | Aucun accès aux données structurées, au robots.txt ni aux journaux |
| CMS type WordPress | Base de données, mises à jour de sécurité, back-office inutile si j'écris depuis Claude |
| Hébergement cloud managé | Fonctionne, mais coût récurrent et moins de contrôle sur les journaux bruts |
| Google Analytics | Ne voit pas les robots, impose un bandeau cookies |

## L'architecture retenue

```text
Conversation avec Claude ──► git push (GitHub)
                                   │
                    toutes les 5 min, le Pi tire le dépôt
                                   ▼
              Raspberry Pi 4 : build.py ──► HTML + JSON-LD + llms.txt + .md
                                   │
                         Caddy (journaux JSON)
                                   │
                       cloudflared (tunnel sortant)
                                   ▼
                    Cloudflare ──► visiteurs, robots d'IA
                                   │
          chaque lundi : rapport (humains, référents IA, robots) par e-mail
```

**Un générateur statique maison**, en Python avec Jinja2. Quelques centaines de lignes que je maîtrise
entièrement, plutôt qu'un framework dont je n'utiliserais pas 90 %. Il produit pour chaque article une page HTML,
une version Markdown brute et un graphe schema.org (`TechArticle`, `Person`, `FAQPage`, `BreadcrumbList`).

**Une seule entité `Person`**, avec un identifiant stable et des liens `sameAs` vers LinkedIn et Medium. Chaque
article y renvoie comme auteur : c'est ce qui permet de relier mes contenus à mon nom.

**Des fichiers pour les machines** : `llms.txt` (index du site pour les agents), `llms-full.txt` (tout le contenu
en un fichier), un `robots.txt` qui autorise explicitement les robots d'IA, un sitemap et un flux RSS complet.

**Un tunnel Cloudflare** plutôt qu'une ouverture de port : le Pi établit une connexion sortante, mon adresse IP
reste cachée, et Cloudflare sert les fichiers statiques depuis son cache.

**Les journaux de Caddy comme source d'analytics.** Un script les lit chaque semaine et sépare trois populations :
les humains, les visiteurs venus d'une IA, et les robots d'IA par nom.

## Ce que ça a donné

Le site est publié par un simple `git push`, sans back-office ni base de données. Chaque article est lisible
par un humain, un moteur de recherche et un agent IA, dans le format qui leur convient.

[À CONFIRMER : premiers chiffres du rapport hebdomadaire après 4 semaines — robots d'IA, référents IA, visiteurs.]

## Ce que je referais différemment

Je commencerais par vérifier les réglages de mon CDN. Cloudflare propose de bloquer les robots d'IA et peut gérer
lui-même le `robots.txt` : pour un site dont le but est justement d'être lu par ces robots, ces options doivent
être désactivées dès le premier jour.
