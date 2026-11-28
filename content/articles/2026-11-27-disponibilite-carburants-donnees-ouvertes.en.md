---
title: "Seeing fuel shortages nearby with French government open data"
description: "A macOS widget that shows fuel availability and prices on an IGN map, from the official feed updated every 10 minutes, with no API key and no dependency."
date: 2026-11-27
slug: fuel-availability-open-data
tags: [Open data, Software architecture, Agentic coding]
keywords: [fuel prices, open data, data.economie.gouv.fr, IGN, Übersicht, Node.js, hexagonal architecture]
tldr: "The official French fuel price feed also reports shortages, station by station. A dependency-free Node.js core turns that feed into a display JSON, and a desktop widget simply draws it on an IGN map. No API key, no server."
problem: "Knowing, before taking the car, which nearby stations still have the fuel you need and at what price."
context: "Personal open-source tool for macOS, built through agentic coding with Claude Code."
constraints:
  - "Only official open data, with no API key"
  - "No npm dependency to install"
  - "Logic testable without the display environment"
  - "Never publish the home location in a public repository"
stack: [Node.js, React (JSX), Übersicht, French fuel price API, IGN Géoplateforme, geo.api.gouv.fr, Claude Code]
outcome: "A desktop widget showing nearby stations or a chosen list, with availability badges, prices, an interactive map, search by town, postcode or station, and a Finder launcher. [TO CONFIRM: actual use, number of users]"
faq:
  - q: "Where can you find real-time fuel availability in France?"
    a: "In the “Prix des carburants en France – flux instantané v2” dataset published on data.economie.gouv.fr under the Etalab Open Licence. It gives prices and shortages station by station and is updated every ten minutes. No key is needed to query it."
  - q: "Why does the widget not show station names?"
    a: "Because the official dataset contains neither the name nor the brand of stations. The widget therefore shows the address, the town and the station's official identifier, which lets you find it on prix-carburants.gouv.fr."
  - q: "Why separate logic from display in such a small widget?"
    a: "To test every rule, availability, search, distance, without launching the graphical environment. The core is plain Node.js and produces JSON; the display just draws it. Tests run with Node's built-in test runner, with no dependency at all."
---
The official French fuel price feed also publishes shortages, station by station, every ten minutes. I turned it into
pump-radar, a macOS desktop widget that shows fuel availability and prices around you on an IGN map, with no API key,
no server and no npm dependency. The need is simple; the interest lies in the strict separation between data, logic
and display.

## The situation

Before taking the car, the question is not only “where is it cheapest?” but “where is the fuel I need still
available?”. Official websites answer station by station; the widget gives the answer at a glance, on the desktop.
[TO CONFIRM: context that motivated the project]

## Why it's harder than it looks

**The data is incomplete in its own way.** The official feed gives prices and shortages, but neither the name nor the
brand of stations. Some prices are several days old.

**A desktop widget is a constrained environment.** Übersicht runs a command and displays its output: no server, few
testing tools, a reload on every file change.

**The repository is public.** The default configuration contains a geographic reference point; it must never be the
home address.

## The options I ruled out

| Option | Why I ruled it out |
|---|---|
| A third-party mobile app | No desktop view, data and logic outside my control |
| A commercial fuel API | Key, quota and cost for public, free data |
| Coding everything in the widget component | Logic impossible to test without launching the display |

## The architecture I chose

```text
config.json ─► core/main.mjs ─► adapters: fuel price API, towns API, IGN tiles, location
                     │
                     ├─► domain: Station, availability rules
                     ├─► app: dashboard, search, town suggestions
                     ▼
               “view” JSON on standard output ─► index.jsx (Übersicht) draws the map and list
```

**Adapters** isolate each source: the price and shortage feed, the administrative boundaries API for towns, the IGN
Géoplateforme for the base map. All are public and keyless.

**The domain** holds the business rules: a green badge when every tracked fuel is available, orange for a partial
shortage, red when nothing is available, grey when the station sells none of them. A price older than 24 hours is
greyed out.

**The application layer** builds the view: stations within a radius, a fixed list of stations, search by town with
suggestions, by postcode or by identifier.

**The display** only draws the JSON it receives: an interactive map (drag, zoom, a bubble per station with a
directions link), a list and a menu. All the logic is tested with Node's built-in test runner, with nothing to
install.

A small Finder launcher, `Essence.app`, creates the widget link if missing, starts Übersicht and logs each launch.

## What it delivered

A widget published as open source on GitHub, with installation documentation, a detailed design document and a
dependency-free test suite.

[TO CONFIRM: actual use, user feedback.]

## What I would do differently

The interactive map is not covered by automated tests: the README describes a manual checklist. Moving more of the
map logic into the testable core would reduce that share of hand checking.
