---
title: "Agentic coding en Monkey C : un cadran de montre et un émetteur Morse pour Garmin"
description: "Deux applications Connect IQ écrites avec Claude Code dans un langage de niche, sous de fortes contraintes d'énergie, d'écran et d'API matérielle."
date: 2026-11-27
slug: applications-garmin-monkey-c-agentic-coding
tags: [Agentic coding, Claude Code, Objets connectés]
keywords: [Garmin, Connect IQ, Monkey C, cadran de montre, Morse, CRR, agentic coding, budget énergétique]
tldr: "Un agent de code est aussi utile dans un langage de niche comme Monkey C, à condition de lui imposer des mesures et des tests : budget d'énergie mesuré dans le simulateur, tests unitaires, prototype matériel avant toute conception. Deux applications en sont sorties : un cadran qui affiche marées et tâches du jour, et un émetteur Morse par la lampe de la montre."
problem: "Construire des applications pour montre Garmin, dans un langage peu documenté, sur un matériel où chaque milliseconde de calcul et chaque pixel comptent."
context: "Deux projets personnels Connect IQ pour fēnix 7, développés en novembre 2026 avec Claude Code."
constraints:
  - "Budget d'énergie strict du cadran en mode économie"
  - "Écrans de 240 à 280 pixels, polices affichées sans lissage"
  - "API de la lampe absente sur certains modèles qui en ont pourtant une"
  - "Aucune donnée ni clé sensible dans le dépôt"
stack: [Monkey C, Connect IQ SDK, Python, Open-Meteo Marine, SwiftUI, Claude Code]
outcome: "Un cadran à trois styles qui tient environ 7,7 ms par seconde de calcul en mode économie, pour une limite de l'ordre de 30 ms, avec 10 tests automatiques ; et un émetteur Morse avec catalogue de 75 messages du CRR, éditeur sur la montre et application compagnon iPhone. [À CONFIRMER : publication sur le Connect IQ Store, essais réels de la LED]"
faq:
  - q: "Peut-on utiliser un agent de code pour programmer une montre Garmin ?"
    a: "Oui. Claude Code a écrit l'essentiel de ces deux applications en Monkey C, le langage de Connect IQ. La clé est de lui donner des moyens de vérifier son travail : compilation pour plusieurs modèles de montre, tests unitaires, mesures dans le simulateur et documents de conception écrits avant le code."
  - q: "Comment afficher les marées sur un cadran Garmin ?"
    a: "Le cadran ne peut pas appeler internet à chaque minute. Une tâche en arrière-plan interroge l'API gratuite Open-Meteo Marine toutes les trois heures, enregistre les pleines et basses mers, et le cadran calcule le niveau actuel entre deux extrêmes. Ces marées sont indicatives et ne servent pas à la navigation."
  - q: "Une montre Garmin peut-elle émettre du Morse avec sa lampe ?"
    a: "Sur les modèles dont la lampe est accessible aux applications, oui, via l'API Connect IQ de la lampe. Ce n'est pas le cas de toutes les montres équipées d'une LED : l'application vérifie donc que la lampe s'allume vraiment et, sinon, bascule sur l'écran blanc et le rétroéclairage. Elle complète les moyens de détresse réglementaires, elle ne les remplace pas."
linkedin: false
linkedin_post: |
  Un agent de code dans un langage que presque personne n'écrit : Monkey C, celui des montres Garmin.

  Deux applications en sont sorties cette semaine. Un cadran « 36 Vues de l'Heure », dont un style inspiré d'Hokusai fait monter la mer avec la marée réelle. Et un émetteur Morse qui fait clignoter la lampe de la montre, avec les messages du certificat de radiotéléphoniste maritime.

  Ce qui a rendu l'agent fiable, ce n'est pas le langage. Ce sont les garde-fous : compiler pour trois modèles avant chaque commit, des tests unitaires, et une mesure du budget d'énergie : 7,7 ms de calcul par seconde pour une limite d'environ 30.

  Pour le Morse, le premier livrable n'était pas l'application, mais un prototype de dix lignes pour vérifier que la lampe répond.

  Quel est le langage le plus inattendu dans lequel vous avez fait travailler un agent ?

  #AgenticCoding #ClaudeCode #Garmin
---
Un agent de code est utile même dans un langage de niche, à condition de lui imposer des mesures et des tests. Avec
Claude Code, j'ai écrit deux applications Connect IQ pour montre Garmin en Monkey C : un cadran qui affiche marées,
météo et tâches du jour sous un budget d'énergie mesuré, et un émetteur de messages Morse par la lampe de la montre.

## La situation

