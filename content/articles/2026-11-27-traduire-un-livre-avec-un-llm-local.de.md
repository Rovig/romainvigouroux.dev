---
title: "Ein ganzes Buch mit einem lokalen LLM oder jeder beliebigen API übersetzen"
description: "Stridon übersetzt EPUBs, bebilderte PDFs, Untertitel und Webartikel mit Ollama, Claude, GPT oder DeepL, erhält die Struktur des Dokuments und macht dort weiter, wo es aufgehört hat."
date: 2026-11-27
slug: ein-buch-mit-einem-lokalen-llm-uebersetzen
tags: [Lokale LLMs, KI-Architektur, Agentic Coding]
keywords: [maschinelle Übersetzung, Ollama, LLM, EPUB, PDF, Claude, Open Source]
tldr: "Ein Buch mit einem LLM zu übersetzen ist kein Prompt-Problem, sondern ein Dokument-Problem: zerlegen, ohne die Struktur zu zerstören, Kontext bewahren, Unterbrechungen überstehen und das Modell wechseln können. Stridon trennt Engine, Cache, Übersetzer und Formate, um jeden dieser Punkte zu lösen."
problem: "Ein Buch oder ein langes bebildertes PDF mit KI übersetzen, ohne das Layout zu verlieren und ohne bei der ersten Unterbrechung neu anzufangen."
context: "Persönliches Werkzeug, als Open Source veröffentlicht, über die Kommandozeile genutzt, mit kostenlosen lokalen Modellen oder kostenpflichtigen APIs."
constraints:
  - "Struktur erhalten: Kapitel, Überschriften, Bilder, Fußnoten, zeitcodierte Untertitel"
  - "Mit einem kostenlosen lokalen Modell ebenso funktionieren wie mit rund fünfzehn Diensten"
  - "Eine unterbrochene Übersetzung fortsetzen, ohne Erledigtes erneut zu bezahlen"
  - "Namen und Ton von Kapitel zu Kapitel einheitlich halten"
stack: [Python, Ollama, Claude, OpenAI, PyMuPDF, BeautifulSoup, Docker, Claude Code]
outcome: "Ein Werkzeug in Version 1.0 auf GitHub, mit Dokumentation auf Französisch, Englisch und Chinesisch, automatisierten Tests und einem Docker-Image. [ZU BESTÄTIGEN: übersetzter Umfang, bevorzugtes lokales Modell, Dauer für ein Buch]"
faq:
  - q: "Kann man ein Buch mit einem kostenlosen lokalen LLM übersetzen?"
    a: "Ja. Stridon nutzt standardmäßig Ollama auf dem eigenen Rechner, ohne Schlüssel und ohne Kosten. Derselbe Befehl funktioniert mit Claude, GPT, Gemini, Mistral, DeepL oder Google Übersetzer, wenn man eine Option ändert – so lässt sich die Qualität am selben Text vergleichen."
  - q: "Wie verliert man eine lange Übersetzung bei einer Unterbrechung nicht?"
    a: "Jede übersetzte Passage wird gespeichert, sobald sie eintrifft. Bricht die Übersetzung ab, startet man denselben Befehl erneut: Bereits übersetzte Passagen werden wiederverwendet und nicht noch einmal an den Dienst gesendet. Ein Wechsel der Darstellung, zweisprachig oder nicht, kostet keine neue Anfrage."
  - q: "Wie bleiben Figurennamen in einer KI-Übersetzung einheitlich?"
    a: "Indem man dem Modell die zuletzt übersetzten Absätze als Kontext mitschickt. Die Kapitel werden dann der Reihe nach übersetzt, und das Modell sieht, wie ein Name oder Begriff kurz zuvor wiedergegeben wurde."
  - q: "Was macht Stridon mit PDFs, die Bilder enthalten?"
    a: "Es baut ein neues PDF, in dem die Übersetzung von Seite zu Seite fließt, die Bilder an ihrem Platz bleiben und Überschriften größer dargestellt werden. Im zweisprachigen Modus ergibt jede Originalseite eine Seite mit dem Original in Schwarz und der Übersetzung in Blau."
---
Ein Buch mit einem LLM zu übersetzen ist vor allem ein Dokument-Problem: zerlegen, ohne die Struktur zu zerstören,
Einheitlichkeit über Kapitel hinweg wahren, Unterbrechungen überstehen und das Modell wechseln können. Ich habe
Stridon geschrieben, ein Open-Source-Kommandozeilenwerkzeug, das EPUBs, bebilderte PDFs, Markdown, Untertitel und
Webartikel mit einem lokalen Modell über Ollama oder rund fünfzehn Diensten übersetzt und dort weitermacht, wo es
aufgehört hat.

## Die Ausgangslage

