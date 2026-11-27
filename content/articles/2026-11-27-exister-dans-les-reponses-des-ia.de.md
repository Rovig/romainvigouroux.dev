---
title: "In KI-Antworten sichtbar werden – mit einem Blog auf dem Raspberry Pi"
description: "Wie ich meine Expertise als KI-Architekt für ChatGPT, Claude und Perplexity lesbar mache: mit einer selbst gehosteten statischen Website, die jede Woche gemessen wird."
date: 2026-11-27
slug: in-ki-antworten-sichtbar-werden
tags: [GEO, KI-Architektur, Agentic Coding]
keywords: [GEO, Generative Engine Optimization, llms.txt, KI-Architekt, Raspberry Pi]
tldr: "Um von KI-Assistenten zitiert zu werden, braucht es strukturierte Inhalte, eine konsistente Identität und eine Messung der Besuche von KI-Crawlern. Der statische Website-Generator Hugo, ein Raspberry Pi und ein Cloudflare Tunnel reichen dafür aus."
problem: "Wenn ein Recruiter einen KI-Assistenten fragt: „Welcher KI-Architekt kennt sich mit Agentic Coding aus?“, taucht mein Name nicht auf."
context: "Selbstständiges Profil, Inhalte verstreut über LinkedIn und Medium, keinerlei Einfluss darauf, wie KI-Systeme diese Plattformen lesen."
constraints:
  - "Keine laufenden Hosting-Kosten"
  - "Veröffentlichen aus einem Gespräch mit Claude, ohne Admin-Oberfläche"
  - "Messen, ob KI-Crawler die Website tatsächlich lesen"
  - "Kein offener Port am Heimrouter"
stack: [Hugo, Caddy, Cloudflare Tunnel, Raspberry Pi 4, schema.org, llms.txt, Python]
outcome: "Eine vollständig maschinenlesbare Website, veröffentlicht per einfachem git push, mit einem wöchentlichen Bericht über menschliche Besucher und KI-Crawler. [ZU BESTÄTIGEN: erste Zahlen nach 4 Wochen]"
faq:
  - q: "Was ist GEO?"
    a: "GEO (Generative Engine Optimization) bedeutet, Inhalte so aufzubereiten, dass generative Suchsysteme wie ChatGPT, Claude, Perplexity oder Gemini sie leicht finden, verstehen und zitieren können. Es erweitert SEO: Ziel ist es, in einer Antwort zitiert zu werden, nicht nur in einer Linkliste zu ranken."
  - q: "Warum einen Blog auf einem Raspberry Pi hosten statt auf Medium?"
    a: "Weil man alles kontrolliert, was Crawler lesen: strukturierte Daten, llms.txt, robots.txt, Markdown-Versionen. Auf einer fremden Plattform gibt es diese Hebel nicht, und man sieht nicht, welche KI-Crawler vorbeikommen. Ein Pi 4 verbraucht wenige Watt, also unter 10 € Strom pro Jahr, und Cloudflare fängt die Last ab."
  - q: "Bringt die Datei llms.txt wirklich etwas?"
    a: "Sie ist eine junge Konvention, kein verbindlicher Standard: Manche KI-Werkzeuge lesen sie, andere nicht. Sie kostet nichts, da sie automatisch erzeugt wird, und bietet Agenten einen sauberen Index der Website. Der Wochenbericht zeigt, ob sie tatsächlich abgerufen wird."
  - q: "Woran erkenne ich, ob ein KI-Assistent meine Website zitiert?"
    a: "An zwei Signalen in den Server-Logs: Besuche von Crawlern wie GPTBot, ClaudeBot oder PerplexityBot (Lesen) und Besucher, die von chatgpt.com, perplexity.ai oder claude.ai kommen (Zitat mit anschließendem Klick). Beides wird jede Woche gezählt."
---
Wenn ein Recruiter oder ein Kunde einen KI-Assistenten nach einem KI-Architekten fragt, entsteht die Antwort aus
dem, was die Modelle gelesen haben, und aus dem, was sie live abrufen können. Um darin vorzukommen, habe ich einen
selbst gehosteten statischen Blog auf einem Raspberry Pi 4 aufgesetzt: Inhalte, die für Maschinen strukturiert sind,
eine konsistente Identität über alle meine Profile hinweg und ein Wochenbericht, der die Besuche von KI-Crawlern zählt.

## Die Ausgangslage

Ich schreibe regelmäßig über Agentic Coding und KI-Architektur, auf LinkedIn und auf Medium. Trotzdem taucht mein
Name nicht auf, wenn ich einen KI-Assistenten frage. Diese Plattformen geben mir keinerlei Kontrolle darüber, was
Crawler lesen, und keinen Einblick, ob sie überhaupt vorbeikommen.

