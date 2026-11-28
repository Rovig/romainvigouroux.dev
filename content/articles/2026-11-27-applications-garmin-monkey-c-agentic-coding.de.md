---
title: "Agentic Coding in Monkey C: ein Zifferblatt und ein Morse-Sender für Garmin"
description: "Zwei Connect-IQ-Apps, mit Claude Code in einer Nischensprache geschrieben, unter strengen Vorgaben für Energie, Display und Hardware-API."
date: 2026-11-27
slug: garmin-apps-monkey-c-agentic-coding
tags: [Agentic Coding, Claude Code, Vernetzte Geräte]
keywords: [Garmin, Connect IQ, Monkey C, Zifferblatt, Morsecode, Agentic Coding, Energiebudget]
tldr: "Ein Coding-Agent ist auch in einer Nischensprache wie Monkey C nützlich, wenn man ihm Messungen und Tests abverlangt: im Simulator gemessenes Energiebudget, Unit-Tests, ein Hardware-Prototyp vor jedem Entwurf. Daraus entstanden zwei Apps: ein Zifferblatt mit Gezeiten und Tagesaufgaben und ein Morse-Sender über die Lampe der Uhr."
problem: "Apps für eine Garmin-Uhr bauen, in einer schlecht dokumentierten Sprache, auf einer Hardware, bei der jede Millisekunde Rechenzeit und jedes Pixel zählt."
context: "Zwei persönliche Connect-IQ-Projekte für die fēnix 7, im November 2026 mit Claude Code entwickelt."
constraints:
  - "Strenges Energiebudget des Zifferblatts im Stromsparmodus"
  - "Displays von 240 bis 280 Pixeln, Schriften ohne Kantenglättung"
  - "Lampen-API fehlt auf manchen Modellen, die eine Lampe haben"
  - "Keine sensiblen Daten oder Schlüssel im Repository"
stack: [Monkey C, Connect IQ SDK, Python, Open-Meteo Marine, SwiftUI, Claude Code]
outcome: "Ein Zifferblatt mit drei Stilen, das im Stromsparmodus etwa 7,7 ms Rechenzeit pro Sekunde braucht, bei einer Grenze von rund 30 ms, mit 10 automatischen Tests; und ein Morse-Sender mit 75 Nachrichten des französischen Seefunkzeugnisses, Editor auf der Uhr und iPhone-Begleit-App. [ZU BESTÄTIGEN: Veröffentlichung im Connect IQ Store, echte LED-Tests]"
faq:
  - q: "Kann man eine Garmin-Uhr mit einem Coding-Agenten programmieren?"
    a: "Ja. Claude Code hat den Großteil dieser beiden Apps in Monkey C geschrieben, der Sprache von Connect IQ. Entscheidend ist, ihm Mittel zur Selbstkontrolle zu geben: Kompilierung für mehrere Uhrenmodelle, Unit-Tests, Messungen im Simulator und Entwurfsdokumente, die vor dem Code entstehen."
  - q: "Wie zeigt man Gezeiten auf einem Garmin-Zifferblatt an?"
    a: "Ein Zifferblatt kann nicht jede Minute das Internet abfragen. Eine Hintergrundaufgabe ruft alle drei Stunden die kostenlose API Open-Meteo Marine ab und speichert Hoch- und Niedrigwasser; das Zifferblatt berechnet den aktuellen Pegel zwischen zwei Extremen. Diese Gezeiten sind Richtwerte und nicht für die Navigation gedacht."
  - q: "Kann eine Garmin-Uhr mit ihrer Lampe Morsezeichen senden?"
    a: "Bei Modellen, deren Lampe für Apps zugänglich ist, ja, über die Lampen-API von Connect IQ. Nicht jede Uhr mit LED stellt sie bereit; die App prüft daher, ob die Lampe wirklich angeht, und weicht sonst auf einen weißen Bildschirm mit Hintergrundbeleuchtung aus. Sie ergänzt die vorgeschriebene Notfallausrüstung, ersetzt sie aber nicht."
---
Ein Coding-Agent ist selbst in einer Nischensprache nützlich, wenn man ihm Messungen und Tests abverlangt. Mit Claude
Code habe ich zwei Connect-IQ-Apps für Garmin-Uhren in Monkey C geschrieben: ein Zifferblatt, das Gezeiten, Wetter und
Tagesaufgaben innerhalb eines gemessenen Energiebudgets anzeigt, und einen Sender, der Morsenachrichten über die Lampe
der Uhr abgibt.

## Die Ausgangslage

Garmin-Uhren werden in Monkey C mit dem Connect IQ SDK programmiert: eine Garmin-eigene Sprache, verstreute
Dokumentation und sehr eingeschränkte Hardware. Das erste Projekt ist ein Zifferblatt, das Wetter, Luftdruck, Sonne,
Mond, Gezeiten und Tagesaufgaben auf einem Bildschirm vereint. Das zweite sendet Morsenachrichten über die Lampe der
Uhr, auf einer fēnix 7X Pro.

## Warum es schwieriger ist, als es aussieht

