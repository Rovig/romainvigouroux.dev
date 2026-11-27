---
title: "72 Englisch-Aufsätze mit einem LLM korrigieren, ohne ihm die Note zu überlassen"
description: "Eine Korrektur-Pipeline, in der die KI Fehler findet und erklärt, während der Code die Note berechnet, jedes Zitat prüft und die Daten minderjähriger Schüler schützt."
date: 2026-11-27
slug: aufsaetze-mit-einem-llm-korrigieren
tags: [KI-Architektur, Agentic Coding, Lokale LLMs]
keywords: [automatische Korrektur, LLM, Claude Code, Ollama, DSGVO, Bildung, strukturierte JSON-Ausgabe]
tldr: "Die KI analysiert jeden Aufsatz und liefert JSON; der Code prüft, ob jeder zitierte Fehler wirklich im Text steht, berechnet die Note und setzt die Korrekturen. Nächster Schritt: die API durch ein lokales Modell ersetzen, ausgewählt durch einen gemessenen Benchmark."
problem: "Eine Englischlehrerin an einem französischen Collège muss für jede Arbeit drei Klassen ausführliche Einzelkorrekturen zurückgeben – das kostet ganze Abende."
context: "Französisches Collège, drei Klassen der Abschlussstufe, Schreibaufgabe (GER-Niveau A1 bis B1), getippte oder handschriftliche Aufsätze Minderjähriger."
constraints:
  - "Eine gerechte, erklärbare Note auf den halben Punkt genau nach vorhandenem Bewertungsraster"
  - "Keine erfundenen Fehler: jeder zitierte Fehler muss im Aufsatz stehen"
  - "Rückmeldungen auf Französisch in der Höflichkeitsform für 14- bis 15-Jährige"
  - "Daten Minderjähriger: nichts darf versioniert oder offengelegt werden"
stack: [Claude Code, Python, Jinja2, WeasyPrint, python-docx, Ollama, YAML]
outcome: "Alle 72 Aufsätze der Arbeit „Yearbook“ korrigiert: eine PDF- und Word-Korrektur pro Schüler, ein anonymes Rückmeldeblatt für die Klasse, ein Bericht pro Klasse und eine Notendatei. Ein Einspruch gegen eine Note ist in etwa einer Minute bearbeitet. [ZU BESTÄTIGEN: Zeitaufwand vorher / nachher, Rückmeldung der Lehrerin]"
faq:
  - q: "Kann man ein LLM Aufsätze benoten lassen?"
    a: "Nicht allein. In diesem Projekt vergibt das Modell Punkte je Kriterium und erklärt Fehler, aber die Gesamtnote berechnet das Programm, das Längenkriterium wird mechanisch gezählt und jeder zitierte Fehler wird im Schülertext überprüft. Die Lehrerin prüft nach und kann eine Note mit einer Zeile in einer Datei ändern."
  - q: "Wie verhindert man, dass ein LLM Fehler erfindet?"
    a: "Indem man zu jedem Fehler den exakten Auszug aus dem Aufsatz verlangt und per Code prüft, ob dieser Auszug existiert. Ein nicht gefundener Auszug löst eine neue Anfrage an das Modell aus. Diese einfache Regel beseitigt die meisten Halluzinationen, die ein Schüler sehen würde."
  - q: "Warum ein lokales Modell statt einer API?"
    a: "Damit Aufsätze Minderjähriger die Schule oder das Zuhause nie verlassen. Die Architektur ist darauf vorbereitet: Nur der Analyseschritt wechselt den Motor, über eine OpenAI-kompatible API mit Ollama oder vLLM, und ein Benchmark vergleicht jedes lokale Modell vor jeder Entscheidung mit der Referenz."
  - q: "Welche Hardware braucht ein lokales LLM zur Korrektur?"
    a: "Ein Mac M1 mit 16 GB kann laut den Schätzungen des Architekturdokuments ein Modell mit 8 bis 9 Milliarden Parametern betreiben und eine Arbeit mit 75 Aufsätzen über Nacht bearbeiten. In leistungsstärkere Hardware investiert man erst, wenn der Benchmark zeigt, dass die Qualität nicht reicht."
---
Für eine Englischlehrerin an einem französischen Collège habe ich eine Korrektur-Pipeline gebaut, in der ein LLM den
Text jedes Schülers analysiert, während der Code die Kontrolle über alles behält, was exakt sein muss: die Note, die
Zitate, das Layout und den Datenschutz. Ergebnis: 72 korrigierte Aufsätze mit einer Einzelkorrektur pro Schüler und
eine Architektur, die für ein lokales Modell bereit ist.

## Die Ausgangslage

Für jede Schreibaufgabe möchte die Lehrerin weit mehr als eine Note zurückgeben: unterstrichene Fehler, ihre
Korrektur, eine Erklärung, Übungen aus den eigenen Sätzen des Schülers und einen Klassenbericht. Bei drei Klassen
kostet dieser Detailgrad ganze Abende.

Die erste bearbeitete Arbeit, „Yearbook“, umfasste 72 getippte oder handschriftliche Aufsätze auf GER-Niveau A1 bis B1.

## Warum es schwieriger ist, als es aussieht

**Die Note muss gerecht und vertretbar sein.** Noten werden angefochten. Sie müssen einem genauen Raster folgen, auf
den halben Punkt, und sich Kriterium für Kriterium erklären lassen.

