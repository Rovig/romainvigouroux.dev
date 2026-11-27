---
title: "Erst spezifizieren, dann coden: Personen-Tracking auf der CPU mit YOLO11 und DeepSORT"
description: "Ein System zur Erkennung und Verfolgung von Personen ohne GPU, geschrieben von Claude Code nach einer präzisen technischen Spezifikation: Module, Konfiguration, Randbedingungen."
date: 2026-11-27
slug: personen-tracking-yolo-deepsort-cpu
tags: [Computer Vision, Agentic Coding, Claude Code]
keywords: [YOLO11, DeepSORT, Multi-Object-Tracking, MOT20, CPU, Spezifikation, Agentic Coding]
tldr: "Mit einem Coding-Agenten hängt die Qualität des Ergebnisses vor allem von der Spezifikation ab. Eine Seite, die Verzeichnisstruktur, Zuständigkeit jedes Moduls, Konfiguration und Randbedingungen (nur CPU, Typisierung, Fehlerbehandlung) festlegt, genügte für einen modularen, testbaren Tracker mit YOLO11 und DeepSORT."
problem: "Personen in einem Video erkennen und verfolgen und jeder eine stabile Kennung geben – auf einem Rechner ohne GPU."
context: "Projekt im Modul RCP217 (Objekterkennung und -verfolgung), 2026 in Python 3.13 mit Claude Code umgesetzt."
constraints:
  - "Ausführung nur auf der CPU, ausdrücklich erzwungen"
  - "Keine fest codierten Werte: die gesamte Konfiguration in einer YAML-Datei"
  - "Vorgegebene Architektur, ein Modul pro Zuständigkeit"
  - "Optionales Fine-Tuning auf dem Datensatz MOT20"
stack: [Python, YOLO11, DeepSORT, OpenCV, PyYAML, pytest, Claude Code]
outcome: "Ein Kommandozeilenwerkzeug, das Personen in einem Video oder per Webcam verfolgt, Kennungen und Bahnen einzeichnet, mit Fine-Tuning-Skript für MOT20 und Tests. [ZU BESTÄTIGEN: gemessene FPS auf dem verwendeten Rechner, Ergebnis im Modul]"
faq:
  - q: "Kann man Personen ohne GPU in Echtzeit verfolgen?"
    a: "Ja, wenn man einen leichten Detektor wie YOLO11 Nano wählt und den Tracker entsprechend einstellt. Die Projektdokumentation nennt als erwartete Größenordnung 8 bis 12 Bilder pro Sekunde auf einem Prozessor der Klasse Intel i7 oder Apple M1; der reale Wert hängt von der Videoauflösung ab."
  - q: "Was ist der Unterschied zwischen YOLO und DeepSORT?"
    a: "YOLO erkennt Objekte Bild für Bild, ohne Gedächtnis. DeepSORT verknüpft diese Erkennungen über die Zeit: Es gibt jeder Person eine Kennung und behält sie von Bild zu Bild bei, mithilfe eines Bewegungsmodells und visueller Merkmale zur Wiedererkennung."
  - q: "Wie erzielt man gute Ergebnisse mit einem Coding-Agenten wie Claude Code?"
    a: "Geben Sie ihm eine Spezifikation statt einer Idee: erwartete Verzeichnisstruktur, Zuständigkeit jedes Moduls, Konfigurationsformat, nicht verhandelbare Randbedingungen und Coding-Regeln. Der Agent muss die Architektur nicht mehr erraten, und das Ergebnis lässt sich Punkt für Punkt am Dokument prüfen."
---
Mit einem Coding-Agenten hängt die Qualität des Ergebnisses zuerst von der Qualität der Anfrage ab. Für ein Projekt
zur Personenerkennung und -verfolgung auf der CPU habe ich eine einseitige technische Spezifikation geschrieben, bevor
ich die Umsetzung Claude Code überlassen habe. Das Ergebnis ist ein modulares, konfigurierbares und testbares System
mit YOLO11 und DeepSORT, das ohne GPU läuft.

## Die Ausgangslage

Das Projekt im Modul RCP217 betraf ein System zur Erkennung und Verfolgung: jede Person in einem Video finden und ihr
über die gesamte Sequenz dieselbe Kennung geben. Die Randbedingung stand von Anfang an fest: Alles musste auf der CPU
laufen, ohne Abhängigkeit von einer GPU.

