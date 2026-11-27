---
title: "Voir les ruptures de carburant autour de soi avec les données ouvertes de l'État"
description: "Un widget macOS qui affiche sur une carte IGN la disponibilité et le prix des carburants, à partir du flux officiel mis à jour toutes les 10 minutes, sans clé API ni dépendance."
date: 2026-11-27
slug: disponibilite-carburants-donnees-ouvertes
tags: [Données ouvertes, Architecture logicielle, Agentic coding]
keywords: [prix des carburants, open data, data.economie.gouv.fr, IGN, Übersicht, Node.js, architecture hexagonale]
tldr: "Le flux officiel des prix des carburants indique aussi les ruptures, station par station. Un cœur Node.js sans dépendance transforme ce flux en un JSON d'affichage, et un widget de bureau se contente de le dessiner sur une carte IGN. Aucune clé API, aucun serveur."
problem: "Savoir, avant de prendre la voiture, quelles stations autour de soi ont encore le carburant voulu et à quel prix."
context: "Outil personnel open source pour macOS, construit en agentic coding avec Claude Code."
constraints:
  - "Uniquement des données officielles et ouvertes, sans clé API"
  - "Aucune dépendance npm à installer"
  - "Logique testable sans l'environnement d'affichage"
  - "Ne jamais publier la position du domicile dans un dépôt public"
stack: [Node.js, React (JSX), Übersicht, API prix-carburants, Géoplateforme IGN, geo.api.gouv.fr, Claude Code]
outcome: "Un widget de bureau qui affiche les stations proches ou une liste choisie, avec pastilles de disponibilité, prix, carte interactive, recherche par ville, code postal ou station, et un lanceur Finder. [À CONFIRMER : usage réel, nombre d'utilisateurs]"
faq:
  - q: "Où trouver la disponibilité des carburants en temps réel en France ?"
    a: "Dans le jeu de données « Prix des carburants en France – flux instantané v2 » publié sur data.economie.gouv.fr sous Licence Ouverte. Il indique, station par station, les prix et les ruptures, et il est mis à jour toutes les dix minutes. Aucune clé n'est nécessaire pour l'interroger."
  - q: "Pourquoi le widget n'affiche-t-il pas le nom des stations ?"
    a: "Parce que le jeu de données officiel ne contient ni le nom ni l'enseigne des stations. Le widget affiche donc l'adresse, la ville et l'identifiant officiel de la station, qui permet de la retrouver sur prix-carburants.gouv.fr."
  - q: "Pourquoi séparer la logique de l'affichage dans un widget aussi petit ?"
    a: "Pour pouvoir tester toutes les règles, disponibilité, recherche, calcul de distance, sans lancer l'environnement graphique. Le cœur est en Node.js pur et produit un JSON ; l'affichage se contente de le dessiner. Les tests tournent avec le lanceur intégré à Node, sans aucune dépendance."
linkedin: false
linkedin_post: |
  Le flux officiel des prix des carburants contient une information que peu de gens exploitent : les ruptures, station par station, mises à jour toutes les 10 minutes.

  J'en ai fait un widget de bureau macOS : une carte IGN avec des pastilles vertes, orange ou rouges selon ce qui reste à la pompe, et les prix à côté.

  Aucune clé API. Aucune dépendance npm. Toute la logique vit dans un cœur Node.js testable seul ; le widget ne fait que dessiner un JSON.

  Petite leçon des données ouvertes : le jeu de données ne contient pas le nom des stations. On affiche l'adresse.

  Quelles données publiques vous rendent service au quotidien ?

  #OpenData #NodeJS #AgenticCoding
---
Le flux officiel des prix des carburants publie aussi les ruptures, station par station, toutes les dix minutes.
J'en ai fait pump-radar, un widget de bureau macOS qui affiche sur une carte IGN la disponibilité et le prix des
carburants autour de soi, sans clé API, sans serveur et sans dépendance npm. Le besoin est simple ; l'intérêt est
dans la séparation stricte entre les données, la logique et l'affichage.

## La situation

Avant de prendre la voiture, la question n'est pas seulement « où est-ce le moins cher ? » mais « où reste-t-il le
carburant que je veux ? ». Les sites officiels répondent station par station ; le widget donne la réponse d'un
coup d'œil, sur le bureau. [À CONFIRMER : contexte qui a motivé le projet]

## Pourquoi c'est plus difficile qu'il n'y paraît

**Les données sont incomplètes à leur manière.** Le flux officiel donne prix et ruptures, mais ni le nom ni
l'enseigne des stations. Certains prix datent de plusieurs jours.

**Un widget de bureau est un environnement contraint.** Übersicht exécute une commande et affiche son résultat : pas
de serveur, peu d'outils de test, rechargement à chaque modification de fichier.

**Le dépôt est public.** La configuration par défaut contient un point de référence géographique ; il ne doit jamais
s'agir du domicile.

## Les pistes écartées

| Option | Pourquoi je l'ai écartée |
|---|---|
| Une application mobile tierce | Pas de vue sur le bureau, données et logique hors de mon contrôle |
| Une API commerciale de carburants | Clé, quota et coût pour une donnée publique et gratuite |
| Tout coder dans le composant du widget | Logique impossible à tester sans lancer l'affichage |

## L'architecture retenue

```text
config.json ─► core/main.mjs ─► adapters : API prix-carburants, API communes, tuiles IGN, position
                     │
                     ├─► domain : Station, règles de disponibilité
                     ├─► app : tableau de bord, recherche, suggestions de communes
                     ▼
               JSON « vue » sur la sortie standard ─► index.jsx (Übersicht) dessine la carte et la liste
```

**Les adaptateurs** isolent chaque source : le flux des prix et des ruptures, l'API Découpage administratif pour les
communes, la Géoplateforme IGN pour le fond de carte. Toutes sont publiques et sans clé.

**Le domaine** porte les règles métier : une pastille verte quand tous les carburants suivis sont disponibles, orange
en cas de rupture partielle, rouge quand rien n'est disponible, grise quand la station ne vend aucun d'eux. Un prix
de plus de 24 heures est grisé.

**La couche applicative** construit la vue : stations dans un rayon donné, liste fixe de stations, recherche par
ville avec suggestions, par code postal ou par identifiant.

**L'affichage** ne fait que dessiner le JSON reçu : carte interactive (glisser, zoomer, bulle par station avec lien
d'itinéraire), liste et menu. Toute la logique se teste avec le lanceur de tests intégré à Node, sans rien installer.

Un petit lanceur Finder, `Essence.app`, installe le lien du widget s'il manque, démarre Übersicht et trace chaque
lancement dans un journal.

## Ce que ça a donné

Un widget publié en open source sur GitHub, avec une documentation d'installation, un
document de conception détaillé et une suite de tests sans dépendance.

[À CONFIRMER : usage réel, retours d'utilisateurs.]

## Ce que je referais différemment

La carte interactive n'est pas couverte par les tests automatiques : le README décrit une recette manuelle. Extraire
davantage de la logique de la carte vers le cœur testable réduirait cette part de vérification à la main.
