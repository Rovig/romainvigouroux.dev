---
title: "Aus einem Gebäudeplan ein Satellitenbild erzeugen – mit Pix2Pix"
description: "Ein bedingtes GAN (U-Net + PatchGAN), trainiert auf dem Datensatz Inria Aerial Image Labeling, verwandelt eine Gebäudemaske in ein Satellitenbild, mit vier Umgebungsstilen."
date: 2026-11-27
slug: satellitenbilder-erzeugen-pix2pix
tags: [Computer Vision, KI-Architektur]
keywords: [Pix2Pix, bedingtes GAN, U-Net, PatchGAN, Satellitenbild, Inria Aerial Image Labeling, PSNR]
tldr: "Pix2Pix lernt die Zuordnung zwischen einer Gebäudemaske und dem echten Satellitenbild. Die meiste Arbeit steckt nicht im bekannten Netz, sondern in allem drumherum: Zerlegung der Kacheln, frühes Stoppen anhand des PSNR, fortsetzbares Training, Erkennung der Architektur aus dem Checkpoint."
problem: "Aus einer einfachen binären Karte, die zeigt, wo Gebäude stehen, ein plausibles Satellitenbild erzeugen."
context: "Projekt im Modul RCP211, in Python, trainiert auf dem öffentlichen Datensatz Inria Aerial Image Labeling."
constraints:
  - "Bilder und Masken kachelweise gepaart"
  - "Langes Training, das unterbrochen und fortgesetzt werden kann"
  - "Lauffähig auf NVIDIA-GPUs, auf Macs mit Apple Silicon oder auf der CPU"
  - "Erzeugung aus einem handgezeichneten Plan, nicht nur aus dem Datensatz"
stack: [Python, PyTorch, Pix2Pix, U-Net, PatchGAN, Weights & Biases]
outcome: "Eine vollständige Trainings- und Erzeugungs-Pipeline mit vier Umgebungsstilen (städtisch, maritim, Natur, Standard), optionaler Vergrößerung und Unit-Tests. [ZU BESTÄTIGEN: erreichter PSNR, Anzahl der Epochen, Beispielbilder]"
faq:
  - q: "Was ist Pix2Pix?"
    a: "Pix2Pix ist ein bedingtes generatives gegnerisches Netz: Ein Generator lernt, ein Eingabebild in ein Ausgabebild zu verwandeln, während ein Diskriminator lernt, echte von erzeugten Paaren zu unterscheiden. Es dient der Bild-zu-Bild-Übersetzung, etwa von einer Karte zu einem Foto."
  - q: "Warum ein PatchGAN-Diskriminator?"
    a: "Statt das ganze Bild zu beurteilen, bewertet ein PatchGAN-Diskriminator jeden kleinen Bereich. Das treibt den Generator zu realistischen lokalen Texturen, was bei Dächern, Straßen und Vegetation aus der Luft viel ausmacht."
  - q: "Wann sollte man das Training eines GAN beenden?"
    a: "Die Verluste eines GAN schwanken und zeigen nicht klar, wann das Modell gut ist. Dieses Projekt misst alle fünf Epochen den PSNR auf einem Validierungsdatensatz und beendet das Training nach zwanzig Validierungen ohne Verbesserung, wobei das beste Modell erhalten bleibt."
---
Für das Modul RCP211 habe ich ein bedingtes GAN nach dem Vorbild von Pix2Pix trainiert, das eine binäre Gebäudekarte
in ein Satellitenbild verwandelt. Das Netz ist klassisch, ein U-Net-Generator gegen einen PatchGAN-Diskriminator. Die
Arbeit drehte sich vor allem um das Drumherum: Aufbereitung der Kacheln, Abbruchkriterium, fortsetzbares Training und
Erzeugung aus einem handgezeichneten Plan.

## Die Ausgangslage