## Warum es schwieriger ist, als es aussieht

**Erkennen reicht nicht.** Ein Detektor wie YOLO arbeitet Bild für Bild, ohne Gedächtnis. Eine Person zu verfolgen
heißt, Erkennungen über die Zeit zu verknüpfen – trotz Überkreuzungen, Verdeckungen und verpasster Erkennungen.

**Die CPU erzwingt Kompromisse.** Ohne GPU zählt jede Entscheidung: Modellgröße, Konfidenzschwelle, Anzahl der
Bestätigungen, bevor eine Bahn gilt. Diese Einstellungen müssen sich ohne Codeänderung anpassen lassen.

**Ein Coding-Agent improvisiert, wenn man ihn lässt.** Eine vage Anfrage erzeugt eine beliebige Architektur, fest
codierte Werte und versteckte GPU-Abhängigkeiten. Der Code funktioniert vielleicht, lässt sich aber nicht warten.

## Die verworfenen Ansätze

| Option | Warum ich sie verworfen habe |
|---|---|
| Den Agenten direkt um „einen Personen-Tracker“ bitten | Unvorhersehbare Architektur, nicht gegen eine schriftliche Erwartung prüfbar |
| Ein größeres Erkennungsmodell (YOLO11 Medium oder Large) | Zu langsam auf der CPU; als Konfigurationsoption behalten |
| Eine GPU-Lösung in der Cloud | Außerhalb der Projektvorgaben |

## Die gewählte Architektur

```text
config.yaml ─► main.py
                 │  Video oder Webcam (OpenCV, Bild für Bild)
                 ▼
        YoloDetector (YOLO11n, CPU erzwungen, nur Klasse „Person“)
                 │  Boxen + Scores
                 ▼
        DeepSortTracker (stabile Kennungen, Wiedererkennung)
                 │  Bahnen
                 ▼
        draw_utils (Boxen, Kennungen, Bahnen) ─► annotiertes Video
```

**Die Spezifikation legte die Verzeichnisstruktur fest**, ein Modul pro Zuständigkeit: Erkennung, Verfolgung,
Geometrie- und Video-Hilfsfunktionen, Visualisierung. Jede Klasse hatte ihre Rolle, ihre Ein- und Ausgaben.

**Die gesamte Konfiguration steht in einer YAML-Datei**: Modell, Konfidenz- und IoU-Schwellen, verfolgte Klassen,
DeepSORT-Parameter (`max_age`, `n_init`, `max_iou_distance`), Videoquelle. Der Wechsel von einem Video zur Webcam oder
von einem Nano- zu einem Medium-Modell braucht keine Codeänderung.

**Die CPU wird ausdrücklich erzwungen**, damit keine Bibliothek standardmäßig nach einer GPU sucht.

**Ein Abschnitt der Spezifikation richtete sich an Claude Code**: Typannotationen für alle Funktionen,
Fehlerbehandlung beim Laden von Dateien und Modellen, vektorisierte NumPy-Operationen statt verschachtelter Schleifen,
automatisches Anlegen des Ausgabeordners.

**Ein separates Trainingsskript** passt den Detektor per Fine-Tuning auf den Datensatz MOT20 an, mit den
Hyperparametern auf der Kommandozeile.

## Was es gebracht hat

Ein Kommandozeilenwerkzeug, das Personen in einem Video oder per Webcam verfolgt, ihre Boxen, Kennungen und Bahnen
einzeichnet und auf MOT20 nachtrainiert werden kann. Die Dokumentation nennt als erwartete Größenordnung 8 bis 12
Bilder pro Sekunde mit YOLO11 Nano auf einem Prozessor der Klasse Intel i7 oder Apple M1.

[ZU BESTÄTIGEN: gemessene Bilder pro Sekunde auf dem verwendeten Rechner, Ergebnis im Modul.]

## Was ich anders machen würde

Die Leistungsangaben im README sind erwartete Werte, keine Messungen. Die Spezifikation hätte ein Skript verlangen
können, das Durchsatz und Tracking-Qualität misst, damit diese Zahlen vom Code erzeugt statt angekündigt werden.
