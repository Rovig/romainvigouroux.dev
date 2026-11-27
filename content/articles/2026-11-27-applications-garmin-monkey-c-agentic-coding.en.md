---
title: "Agentic coding in Monkey C: a watch face and a Morse transmitter for Garmin"
description: "Two Connect IQ apps written with Claude Code in a niche language, under tight energy, screen and hardware API constraints."
date: 2026-11-27
slug: garmin-apps-monkey-c-agentic-coding
tags: [Agentic coding, Claude Code, Connected devices]
keywords: [Garmin, Connect IQ, Monkey C, watch face, Morse code, agentic coding, power budget]
tldr: "A coding agent is just as useful in a niche language like Monkey C, provided you make it measure and test: power budget measured in the simulator, unit tests, a hardware prototype before any design. Two apps came out of it: a watch face showing tides and today's tasks, and a Morse transmitter using the watch's flashlight."
problem: "Building apps for a Garmin watch, in a poorly documented language, on hardware where every millisecond of computation and every pixel counts."
context: "Two personal Connect IQ projects for the fēnix 7, developed in November 2026 with Claude Code."
constraints:
  - "Strict power budget for the watch face in low-power mode"
  - "Screens from 240 to 280 pixels, fonts drawn without anti-aliasing"
  - "Flashlight API missing on some models that do have a light"
  - "No sensitive data or key in the repository"
stack: [Monkey C, Connect IQ SDK, Python, Open-Meteo Marine, SwiftUI, Claude Code]
outcome: "A three-style watch face that uses about 7.7 ms of computation per second in low-power mode, against a limit of around 30 ms, with 10 automated tests; and a Morse transmitter with a catalogue of 75 maritime radio messages, an on-watch editor and an iPhone companion app. [TO CONFIRM: Connect IQ Store release, real LED tests]"
faq:
  - q: "Can you use a coding agent to program a Garmin watch?"
    a: "Yes. Claude Code wrote most of these two apps in Monkey C, the Connect IQ language. The key is to give it ways to check its work: compiling for several watch models, unit tests, measurements in the simulator and design documents written before the code."
  - q: "How do you show tides on a Garmin watch face?"
    a: "A watch face cannot call the internet every minute. A background task queries the free Open-Meteo Marine API every three hours and stores high and low tides, and the watch face computes the current level between two extremes. These tides are indicative and not meant for navigation."
  - q: "Can a Garmin watch send Morse code with its flashlight?"
    a: "On models whose flashlight is open to apps, yes, through the Connect IQ flashlight API. Not every watch with an LED exposes it, so the app checks that the light actually turns on and otherwise falls back to a white screen with backlight. It complements regulatory distress equipment; it does not replace it."
---
A coding agent is useful even in a niche language, provided you make it measure and test. With Claude Code, I wrote
two Connect IQ apps for Garmin watches in Monkey C: a watch face showing tides, weather and today's tasks within a
measured power budget, and a transmitter that sends Morse messages with the watch's flashlight.

## The situation

Garmin watches are programmed in Monkey C, with the Connect IQ SDK: a Garmin-specific language, scattered
documentation and very constrained hardware. The first project is a watch face that brings weather, pressure, sun,
moon, tides and today's tasks together on one screen. The second sends Morse messages with the watch's flashlight, on
a fēnix 7X Pro.

## Why it's harder than it looks

**The watch face has a power budget.** In low-power mode, the watch stops drawing seconds if computation exceeds its
limit, around 30 ms on average. Every shape drawn has a cost.

**The screen does not anti-alias custom fonts.** The fēnix 7 draws a custom font without smoothing, and the three
target models range from 240 to 280 pixels.

**A watch face cannot query the internet at will.** Remote data, tides and tasks, goes through a background task at a
fixed interval.

**The flashlight API is not guaranteed.** It is missing on some watches that have an LED; on some models it answers
“unsupported”. Designing the Morse transmitter without checking would have meant building on sand.

## The options I ruled out

| Option | Why I ruled it out |
|---|---|
| Letting the agent code without measurements | Risk of exceeding the power budget unnoticed, or breaking one screen size |
| Using only the watch's built-in fonts | Rules out the intended Bauhaus and Hokusai styles |
| A classic keyboard for Morse input | Impractical on a button-driven watch; replaced by a word carousel |

## The architecture I chose

### The “36 Views of the Hour” watch face

```text
Background service (every 30 min) ─► today's tasks (Gist); Open-Meteo tides (every 3 h)
                     │
Data ─► sensors, Garmin weather, sun, computed moon, tides, tasks
                     │
FaceView ─► chosen style: Tactical │ Bauhaus │ Hokusai (sea at the real tide level)
```

Three styles share the same data. The Hokusai style draws a sea whose level follows the real tide, computed between
the last and next high or low water, the sun's path, and a shark that moves towards a boat as the minutes go by.
Today's tasks come from a Gist fed by an iPhone shortcut.

To work around the lack of smoothing, two Python scripts generate the fonts and pre-smoothed digits for each palette.
The simulator measures about 7.7 ms of computation per second in low-power mode, roughly a fourfold margin on the
limit. Ten automated tests cover task parsing and tide calculations.

### The Morse transmitter

```text
MorseCodec (text → on/off segments, tested) ─► Emitter (state machine, absolute deadlines)
                                                    │
                              SwitchingOutput ─► LED flashlight │ fallback: white screen + backlight
```

The first deliverable was a few-line prototype to measure the flashlight's latency and regularity. The codec follows
the PARIS timing standard (6 words per minute by default, i.e. 200 ms per unit). To avoid drift, each delay targets an
absolute deadline rather than a relative one. If the light does not actually turn on, output switches to the screen.

The app ships a catalogue of 75 messages from the CRR, the French restricted maritime radiotelephone operator
certificate (distress, single-letter signals, procedure), a token-based editor on the watch, settings synced with the
phone and a SwiftUI iPhone companion app. It complements VHF radio, distress beacons and regulatory flares; it does not
replace them.

## What it delivered

A three-style watch face that runs on the fēnix 7, 7S and 7X with a measured power margin, and a complete Morse
transmitter on the watch side, with its iPhone companion. Both repositories document their maintenance and design.

[TO CONFIRM: Connect IQ Store release, LED tests on the watch, iPhone companion build.]

## What I would do differently

The iPhone companion app was written without being compiled, as there was no Xcode on the development machine: only
the bridge with the SDK was checked against its real headers. A coding agent does not replace a build chain; you have
to give it one.