**Ein LLM erfindet.** Bittet man es, „diesen Aufsatz zu korrigieren“, findet es manchmal Fehler, die es nicht gibt.
Für einen 14-Jährigen ist ein falscher Fehler schlimmer als ein übersehener.

**Der Ton zählt.** Rückmeldungen an Schüler müssen auf Französisch und in der Höflichkeitsform sein. Ein einziges vom
Modell eingeschmuggeltes Duzen macht ein Dokument unbrauchbar.

**Es sind Daten von Minderjährigen.** Aufsätze enthalten Namen und manchmal persönliche Angaben. Nichts darf
versioniert werden, und langfristig sollte nichts die Schule verlassen.

## Die verworfenen Ansätze

| Option | Warum ich sie verworfen habe |
|---|---|
| Ein Prompt „korrigiere und benote“ | Nicht reproduzierbare Noten, erfundene Fehler, keine Kontrolle |
| Nur eine Grammatikprüfung (Typ LanguageTool) | Findet Rechtschreibfehler, benotet und erklärt aber nicht; als möglicher Vorlauf behalten |
| Eine Online-Korrekturplattform | Schüleraufsätze würden an Dritte gesendet |

## Die gewählte Architektur

```text
Aufsätze .docx/.pdf/Foto ─► extrahieren ─► ANALYSE (LLM) ─► prüfen ─► Übungen ─► Ausgabe
                                            JSON je Aufsatz   Code      Code       PDF, Word,
                                                                                   Berichte, noten.csv
```

**Das LLM schreibt nur eine JSON-Datei pro Aufsatz**: Fehler (exakter Auszug, Korrektur, Kategorie, Erklärung),
Punkte je Kriterium, Stärken und Ratschläge. Heute erzeugt Claude sie in einer Claude-Code-Sitzung: Ich bitte es,
„die Aufsätze dieser Arbeit zu korrigieren“, und es folgt den im Repository beschriebenen Regeln.

**Der Code erledigt alles, was exakt sein muss.** Das Längenkriterium zählt das Programm (Wörter ohne das Zitat, feste
Schwellen); die Gesamtnote wird nie vom Modell übernommen, sondern neu berechnet. Ein Schritt `verifier` prüft, ob
jeder zitierte Auszug im Aufsatz steht, ob die Noten halbe Punkte sind, ob die Kategorien existieren und ob kein Text
den Schüler duzt.

**Eine Fehlertaxonomie** ordnet jeder Kategorie eine Regel, ein Beispiel und eine Übung zu. Dieselben Kategorien
speisen die Einzelkorrekturen, das anonyme, projizierbare Rückmeldeblatt für die Klasse und die Fördergruppen im
Bericht für die Lehrerin.

**Ein Einspruch kostet eine Zeile.** Die Lehrerin trägt die Änderung in eine Datei `corrections.yaml` ein und startet
die Ausgabe neu: Alles wird in etwa einer Minute neu erzeugt, ohne die Analyse zu wiederholen.

**Handschriftliche Aufsätze** werden fotografiert; das Modell erstellt eine getreue Abschrift, Fehler inbegriffen, die
die Lehrerin vor der Korrektur prüft.

### Auf dem Weg zu einem lokalen Modell

Das Architekturdokument tauscht nur einen Baustein aus: Die Analyse läuft über ein OpenAI-kompatibles Gateway (Ollama
auf dem Mac, vLLM auf dem PC), mit einer durch ein JSON-Schema erzwungenen Ausgabe. Für ein Modell mit 8 bis 30
Milliarden Parametern wird die Aufgabe zerlegt: Fehler Absatz für Absatz, Checkliste, Benotung, Formulierung.

Ein **Benchmark** vergleicht jedes Kandidatenmodell mit den 72 Referenzanalysen anhand einer geschichteten Stichprobe
von 16 Aufsätzen: Trefferquote und Genauigkeit bei Fehlern, Notenabweichung (im Mittel höchstens 1,5 Punkte, nie mehr
als 3), GER-Niveau, Höflichkeitsform, Geschwindigkeit. Ein Modell unter der Schwelle bei Genauigkeit oder
Notenabweichung scheidet aus, unabhängig von seiner Gesamtpunktzahl.

## Was es gebracht hat

Alle 72 Aufsätze der Arbeit „Yearbook“ wurden korrigiert: eine PDF- und Word-Korrektur pro Schüler, alle Korrekturen
einer Klasse druckfertig, ein anonymes Rückmeldeblatt, ein Bericht pro Klasse und eine Notendatei Kriterium für
Kriterium. Das Gateway zu lokalen Modellen und der Benchmark sind umgesetzt.

[ZU BESTÄTIGEN: Korrekturzeit vorher / nachher, Benchmark-Ergebnisse der lokalen Modelle, Rückmeldung der Lehrerin.]

## Was ich anders machen würde

Die Referenz des Benchmarks sind die von Claude erzeugten Analysen, nicht die Wahrheit. Das Architekturdokument sagt
das ausdrücklich und sieht vor, dass die Lehrerin selbst zehn Aufsätze benotet, die als Maßstab für alle Modelle
dienen, Claude eingeschlossen. Solange es diesen menschlichen Maßstab nicht gibt, sagt keine Benchmark-Zahl, dass ein
Modell „gut korrigiert“ – nur, dass es korrigiert wie Claude.
