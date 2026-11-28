---
title: "Spécifier avant de coder : suivre des personnes sur CPU avec YOLO11 et DeepSORT"
description: "Un système de détection et de suivi de personnes sans GPU, écrit par Claude Code à partir d'une spécification technique précise : modules, configuration, contraintes."
date: 2026-11-27
slug: suivi-de-personnes-yolo-deepsort-cpu
tags: [Vision par ordinateur, Agentic coding, Claude Code]
keywords: [YOLO11, DeepSORT, suivi multi-objets, MOT20, CPU, spécification, agentic coding]
tldr: "Avec un agent de code, la qualité du résultat dépend surtout de la spécification. Une page qui fixe l'arborescence, les responsabilités de chaque module, la configuration et les contraintes (CPU seul, typage, gestion d'erreurs) a suffi à obtenir un tracker YOLO11 + DeepSORT modulaire et testable."
problem: "Détecter et suivre des personnes dans une vidéo, en leur gardant un identifiant stable, sur une machine sans GPU."
context: "Projet du module RCP217 (détection et suivi d'objets), réalisé en 2026 en Python 3.13 avec Claude Code."
constraints:
  - "Exécution sur CPU uniquement, forcée explicitement"
  - "Aucune valeur en dur : toute la configuration dans un fichier YAML"
  - "Architecture imposée, un module par responsabilité"
  - "Fine-tuning possible sur le jeu de données MOT20"
stack: [Python, YOLO11, DeepSORT, OpenCV, PyYAML, pytest, Claude Code]
outcome: "Un outil en ligne de commande qui suit les personnes dans une vidéo ou depuis une webcam, avec identifiants et trajectoires dessinés, un script de fine-tuning sur MOT20 et des tests. [À CONFIRMER : FPS mesurés sur la machine utilisée, résultat obtenu au module]"
faq:
  - q: "Peut-on faire du suivi de personnes en temps réel sans GPU ?"
    a: "Oui, à condition de choisir un détecteur léger comme YOLO11 Nano et de régler le tracker en conséquence. La documentation du projet donne comme ordre de grandeur attendu 8 à 12 images par seconde sur un processeur de type Intel i7 ou Apple M1 ; le chiffre réel dépend de la résolution de la vidéo."
  - q: "Quelle est la différence entre YOLO et DeepSORT ?"
    a: "YOLO détecte les objets image par image, sans mémoire. DeepSORT relie ces détections dans le temps : il attribue à chaque personne un identifiant et le conserve d'une image à l'autre grâce à un modèle de mouvement et à des caractéristiques visuelles de ré-identification."
  - q: "Comment bien utiliser un agent de code comme Claude Code ?"
    a: "En lui donnant une spécification plutôt qu'une idée : arborescence attendue, responsabilité de chaque module, format de configuration, contraintes non négociables et règles de code. L'agent n'a plus à deviner l'architecture, et le résultat se vérifie point par point contre le document."
linkedin: false
linkedin_post: |
  « Fais-moi un tracker de personnes » : c'est la pire demande qu'on puisse faire à un agent de code.

  Pour un module de vision par ordinateur, j'ai écrit une page de spécification avant la première ligne de code : arborescence imposée, une responsabilité par module, configuration YAML sans aucune valeur en dur, CPU uniquement, typage obligatoire.

  Claude Code a ensuite produit un système YOLO11 + DeepSORT qui suit les personnes dans une vidéo ou depuis une webcam, avec fine-tuning sur MOT20.

  Le plus intéressant n'est pas le code généré. C'est que le résultat se relit contre le document, point par point.

  Vous écrivez une spécification avant de lancer un agent ?

  #AgenticCoding #ComputerVision #ClaudeCode
---
Avec un agent de code, la qualité du résultat dépend d'abord de la qualité de la demande. Pour un projet de
détection et de suivi de personnes sur CPU, j'ai écrit une spécification technique d'une page avant de confier
l'implémentation à Claude Code. Le résultat est un système YOLO11 + DeepSORT modulaire, configurable et testable,
qui tourne sans GPU.

## La situation

Le projet du module RCP217 portait sur un système de détection et de suivi : repérer chaque personne dans une vidéo
et lui garder le même identifiant tout au long de la séquence. Contrainte posée dès le départ : tout devait tourner
sur CPU, sans dépendance à un GPU.

## Pourquoi c'est plus difficile qu'il n'y paraît

**Détecter ne suffit pas.** Un détecteur comme YOLO travaille image par image, sans mémoire. Suivre une personne
suppose de relier les détections dans le temps, malgré les croisements, les occlusions et les détections manquées.

**Le CPU impose des compromis.** Sans GPU, chaque choix compte : taille du modèle, seuil de confiance, nombre de
confirmations avant de valider une trajectoire. Ces réglages doivent pouvoir changer sans toucher au code.

**Un agent de code improvise si on le laisse faire.** Une demande vague produit une architecture arbitraire, des
valeurs en dur et des dépendances GPU implicites. Le code fonctionne peut-être, mais il ne se maintient pas.

## Les pistes écartées

| Option | Pourquoi je l'ai écartée |
|---|---|
| Demander directement « un tracker de personnes » à l'agent | Architecture imprévisible, impossible à vérifier contre une attente écrite |
| Un modèle de détection plus gros (YOLO11 medium ou large) | Trop lent sur CPU ; gardé comme option de configuration |
| Une solution sur GPU dans le cloud | Hors des contraintes du projet |

## L'architecture retenue

```text
config.yaml ─► main.py
                 │  vidéo ou webcam (OpenCV, lecture image par image)
                 ▼
        YoloDetector (YOLO11n, CPU forcé, classe « personne » seule)
                 │  boîtes + scores
                 ▼
        DeepSortTracker (identifiants stables, ré-identification)
                 │  pistes
                 ▼
        draw_utils (boîtes, identifiants, trajectoires) ─► vidéo annotée
```

**La spécification fixait l'arborescence**, un module par responsabilité : détection, suivi, utilitaires de
géométrie et de vidéo, visualisation. Chaque classe y avait son rôle, ses entrées et ses sorties.

**Toute la configuration est dans un YAML** : modèle, seuils de confiance et d'IoU, classes suivies, paramètres de
DeepSORT (`max_age`, `n_init`, `max_iou_distance`), source vidéo. Passer d'une vidéo à la webcam ou d'un modèle
Nano à un modèle Medium se fait sans toucher au code.

**Le CPU est forcé explicitement**, pour qu'aucune bibliothèque ne cherche un GPU par défaut.

**Une section de la spécification s'adressait à Claude Code** : typage obligatoire de toutes les fonctions,
gestion d'erreurs sur le chargement des fichiers et des modèles, opérations vectorielles NumPy plutôt que des
boucles imbriquées, création automatique du dossier de sortie.

**Un script d'entraînement séparé** permet d'affiner le détecteur sur le jeu de données MOT20, avec ses
hyperparamètres en ligne de commande.

## Ce que ça a donné

Un outil en ligne de commande qui suit les personnes dans une vidéo ou depuis une webcam, dessine leurs boîtes,
identifiants et trajectoires, et peut être affiné sur MOT20. La documentation donne comme ordre de grandeur attendu
8 à 12 images par seconde avec YOLO11 Nano sur un processeur de type Intel i7 ou Apple M1.

[À CONFIRMER : images par seconde mesurées sur la machine utilisée, résultat obtenu au module.]

## Ce que je referais différemment

Les performances du README sont des valeurs attendues, pas des mesures. La spécification aurait pu exiger un script
de mesure du débit et de la qualité du suivi, pour que ces chiffres soient produits par le code plutôt qu'annoncés.
