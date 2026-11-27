---
title: "Generating a satellite image from a building map with Pix2Pix"
description: "A conditional GAN (U-Net + PatchGAN) trained on the Inria Aerial Image Labeling dataset turns a building mask into a satellite image, with four environment styles."
date: 2026-11-27
slug: generating-satellite-images-pix2pix
tags: [Computer vision, AI architecture]
keywords: [Pix2Pix, conditional GAN, U-Net, PatchGAN, satellite image, Inria Aerial Image Labeling, PSNR]
tldr: "Pix2Pix learns the mapping between a building mask and the real satellite image. Most of the work is not the network, which is well known, but everything around it: tile slicing, early stopping on PSNR, resumable training, detecting the architecture from the checkpoint."
problem: "Producing a plausible satellite image from a simple binary map showing where buildings are."
context: "Project for the RCP211 course, in Python, trained on the public Inria Aerial Image Labeling dataset."
constraints:
  - "Images and masks paired tile by tile"
  - "Long training that must be interruptible and resumable"
  - "Run on NVIDIA GPUs, on Apple Silicon Macs or on CPU"
  - "Generate from a hand-drawn map, not only from the dataset"
stack: [Python, PyTorch, Pix2Pix, U-Net, PatchGAN, Weights & Biases]
outcome: "A complete training and generation pipeline, with four environment styles (urban, maritime, nature, default), optional upscaling and unit tests. [TO CONFIRM: PSNR reached, number of epochs, sample images]"
faq:
  - q: "What is Pix2Pix?"
    a: "Pix2Pix is a conditional generative adversarial network: a generator learns to turn an input image into an output image, while a discriminator learns to tell real pairs from generated ones. It is used for image-to-image translation, for example from a map to a photo."
  - q: "Why a PatchGAN discriminator?"
    a: "Instead of judging the whole image, a PatchGAN discriminator judges each small region. This pushes the generator towards realistic local textures, which matters a lot for roofs, roads or vegetation seen from above."
  - q: "When should you stop training a GAN?"
    a: "GAN losses oscillate and do not clearly tell when the model is good. This project measures PSNR on a validation set every five epochs and stops training after twenty validations without improvement, keeping the best model."
---
For the RCP211 course, I trained a Pix2Pix-style conditional GAN that turns a binary building map into a satellite
image. The network is classic, a U-Net generator against a PatchGAN discriminator. The work was mostly about what
surrounds it: tile preparation, stopping criterion, resumable training and generation from a hand-drawn map.

## The situation

The starting point is a black-and-white mask: white where there is a building, black elsewhere. The goal is to turn
it into an image that looks like a real satellite view, with credible roofs, roads and vegetation.

The Inria Aerial Image Labeling dataset provides exactly these pairs: aerial tiles and their building masks.

## Why it's harder than it looks

**A GAN does not tell you when it is done.** Generator and discriminator losses oscillate against each other. You
need an external measure to know whether images are getting better.

**Tiles are too large for the network.** They must be sliced and resized without the image and its mask drifting
apart.

**Training is long.** Two hundred epochs by default, checkpoints of several hundred megabytes: you must be able to
stop and resume without losing work.

**A real input map is not a dataset tile.** A hand-drawn map has neither the size nor the proportions of the training
data.

## The options I ruled out

| Option | Why I ruled it out |
|---|---|
| An unconditional GAN | Generates arbitrary satellite images, ignoring the given map |
| Stopping on the generator loss | Unreliable for a GAN: the loss does not reflect perceived quality |
| A single fixed image size | Too rigid; the project supports 256 and 512 pixels |

## The architecture I chose

```text
Inria tile (image + mask) ─► 4 patches ─► resize (256 or 512)
                                              │
           U-Net generator ◄──────────────────┤ mask
                 │ generated image            │
                 ▼                            ▼
        PatchGAN discriminator  ◄──  real satellite image
                 │
   adversarial loss + 100 × L1 loss ─► PSNR validation every 5 epochs
                                       └─► best model, stop after 20 validations without progress
```

**Data**: 20% of tiles are held out for validation, and each tile provides four patches.

**Training** combines the adversarial loss with an L1 loss weighted by 100, so the generated image stays faithful to
the map. Validation PSNR selects the best model and triggers early stopping.

**Resuming** works from any periodic checkpoint, and computation automatically uses CUDA, an Apple Silicon GPU (MPS)
or the CPU.

**Generation** detects the architecture (256 or 512) from the checkpoint, resizes the input map accordingly, and
offers four environment styles: urban, maritime, nature and default, with optional upscaling.

## What it delivered

A complete pipeline: resumable training, samples generated at each stage, loss plots, optional Weights & Biases
tracking, generation from any map and unit tests.

[TO CONFIRM: validation PSNR reached, number of epochs actually trained, sample images to publish.]

## What I would do differently

PSNR measures pixel-by-pixel fidelity, while the eye mostly judges how realistic the textures are. A perceptual
metric alongside it would help pick the best model. [TO CONFIRM]
