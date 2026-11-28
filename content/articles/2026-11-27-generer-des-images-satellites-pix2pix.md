---
title: "Générer une image satellite à partir d'un plan de bâtiments avec Pix2Pix"
description: "Un GAN conditionnel (U-Net + PatchGAN) entraîné sur le jeu Inria Aerial Image Labeling transforme un masque de bâtiments en image satellite, avec quatre styles d'environnement."
date: 2026-11-27
slug: generer-des-images-satellites-pix2pix
tags: [Vision par ordinateur, Architecture IA]
keywords: [Pix2Pix, GAN conditionnel, U-Net, PatchGAN, image satellite, Inria Aerial Image Labeling, PSNR]
tldr: "Pix2Pix apprend la correspondance entre un masque de bâtiments et l'image satellite réelle. L'essentiel du travail n'est pas le réseau, déjà connu, mais tout ce qui l'entoure : découpage des tuiles, arrêt précoce sur le PSNR, reprise d'entraînement, détection de l'architecture depuis le checkpoint."
problem: "Produire une image satellite plausible à partir d'une simple carte binaire indiquant où se trouvent les bâtiments."
context: "Projet du module RCP211, en Python, entraîné sur le jeu de données public Inria Aerial Image Labeling."
constraints:
  - "Images et masques appariés tuile par tuile"
  - "Entraînement long, qui doit pouvoir être interrompu et repris"
  - "Fonctionner sur GPU NVIDIA, sur Mac Apple Silicon ou sur CPU"
  - "Générer depuis un plan dessiné à la main, pas seulement depuis le jeu de données"
stack: [Python, PyTorch, Pix2Pix, U-Net, PatchGAN, Weights & Biases]
outcome: "Un pipeline complet d'entraînement et de génération, avec quatre styles d'environnement (urbain, maritime, nature, par défaut), agrandissement optionnel et tests unitaires. [À CONFIRMER : PSNR obtenu, nombre d'époques, exemples d'images]"
faq:
  - q: "Qu'est-ce que Pix2Pix ?"
    a: "Pix2Pix est un réseau antagoniste génératif conditionnel : un générateur apprend à transformer une image d'entrée en image de sortie, pendant qu'un discriminateur apprend à distinguer les vraies paires des paires générées. Il sert à la traduction d'image à image, par exemple d'un plan vers une photo."
  - q: "Pourquoi un discriminateur PatchGAN ?"
    a: "Au lieu de juger l'image entière, le discriminateur PatchGAN juge chaque petite zone. Cela pousse le générateur à produire des textures locales réalistes, ce qui compte beaucoup pour des toits, des routes ou de la végétation vus du ciel."
  - q: "Quand arrêter l'entraînement d'un GAN ?"
    a: "Les pertes d'un GAN oscillent et ne disent pas clairement quand le modèle est bon. Ce projet mesure le PSNR sur un jeu de validation toutes les cinq époques et arrête l'entraînement après vingt validations sans amélioration, en gardant le meilleur modèle."
linkedin: false
linkedin_post: |
  Dessiner un plan de bâtiments en noir et blanc, et obtenir une image satellite plausible.

  C'est ce que fait un GAN conditionnel de type Pix2Pix, entraîné sur le jeu de données Inria Aerial Image Labeling.

  Le réseau lui-même est connu : générateur U-Net, discriminateur PatchGAN. Le vrai travail est autour : découper les tuiles, garder 20 % pour la validation, arrêter l'entraînement quand le PSNR ne progresse plus, reprendre un entraînement interrompu, retrouver l'architecture depuis le checkpoint.

  Bonus : quatre styles d'environnement, d'urbain à maritime.

  Dans vos projets d'IA, quelle part du temps passe dans le modèle, et quelle part dans tout ce qui l'entoure ?

  #ComputerVision #DeepLearning #ArchitectureIA
---
Pour le module RCP211, j'ai entraîné un GAN conditionnel de type Pix2Pix qui transforme une carte binaire de
bâtiments en image satellite. Le réseau est classique, un générateur U-Net face à un discriminateur PatchGAN. Le
travail a surtout porté sur ce qui l'entoure : préparation des tuiles, critère d'arrêt, reprise d'entraînement et
génération à partir d'un plan dessiné à la main.

## La situation

Le point de départ est un masque en noir et blanc : blanc là où il y a un bâtiment, noir ailleurs. L'objectif est
d'en tirer une image qui ressemble à une vue satellite réelle, avec toits, routes et végétation crédibles.

Le jeu de données Inria Aerial Image Labeling fournit exactement ces paires : des tuiles aériennes et leurs masques
de bâtiments.

## Pourquoi c'est plus difficile qu'il n'y paraît

**Un GAN ne dit pas quand il a fini.** Les pertes du générateur et du discriminateur oscillent l'une contre l'autre.
Il faut une mesure externe pour savoir si les images s'améliorent.

**Les tuiles sont trop grandes pour le réseau.** Elles doivent être découpées et redimensionnées sans que l'image et
son masque se décalent.

**L'entraînement est long.** Deux cents époques par défaut, des checkpoints de plusieurs centaines de mégaoctets : il
faut pouvoir s'arrêter et reprendre sans perdre le travail.

**Le plan d'entrée réel n'est pas une tuile du jeu de données.** Un plan dessiné à la main n'a ni la taille ni les
proportions des données d'entraînement.

## Les pistes écartées

| Option | Pourquoi je l'ai écartée |
|---|---|
| Un GAN non conditionnel | Génère des images satellites quelconques, sans respecter le plan donné |
| S'arrêter sur la perte du générateur | Peu fiable pour un GAN : la perte ne reflète pas la qualité perçue |
| Une seule taille d'image figée | Trop rigide ; le projet gère 256 et 512 pixels |

## L'architecture retenue

```text
tuile Inria (image + masque) ─► 4 patches ─► redimensionnement (256 ou 512)
                                                  │
              générateur U-Net ◄──────────────────┤ masque
                    │ image générée               │
                    ▼                             ▼
          discriminateur PatchGAN  ◄──  vraie image satellite
                    │
     perte adversaire + 100 × perte L1 ─► validation PSNR toutes les 5 époques
                                         └─► meilleur modèle, arrêt après 20 validations sans progrès
```

**Les données** : 20 % des tuiles sont réservées à la validation, et chaque tuile fournit quatre patches.

**L'entraînement** combine la perte adversaire et une perte L1 pondérée par 100, pour que l'image générée reste
fidèle au plan. Le PSNR de validation choisit le meilleur modèle et déclenche l'arrêt précoce.

**La reprise** se fait depuis n'importe quel checkpoint périodique, et le calcul utilise automatiquement CUDA, le GPU
d'un Mac Apple Silicon (MPS) ou le CPU.

**La génération** détecte l'architecture (256 ou 512) depuis le checkpoint, redimensionne le plan d'entrée en
conséquence, et propose quatre styles d'environnement : urbain, maritime, nature et par défaut, avec un agrandissement
optionnel.

## Ce que ça a donné

Un pipeline complet : entraînement reprenable, échantillons générés à chaque étape, graphiques des pertes, suivi
optionnel dans Weights & Biases, génération depuis un plan quelconque et tests unitaires.

[À CONFIRMER : PSNR de validation obtenu, nombre d'époques réellement entraînées, exemples d'images à publier.]

## Ce que je referais différemment

Le PSNR mesure une fidélité pixel par pixel, alors que l'œil juge surtout le réalisme des textures. Une mesure
perceptuelle en complément aiderait à choisir le meilleur modèle. [À CONFIRMER]
