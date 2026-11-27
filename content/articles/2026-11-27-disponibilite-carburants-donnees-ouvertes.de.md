---
title: "Kraftstoffengpässe in der Umgebung sehen – mit den offenen Daten des französischen Staates"
description: "Ein macOS-Widget, das Verfügbarkeit und Preise von Kraftstoffen auf einer IGN-Karte zeigt, aus dem offiziellen, alle 10 Minuten aktualisierten Datenstrom, ohne API-Schlüssel und ohne Abhängigkeiten."
date: 2026-11-27
slug: kraftstoffverfuegbarkeit-open-data
tags: [Open Data, Softwarearchitektur, Agentic Coding]
keywords: [Kraftstoffpreise, Open Data, data.economie.gouv.fr, IGN, Übersicht, Node.js, hexagonale Architektur]
tldr: "Der offizielle französische Kraftstoffpreis-Datenstrom meldet auch Engpässe, Tankstelle für Tankstelle. Ein Node.js-Kern ohne Abhängigkeiten macht daraus ein Anzeige-JSON, und ein Desktop-Widget zeichnet es nur noch auf eine IGN-Karte. Kein API-Schlüssel, kein Server."
problem: "Vor der Fahrt wissen, welche Tankstellen in der Nähe den gewünschten Kraftstoff noch haben und zu welchem Preis."
context: "Persönliches Open-Source-Werkzeug für macOS, im Agentic Coding mit Claude Code entwickelt."
constraints:
  - "Nur offizielle offene Daten, ohne API-Schlüssel"
  - "Keine npm-Abhängigkeit zu installieren"
  - "Logik testbar ohne die Anzeigeumgebung"
  - "Niemals die Wohnadresse in einem öffentlichen Repository veröffentlichen"
stack: [Node.js, React (JSX), Übersicht, französische Kraftstoffpreis-API, IGN-Géoplateforme, geo.api.gouv.fr, Claude Code]
outcome: "Ein Desktop-Widget, das nahe Tankstellen oder eine gewählte Liste zeigt, mit Verfügbarkeitspunkten, Preisen, interaktiver Karte, Suche nach Ort, Postleitzahl oder Tankstelle und einem Finder-Starter. [ZU BESTÄTIGEN: tatsächliche Nutzung, Anzahl der Nutzer]"
faq:
  - q: "Wo findet man die Kraftstoffverfügbarkeit in Frankreich in Echtzeit?"
    a: "Im Datensatz „Prix des carburants en France – flux instantané v2“ auf data.economie.gouv.fr unter der offenen Lizenz Etalab. Er nennt Preise und Engpässe für jede Tankstelle und wird alle zehn Minuten aktualisiert. Für die Abfrage ist kein Schlüssel nötig."
  - q: "Warum zeigt das Widget keine Tankstellennamen?"
    a: "Weil der offizielle Datensatz weder Namen noch Marke der Tankstellen enthält. Das Widget zeigt daher Adresse, Ort und die offizielle Kennung der Tankstelle, mit der sie sich auf prix-carburants.gouv.fr finden lässt."
  - q: "Warum Logik und Anzeige in einem so kleinen Widget trennen?"
    a: "Um alle Regeln – Verfügbarkeit, Suche, Entfernung – zu testen, ohne die grafische Umgebung zu starten. Der Kern ist reines Node.js und erzeugt JSON; die Anzeige zeichnet es nur. Die Tests laufen mit dem in Node eingebauten Test-Runner, ganz ohne Abhängigkeiten."
---
Der offizielle französische Kraftstoffpreis-Datenstrom veröffentlicht auch Engpässe, Tankstelle für Tankstelle, alle
zehn Minuten. Daraus habe ich pump-radar gemacht, ein macOS-Desktop-Widget, das Verfügbarkeit und Preise von
Kraftstoffen in der Umgebung auf einer IGN-Karte zeigt – ohne API-Schlüssel, ohne Server und ohne npm-Abhängigkeit. Der
Bedarf ist einfach; interessant ist die strikte Trennung von Daten, Logik und Anzeige.