Les montres Garmin se programment en Monkey C, avec le SDK Connect IQ : un langage propre à Garmin, une
documentation dispersée, et un matériel très contraint. Le premier projet est un cadran qui rassemble sur un seul
écran météo, pression, soleil, lune, marées et tâches du jour. Le second émet des messages Morse avec la lampe de la
montre, sur une fēnix 7X Pro.

## Pourquoi c'est plus difficile qu'il n'y paraît

**Le cadran a un budget d'énergie.** En mode économie, la montre coupe l'affichage des secondes si le calcul dépasse
sa limite, de l'ordre de 30 ms en moyenne. Chaque forme dessinée se paie.

**L'écran ne lisse pas les polices ajoutées.** Le fēnix 7 affiche une police personnalisée sans anticrénelage, et
les trois modèles visés vont de 240 à 280 pixels.

**Un cadran ne peut pas interroger internet à volonté.** Les données distantes, marées et tâches, passent par une
tâche en arrière-plan à intervalle fixe.

**L'API de la lampe n'est pas garantie.** Elle n'existe pas sur toutes les montres qui ont une LED ; sur certains
modèles, elle répond « non supporté ». Concevoir l'émetteur Morse sans le vérifier aurait été bâtir sur du sable.

## Les pistes écartées

| Option | Pourquoi je l'ai écartée |
|---|---|
| Laisser l'agent coder sans mesures | Risque de dépasser le budget d'énergie sans le voir, ou de casser un modèle d'écran |
| Utiliser les polices de la montre seulement | Ne permet pas les styles Bauhaus et Hokusai voulus |
| Un clavier de saisie classique pour le Morse | Peu pratique sur une montre pilotée aux boutons ; remplacé par un carrousel de mots |

## L'architecture retenue

### Le cadran « 36 Vues de l'Heure »

```text
ServiceFond (arrière-plan, toutes les 30 min) ─► tâches du jour (Gist) ; marées Open-Meteo (toutes les 3 h)
                     │
Donnees ─► capteurs, météo Garmin, soleil, lune calculée, marées, tâches
                     │
FaceView ─► style choisi : Tactique │ Bauhaus │ Hokusai (mer au niveau de la marée réelle)
```

Trois styles partagent les mêmes données. Le style Hokusai dessine une mer dont le niveau suit la marée réelle
calculée entre la dernière et la prochaine pleine ou basse mer, une course du soleil, et un requin qui avance vers un
bateau au fil des minutes. Les tâches du jour viennent d'un Gist alimenté par un raccourci iPhone.

Pour contourner l'absence de lissage, deux scripts Python génèrent les polices et des chiffres pré-lissés pour
chaque palette. La mesure du simulateur donne environ 7,7 ms de calcul par seconde en mode économie, soit une marge
d'environ quatre fois sur la limite. Dix tests automatiques couvrent la lecture des tâches et le calcul des marées.

### L'émetteur Morse

```text
MorseCodec (texte → segments allumé/éteint, testé) ─► Emitter (machine à états, échéances absolues)
                                                          │
                                  SwitchingOutput ─► lampe LED │ secours : écran blanc + rétroéclairage
```

Le premier livrable était un prototype de quelques lignes pour mesurer la latence et la régularité de la lampe. Le
codec suit la norme de timing PARIS (6 mots par minute par défaut, soit 200 ms par unité). Pour éviter la dérive,
chaque délai vise une échéance absolue plutôt qu'un délai relatif. Si la lampe ne s'allume pas vraiment, la sortie
bascule sur l'écran.

L'application embarque un catalogue de 75 messages du CRR, le Certificat restreint de radiotéléphoniste maritime
(détresse, signaux à une lettre, procédure), un éditeur par « jetons » sur la montre, des réglages synchronisés avec
le téléphone et une application compagnon iPhone en SwiftUI. Elle complète la VHF, la balise de détresse et les feux
réglementaires ; elle ne les remplace pas.

## Ce que ça a donné

Un cadran à trois styles qui fonctionne sur fēnix 7, 7S et 7X avec une marge d'énergie mesurée, et un émetteur
Morse complet côté montre, avec son compagnon iPhone. Les deux dépôts documentent leur maintenance et leur conception.

[À CONFIRMER : publication sur le Connect IQ Store, essais de la LED sur la montre, compilation du compagnon iPhone.]

## Ce que je referais différemment

L'application compagnon iPhone a été écrite sans pouvoir être compilée, faute de Xcode sur la machine de
développement : seul le pont avec le SDK a été vérifié contre ses en-têtes réels. Un agent de code ne remplace pas
une chaîne de compilation ; il faut la lui fournir.