Ein DRM-freies Buch, einen PDF-Bericht voller Abbildungen oder einen Webartikel in einer anderen Sprache als der
Originalsprache zu lesen, ist nach wie vor mühsam. Online-Dokumentübersetzer verarbeiten eine Datei nach der anderen,
verlieren oft das Layout und schreiben ihre eigene Engine vor. [ZU BESTÄTIGEN: der persönliche oder Kundenbedarf, der
das Projekt ausgelöst hat]

LLMs übersetzen heute weit besser als noch vor wenigen Jahren, auch lokal. Aber ein in einen Chat kopiertes Kapitel
ergibt noch kein übersetztes Buch.

## Warum es schwieriger ist, als es aussieht

**Die Struktur ist empfindlich.** Ein EPUB mischt Absätze, Überschriften, Fußnotenverweise, Code und Bildunterschriften.
Ein PDF hat überhaupt keine Absätze, nur Textblöcke auf Seiten. Eine SRT-Datei verlangt, dass Nummern und Zeitstempel
unverändert bleiben.

**Lange Übersetzungen werden unterbrochen.** Über Hunderte Seiten hinweg gibt es einen Netzwerkausfall, ein
überschrittenes Kontingent oder eine gelegentliche Verweigerung des Modells. Von vorn anzufangen kostet Zeit und Geld.

**Zwischen Anfragen geht die Einheitlichkeit verloren.** Jede Anfrage kennt die vorherigen nicht: Ein Eigenname oder
Fachbegriff kann von Kapitel zu Kapitel anders übersetzt werden.

**Kein Modell gewinnt überall.** Ein lokales Modell ist kostenlos und privat, eine API oft besser oder schneller, ein
spezialisierter Dienst wie DeepL glänzt bei bestimmten Sprachpaaren. Man muss wählen können.

## Die verworfenen Ansätze

| Option | Warum ich sie verworfen habe |
|---|---|
| Kopieren und Einfügen in einen KI-Assistenten | Skaliert nicht auf ein Buch, verliert die Struktur |
| Ein Online-Dienst für Dokumentübersetzung | Eine einzige Engine, oft beschädigtes Layout, Dokumente gehen an Dritte |
| Ein Skript, das an eine einzige API gebunden ist | Kein Vergleich und kein Wechsel zu einem lokalen Modell möglich |

## Die gewählte Architektur

```text
Datei ─► Format (EPUB, PDF, TXT, MD, SRT, Web) ─► Passagen
                                                    │
                Übersetzungs-Cache ◄───────────────►│ Engine: Bündelung, Kontext, Parallelität
                                                    │
               austauschbarer Übersetzer ◄──────────┘ Ollama, Claude, OpenAI, Gemini, Mistral, DeepL…
                                                    │
                                 Format ─► neu aufgebautes Dokument (übersetzt oder zweisprachig)
```

**Die Formate** wissen, wie man übersetzbare Passagen herauslöst und das Dokument wieder aufbaut: ausgewählte Tags im
EPUB, wieder eingesetzte Bilder im PDF, erhaltene Zeitstempel im SRT, unveränderter Code im Markdown.

**Die Engine** bündelt Absätze nach Blöcken oder Token-Anzahl, sendet mehrere Anfragen parallel und kann dem Modell
die zuletzt übersetzten Absätze mitgeben, damit Ton und Namen einheitlich bleiben.

**Der Cache** speichert jede Passage, sobald sie übersetzt ist. Derselbe Befehl setzt dort fort, wo es aufgehört hat;
eine Option übersetzt eine einzelne Passage neu und baut die ganze Datei aus dem Cache wieder auf.

**Die Übersetzer** teilen sich eine Schnittstelle. Ollama ist der Standarddienst, lokal und ohne Schlüssel. Jeder
OpenAI-kompatible Server (LM Studio, vLLM, ein Unternehmens-Gateway) wird in einer einfachen JSON-Datei deklariert.
Für große Mengen halbiert die Batch-API von OpenAI die Kosten.

## Was es gebracht hat

Stridon ist in Version 1.0 auf GitHub veröffentlicht, mit Dokumentation auf Französisch, Englisch und Chinesisch,
einem Architekturleitfaden, der erklärt, wie man einen Dienst oder ein Format ergänzt, automatisierten Tests und einem
Docker-Image. Entwickelt wurde es im Agentic Coding mit Claude Code.

[ZU BESTÄTIGEN: bereits übersetzter Umfang, bevorzugtes lokales Modell, typische Dauer für ein Buch.]

## Was ich anders machen würde

Die Wahl des Modells bleibt empirisch: Stridon kann denselben Text mit mehreren Diensten übersetzen, misst die
Qualität aber nicht selbst. Das ist die heutige Grenze des Werkzeugs; die später gebaute Aufsatz-Korrektur geht genau
diese Frage der Messung mit einem Benchmark an.