**Das Zifferblatt hat ein Energiebudget.** Im Stromsparmodus schaltet die Uhr die Sekundenanzeige ab, wenn die
Berechnung ihre Grenze überschreitet, im Mittel rund 30 ms. Jede gezeichnete Form kostet.

**Das Display glättet eigene Schriften nicht.** Die fēnix 7 zeigt eine eigene Schrift ohne Kantenglättung, und die
drei Zielmodelle reichen von 240 bis 280 Pixeln.

**Ein Zifferblatt kann das Internet nicht nach Belieben abfragen.** Entfernte Daten, Gezeiten und Aufgaben, laufen über
eine Hintergrundaufgabe in festen Abständen.

**Die Lampen-API ist nicht garantiert.** Auf manchen Uhren mit LED fehlt sie; auf einigen Modellen antwortet sie mit
„nicht unterstützt“. Den Morse-Sender ohne Prüfung zu entwerfen, hätte geheißen, auf Sand zu bauen.

## Die verworfenen Ansätze

| Option | Warum ich sie verworfen habe |
|---|---|
| Den Agenten ohne Messungen programmieren lassen | Gefahr, das Energiebudget unbemerkt zu überschreiten oder eine Displaygröße zu zerstören |
| Nur die eingebauten Schriften der Uhr verwenden | Schließt die gewünschten Stile Bauhaus und Hokusai aus |
| Eine klassische Tastatur für die Morse-Eingabe | Unpraktisch auf einer tastengesteuerten Uhr; ersetzt durch ein Wort-Karussell |

## Die gewählte Architektur

### Das Zifferblatt „36 Ansichten der Stunde“

```text
Hintergrunddienst (alle 30 Min.) ─► Tagesaufgaben (Gist); Gezeiten von Open-Meteo (alle 3 Std.)
                     │
Daten ─► Sensoren, Garmin-Wetter, Sonne, berechneter Mond, Gezeiten, Aufgaben
                     │
FaceView ─► gewählter Stil: Taktisch │ Bauhaus │ Hokusai (Meer auf dem echten Gezeitenpegel)
```

Drei Stile teilen sich dieselben Daten. Der Hokusai-Stil zeichnet ein Meer, dessen Pegel der echten Gezeit folgt,
berechnet zwischen dem letzten und dem nächsten Hoch- oder Niedrigwasser, den Sonnenbogen und einen Hai, der sich im
Lauf der Minuten einem Boot nähert. Die Tagesaufgaben kommen aus einem Gist, der von einem iPhone-Kurzbefehl befüllt
wird.

Um die fehlende Glättung zu umgehen, erzeugen zwei Python-Skripte die Schriften und vorgeglättete Ziffern für jede
Farbpalette. Der Simulator misst im Stromsparmodus etwa 7,7 ms Rechenzeit pro Sekunde, also etwa die vierfache Reserve
gegenüber der Grenze. Zehn automatische Tests decken das Einlesen der Aufgaben und die Gezeitenberechnung ab.

### Der Morse-Sender

```text
MorseCodec (Text → An/Aus-Segmente, getestet) ─► Emitter (Zustandsautomat, absolute Termine)
                                                     │
                               SwitchingOutput ─► LED-Lampe │ Ersatz: weißer Bildschirm + Beleuchtung
```

Das erste Ergebnis war ein Prototyp aus wenigen Zeilen, um Latenz und Gleichmäßigkeit der Lampe zu messen. Der Codec
folgt dem Timing-Standard PARIS (standardmäßig 6 Wörter pro Minute, also 200 ms pro Einheit). Gegen Drift zielt jede
Verzögerung auf einen absoluten Termin statt auf eine relative Dauer. Geht die Lampe nicht wirklich an, wechselt die
Ausgabe auf den Bildschirm.

Die App enthält einen Katalog mit 75 Nachrichten des CRR, des französischen beschränkt gültigen Seefunkzeugnisses
(Notfall, Einbuchstabensignale, Verfahren), einen Editor mit „Bausteinen“ auf der Uhr, mit dem Telefon synchronisierte
Einstellungen und eine iPhone-Begleit-App in SwiftUI. Sie ergänzt UKW-Funk, Notfunkbake und vorgeschriebene Signalmittel;
sie ersetzt sie nicht.

## Was es gebracht hat

Ein Zifferblatt mit drei Stilen, das auf fēnix 7, 7S und 7X mit gemessener Energiereserve läuft, und ein vollständiger
Morse-Sender auf der Uhr mit iPhone-Begleit-App. Beide Repositories dokumentieren Wartung und Entwurf.

[ZU BESTÄTIGEN: Veröffentlichung im Connect IQ Store, LED-Tests auf der Uhr, Kompilierung der iPhone-App.]

## Was ich anders machen würde

Die iPhone-Begleit-App wurde geschrieben, ohne kompiliert werden zu können, da auf dem Entwicklungsrechner kein Xcode
vorhanden war: Nur die Brücke zum SDK wurde gegen dessen echte Header geprüft. Ein Coding-Agent ersetzt keine
Build-Kette; man muss sie ihm zur Verfügung stellen.