Ausgangspunkt ist eine Schwarz-Weiß-Maske: weiß, wo ein Gebäude steht, schwarz überall sonst. Ziel ist ein Bild, das
wie eine echte Satellitenaufnahme aussieht, mit glaubwürdigen Dächern, Straßen und Vegetation.

Der Datensatz Inria Aerial Image Labeling liefert genau diese Paare: Luftbildkacheln und ihre Gebäudemasken.

## Warum es schwieriger ist, als es aussieht

**Ein GAN sagt nicht, wann es fertig ist.** Die Verluste von Generator und Diskriminator schwanken gegeneinander. Man
braucht ein externes Maß, um zu wissen, ob die Bilder besser werden.

**Die Kacheln sind zu groß für das Netz.** Sie müssen zerlegt und skaliert werden, ohne dass Bild und Maske
auseinanderlaufen.

**Das Training dauert lange.** Standardmäßig zweihundert Epochen, Checkpoints von mehreren hundert Megabyte: Man muss
anhalten und fortsetzen können, ohne Arbeit zu verlieren.

**Ein echter Eingabeplan ist keine Kachel aus dem Datensatz.** Ein handgezeichneter Plan hat weder die Größe noch die
Proportionen der Trainingsdaten.

## Die verworfenen Ansätze

| Option | Warum ich sie verworfen habe |
|---|---|
| Ein unbedingtes GAN | Erzeugt beliebige Satellitenbilder, ohne den vorgegebenen Plan zu beachten |
| Abbruch anhand des Generatorverlusts | Bei einem GAN unzuverlässig: Der Verlust spiegelt die wahrgenommene Qualität nicht wider |
| Eine einzige feste Bildgröße | Zu starr; das Projekt unterstützt 256 und 512 Pixel |

## Die gewählte Architektur

```text
Inria-Kachel (Bild + Maske) ─► 4 Ausschnitte ─► Skalierung (256 oder 512)
                                                    │
              U-Net-Generator ◄─────────────────────┤ Maske
                    │ erzeugtes Bild                │
                    ▼                               ▼
         PatchGAN-Diskriminator  ◄──  echtes Satellitenbild
                    │
  gegnerischer Verlust + 100 × L1-Verlust ─► PSNR-Validierung alle 5 Epochen
                                            └─► bestes Modell, Abbruch nach 20 Validierungen ohne Fortschritt
```

**Die Daten**: 20 % der Kacheln sind für die Validierung reserviert, und jede Kachel liefert vier Ausschnitte.

**Das Training** kombiniert den gegnerischen Verlust mit einem mit 100 gewichteten L1-Verlust, damit das erzeugte Bild
dem Plan treu bleibt. Der Validierungs-PSNR wählt das beste Modell und löst den frühen Abbruch aus.

**Die Fortsetzung** funktioniert von jedem periodischen Checkpoint aus, und die Berechnung nutzt automatisch CUDA, die
GPU eines Macs mit Apple Silicon (MPS) oder die CPU.

**Die Erzeugung** erkennt die Architektur (256 oder 512) aus dem Checkpoint, skaliert den Eingabeplan entsprechend und
bietet vier Umgebungsstile: städtisch, maritim, Natur und Standard, mit optionaler Vergrößerung.

## Was es gebracht hat

Eine vollständige Pipeline: fortsetzbares Training, in jeder Phase erzeugte Beispiele, Verlustdiagramme, optionale
Verfolgung in Weights & Biases, Erzeugung aus beliebigen Plänen und Unit-Tests.

[ZU BESTÄTIGEN: erreichter Validierungs-PSNR, tatsächlich trainierte Epochen, zu veröffentlichende Beispielbilder.]

## Was ich anders machen würde

Der PSNR misst die Treue Pixel für Pixel, während das Auge vor allem den Realismus der Texturen beurteilt. Eine
zusätzliche perzeptuelle Metrik würde helfen, das beste Modell zu wählen. [ZU BESTÄTIGEN]