Für einen KI-Architekten ist das paradox: Mein Beruf besteht darin, Informationen für Modelle nutzbar zu machen –
nur meine eigenen sind es nicht.

## Warum es schwieriger ist, als es aussieht

GEO (Generative Engine Optimization, also die Optimierung für generative Suchsysteme) hat kein Dashboard wie die
Google Search Console. Drei Schwierigkeiten kommen zusammen.

**Die Identität muss eindeutig sein.** Ein Modell muss „Romain Vigouroux“, „KI-Architekt“, mein LinkedIn-Profil und
meine Artikel ein und derselben Person zuordnen können. Ohne explizites Markup bleibt diese Verbindung eine Vermutung.

**Crawler sind nicht gleich.** Manche sammeln Inhalte für das Training (GPTBot, ClaudeBot), andere rufen eine Seite
live ab, um eine Frage zu beantworten (ChatGPT-User, Perplexity-User). Ein falsch konfiguriertes CDN kann die eine
oder die andere Gruppe blockieren, ohne dass man es merkt.

**Die Messung ist indirekt.** Ein Zitat in einer KI-Antwort hinterlässt bei mir keine Spur, außer der Nutzer klickt.
Also muss man die Server-Logs auswerten statt eines Tracking-Skripts im Browser – Crawler führen kein JavaScript aus.

## Die verworfenen Ansätze

| Option | Warum ich sie verworfen habe |
|---|---|
| Bei Medium bleiben | Kein Zugriff auf strukturierte Daten, robots.txt oder Logs |
| Ein CMS wie WordPress | Datenbank, Sicherheitsupdates, eine Admin-Oberfläche, die ich nicht brauche, wenn ich aus Claude heraus schreibe |
| Verwaltetes Cloud-Hosting | Funktioniert, aber laufende Kosten und weniger Kontrolle über die Rohdaten der Logs |
| Google Analytics | Sieht keine Crawler, erfordert ein Cookie-Banner |

## Die gewählte Architektur

```text
Gespräch mit Claude ──► git push (GitHub)
                                   │
                    alle 5 Min. holt der Pi das Repository
                                   ▼
              Raspberry Pi 4: hugo ──► HTML + JSON-LD + llms.txt + .md
                                   │
                         Caddy (JSON-Logs)
                                   │
                       cloudflared (ausgehender Tunnel)
                                   ▼
                    Cloudflare ──► Besucher, KI-Crawler
                                   │
          jeden Montag: Bericht (Menschen, KI-Verweise, Crawler) per E-Mail
```

**Der statische Website-Generator Hugo**, eine einzige ausführbare Datei, schnell selbst auf einem Raspberry Pi.
Über eigene Ausgabeformate erzeugt er für jeden Artikel eine HTML-Seite, eine reine Markdown-Version und einen
schema.org-Graphen (`TechArticle`, `Person`, `FAQPage`, `BreadcrumbList`) – auf Französisch, Englisch und Deutsch.

**Eine einzige `Person`-Entität** mit stabiler Kennung und `sameAs`-Links zu LinkedIn und Medium. Jeder Artikel
verweist als Autor auf sie: Genau das verknüpft meine Inhalte mit meinem Namen.

**Dateien für Maschinen**: `llms.txt` (ein Index der Website für Agenten), `llms-full.txt` (alle Inhalte in einer
Datei), eine `robots.txt`, die KI-Crawler ausdrücklich zulässt, eine Sitemap und ein RSS-Feed mit Volltext.

**Ein Cloudflare Tunnel** statt einer Portfreigabe: Der Pi baut eine ausgehende Verbindung auf, meine IP-Adresse
bleibt verborgen, und Cloudflare liefert statische Dateien aus seinem Cache aus.

**Die Caddy-Logs als Analytics-Quelle.** Ein Python-Skript wertet sie jede Woche aus und unterscheidet drei Gruppen:
Menschen, Besucher, die von einem KI-Assistenten kommen, und KI-Crawler nach Namen.

## Was es gebracht hat

Die Website wird per einfachem `git push` veröffentlicht, ohne Admin-Oberfläche und ohne Datenbank. Jeder Artikel ist
für Menschen, Suchmaschinen und KI-Agenten lesbar, jeweils im passenden Format.

[ZU BESTÄTIGEN: erste Zahlen aus dem Wochenbericht nach 4 Wochen – KI-Crawler, KI-Verweise, Besucher.]

## Was ich anders machen würde

Ich würde mit den Einstellungen meines CDN beginnen. Cloudflare bietet an, KI-Crawler zu blockieren, und kann die
`robots.txt` selbst verwalten: Für eine Website, deren ganzer Zweck es ist, von diesen Crawlern gelesen zu werden,
müssen diese Optionen vom ersten Tag an ausgeschaltet sein.
