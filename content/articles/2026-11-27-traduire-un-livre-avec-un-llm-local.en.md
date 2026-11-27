---
title: "Translating a whole book with a local LLM or any API"
description: "Stridon translates EPUBs, illustrated PDFs, subtitles and web articles with Ollama, Claude, GPT or DeepL, keeping the document's structure and resuming where it stopped."
date: 2026-11-27
slug: translating-a-book-with-a-local-llm
tags: [Local LLM, AI architecture, Agentic coding]
keywords: [machine translation, Ollama, LLM, EPUB, PDF, Claude, open source]
tldr: "Translating a book with an LLM is not a prompt problem but a document problem: splitting without breaking the structure, keeping context, surviving interruptions and being able to switch models. Stridon separates engine, cache, translators and formats to solve each of these."
problem: "Translating a book or a long illustrated PDF with AI, without losing the layout and without starting over at the first interruption."
context: "Personal tool published as open source, used from the command line, with free local models or paid APIs."
constraints:
  - "Keep the structure: chapters, headings, images, notes, timed subtitles"
  - "Work with a free local model as well as about fifteen services"
  - "Resume an interrupted translation without paying again for what is already done"
  - "Keep names and tone consistent from one chapter to the next"
stack: [Python, Ollama, Claude, OpenAI, PyMuPDF, BeautifulSoup, Docker, Claude Code]
outcome: "A tool released as version 1.0 on GitHub, with documentation in French, English and Chinese, automated tests and a Docker image. [TO CONFIRM: volume translated, preferred local model, time for a book]"
faq:
  - q: "Can you translate a book with a free local LLM?"
    a: "Yes. By default Stridon uses Ollama on the user's machine, with no key and no cost. The same command works with Claude, GPT, Gemini, Mistral, DeepL or Google Translate by changing one option, which makes it possible to compare quality on the same text."
  - q: "How do you avoid losing a long translation when it is interrupted?"
    a: "Every translated passage is saved as soon as it arrives. If the translation stops, you run the same command again: passages already translated are reused and not sent to the service again. Switching the layout, bilingual or not, costs no new request."
  - q: "How do you keep character names consistent in an AI translation?"
    a: "By sending the model the last translated paragraphs as context. Chapters are then translated in order, and the model sees how a name or a term was rendered just before."
  - q: "What does Stridon do with PDFs that contain images?"
    a: "It rebuilds a new PDF in which the translation flows from page to page, with images in place and headings kept larger. In bilingual mode, each original page gives a page with the original in black and the translation in blue."
---
Translating a book with an LLM is mostly a document problem: splitting without breaking the structure, keeping
consistency from one chapter to the next, surviving interruptions and being able to switch models. I wrote Stridon,
an open-source command-line tool that translates EPUBs, illustrated PDFs, Markdown, subtitles and web articles with a
local model through Ollama or about fifteen services, and resumes where it stopped.

## The situation

Reading a DRM-free book, a figure-heavy PDF report or a web article in another language than the one it was
published in is still tedious. Online document translators handle one file at a time, often lose the layout and
impose their own engine. [TO CONFIRM: the personal or client need that started the project]

LLMs translate far better than a few years ago, including locally. But pasting a chapter into a chat does not make a
translated book.

## Why it's harder than it looks

**Structure is fragile.** An EPUB mixes paragraphs, headings, footnote markers, code and image captions. A PDF has no
paragraphs at all, only blocks of text on pages. An SRT file requires numbers and timestamps to stay intact.

**Long translations get interrupted.** Over hundreds of pages there will be a network drop, an exceeded quota or an
occasional refusal by the model. Starting over costs time and money.

**Consistency gets lost between requests.** Each request ignores the previous ones: a proper name or a technical
term can change translation from one chapter to another.

**No model wins everywhere.** A local model is free and private, an API is often better or faster, a specialised
service like DeepL excels on some language pairs. You need to be able to choose.

## The options I ruled out

| Option | Why I ruled it out |
|---|---|
| Copy-pasting into an AI assistant | Does not scale to a book, loses the structure |
| An online document translation service | One engine, often degraded layout, documents sent to a third party |
| A script tied to a single API | Impossible to compare or to switch to a local model |

## The architecture I chose

```text
file ─► format (EPUB, PDF, TXT, MD, SRT, web) ─► passages
                                                   │
                  translation cache ◄─────────────►│ engine: grouping, context, parallelism
                                                   │
                  interchangeable translator ◄─────┘ Ollama, Claude, OpenAI, Gemini, Mistral, DeepL…
                                                   │
                                     format ─► rebuilt document (translated or bilingual)
```

**Formats** know how to extract translatable passages and rebuild the document: selected tags for EPUB, images put
back in the PDF, timestamps preserved in SRT, code left untouched in Markdown.

**The engine** groups paragraphs by block or by token count, sends several requests in parallel and can give the
model the last translated paragraphs so that tone and names stay consistent.

**The cache** stores every passage as soon as it is translated. Running the same command again resumes where it
stopped; an option re-translates a single passage and rebuilds the whole file from the cache.

**Translators** share one interface. Ollama is the default service, local and keyless. Any OpenAI-compatible server
(LM Studio, vLLM, a corporate gateway) is declared in a simple JSON file. For large volumes, the OpenAI Batch API
halves the cost.

## What it delivered

Stridon is released as version 1.0 on GitHub, with documentation in French, English and Chinese, an architecture
guide explaining how to add a service or a format, automated tests and a Docker image. It was developed through
agentic coding with Claude Code.

[TO CONFIRM: volume already translated, preferred local model, typical time for a book.]

## What I would do differently

Choosing a model remains empirical: Stridon can translate the same text with several services, but it does not
measure quality itself. That is the tool's current limit; the essay-correction pipeline I built later tackles exactly
this question of measurement with a benchmark.