## Die Ausgangslage

Vor der Fahrt lautet die Frage nicht nur „Wo ist es am günstigsten?“, sondern „Wo gibt es den Kraftstoff, den ich
brauche, noch?“. Die offiziellen Websites antworten Tankstelle für Tankstelle; das Widget gibt die Antwort auf einen
Blick, direkt auf dem Schreibtisch. [ZU BESTÄTIGEN: Anlass des Projekts]

## Warum es schwieriger ist, als es aussieht

**Die Daten sind auf ihre Weise unvollständig.** Der offizielle Datenstrom liefert Preise und Engpässe, aber weder
Namen noch Marke der Tankstellen. Manche Preise sind mehrere Tage alt.

**Ein Desktop-Widget ist eine eingeschränkte Umgebung.** Übersicht führt einen Befehl aus und zeigt seine Ausgabe:
kein Server, wenige Testwerkzeuge, ein Neuladen bei jeder Dateiänderung.

**Das Repository ist öffentlich.** Die Standardkonfiguration enthält einen geografischen Bezugspunkt; das darf nie die
Wohnadresse sein.

## Die verworfenen Ansätze

| Option | Warum ich sie verworfen habe |
|---|---|
| Eine mobile App eines Drittanbieters | Keine Ansicht auf dem Desktop, Daten und Logik außerhalb meiner Kontrolle |
| Eine kommerzielle Kraftstoff-API | Schlüssel, Kontingent und Kosten für öffentliche, kostenlose Daten |
| Alles in der Widget-Komponente programmieren | Logik ohne Start der Anzeige nicht testbar |

## Die gewählte Architektur

```text
config.json ─► core/main.mjs ─► Adapter: Kraftstoffpreis-API, Gemeinde-API, IGN-Kacheln, Position
                     │
                     ├─► Domäne: Station, Verfügbarkeitsregeln
                     ├─► Anwendung: Übersicht, Suche, Gemeindevorschläge
                     ▼
               „Ansicht“-JSON auf der Standardausgabe ─► index.jsx (Übersicht) zeichnet Karte und Liste
```

**Die Adapter** kapseln jede Quelle: den Datenstrom mit Preisen und Engpässen, die API für Verwaltungsgrenzen für die
Gemeinden, die IGN-Géoplateforme für die Grundkarte. Alle sind öffentlich und ohne Schlüssel.

**Die Domäne** enthält die fachlichen Regeln: grüner Punkt, wenn alle verfolgten Kraftstoffe verfügbar sind, orange
bei teilweisem Engpass, rot, wenn nichts verfügbar ist, grau, wenn die Tankstelle keinen davon verkauft. Ein Preis,
der älter als 24 Stunden ist, wird ausgegraut.

**Die Anwendungsschicht** baut die Ansicht: Tankstellen in einem Umkreis, eine feste Liste von Tankstellen, Suche nach
Ort mit Vorschlägen, nach Postleitzahl oder nach Kennung.

**Die Anzeige** zeichnet nur das empfangene JSON: interaktive Karte (ziehen, zoomen, Infoblase pro Tankstelle mit
Routenlink), Liste und Menü. Die gesamte Logik wird mit dem in Node eingebauten Test-Runner getestet, ohne etwas zu
installieren.

Ein kleiner Finder-Starter, `Essence.app`, legt bei Bedarf den Widget-Link an, startet Übersicht und protokolliert
jeden Start.

## Was es gebracht hat

Ein Widget, als Open Source auf GitHub veröffentlicht, mit Installationsanleitung, ausführlichem Entwurfsdokument und
einer Testsuite ohne Abhängigkeiten.

[ZU BESTÄTIGEN: tatsächliche Nutzung, Rückmeldungen von Nutzern.]

## Was ich anders machen würde

Die interaktive Karte ist nicht durch automatische Tests abgedeckt: Das README beschreibt eine manuelle Prüfliste.
Mehr Kartenlogik in den testbaren Kern zu verlagern, würde diesen Anteil an Handprüfung verringern.
