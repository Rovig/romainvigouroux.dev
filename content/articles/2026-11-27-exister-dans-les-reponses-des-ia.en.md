---
title: "Showing up in AI answers with a blog on a Raspberry Pi"
description: "How I make my AI architect expertise readable by ChatGPT, Claude and Perplexity with a self-hosted static site, measured every week."
date: 2026-11-27
slug: showing-up-in-ai-answers
tags: [GEO, AI architecture, Agentic coding]
keywords: [GEO, generative engine optimization, llms.txt, AI architect, Raspberry Pi]
tldr: "To be cited by AI assistants you need structured content, a consistent identity and a way to measure AI crawler visits. The Hugo static site generator, a Raspberry Pi and a Cloudflare Tunnel are enough."
problem: "When a recruiter asks an AI assistant \"which AI architect knows agentic coding?\", my name doesn't come up."
context: "Independent profile, content scattered across LinkedIn and Medium, no control over how AI systems read those platforms."
constraints:
  - "No recurring hosting cost"
  - "Publish from a conversation with Claude, with no admin back-office"
  - "Measure whether AI crawlers actually read the site"
  - "No open port on the home router"
stack: [Hugo, Caddy, Cloudflare Tunnel, Raspberry Pi 4, schema.org, llms.txt, Python]
outcome: "A fully machine-readable site, published with a simple git push, with a weekly report of human and AI crawler visits. [TO CONFIRM: first figures after 4 weeks]"
faq:
  - q: "What is GEO?"
    a: "GEO (Generative Engine Optimization) means making content easy to find, understand and cite for generative engines such as ChatGPT, Claude, Perplexity or Gemini. It extends SEO: you optimize to be quoted inside an answer, not only to rank in a list of links."
  - q: "Why host a blog on a Raspberry Pi rather than on Medium?"
    a: "Because you control everything crawlers read: structured data, llms.txt, robots.txt, Markdown versions. On a third-party platform those levers don't exist, and you can't see which AI crawlers visit. A Pi 4 draws a few watts, under €10 of electricity a year, and Cloudflare absorbs the load."
  - q: "Is the llms.txt file actually useful?"
    a: "It is a recent convention, not an enforced standard: some AI tools read it, others don't. It costs nothing since it is generated automatically, and it gives agents a clean index of the site. The weekly report shows whether it is actually fetched."
  - q: "How do I know whether an AI assistant cites my site?"
    a: "Two signals in the server logs: visits from crawlers such as GPTBot, ClaudeBot or PerplexityBot (reading), and visitors arriving from chatgpt.com, perplexity.ai or claude.ai (a citation followed by a click). Both are counted every week."
---
When a recruiter or a client asks an AI assistant to recommend an AI architect, the answer is built from what the
models have read and from what they can fetch live. To be part of that answer, I set up a self-hosted static blog on
a Raspberry Pi 4: content structured for machines, a consistent identity across all my profiles, and a weekly report
that counts visits from AI crawlers.

## The situation

I write regularly about agentic coding and AI architecture, on LinkedIn and on Medium. Yet when I ask an AI
assistant, my name doesn't come up. Those platforms give me no control over what crawlers read, and no visibility
into whether they visit at all.

For an AI architect, that's ironic: my job is to make information usable by models, and my own isn't.

## Why it's harder than it looks

GEO (Generative Engine Optimization) has no dashboard like Google Search Console. Three difficulties stack up.

**The identity must be unambiguous.** A model has to be able to connect "Romain Vigouroux", "AI architect", my
LinkedIn profile and my articles to one and the same person. Without explicit markup, that link stays a guess.

**Crawlers are not all alike.** Some collect content for training (GPTBot, ClaudeBot), others fetch a page live to
answer a question (ChatGPT-User, Perplexity-User). A badly configured CDN can block one group or the other without
any warning.

**Measurement is indirect.** A citation inside an AI answer leaves no trace on my side unless the user clicks. So you
have to read the server logs rather than rely on a browser tracking script — crawlers don't run JavaScript.

## The options I ruled out

| Option | Why I ruled it out |
|---|---|
| Stay on Medium | No access to structured data, robots.txt or logs |
| A CMS like WordPress | Database, security updates, a back-office I don't need if I write from Claude |
| Managed cloud hosting | Works, but recurring cost and less control over raw logs |
| Google Analytics | Doesn't see crawlers, requires a cookie banner |

## The architecture I chose

```text
Conversation with Claude ──► git push (GitHub)
                                   │
                    every 5 min, the Pi pulls the repository
                                   ▼
              Raspberry Pi 4: hugo ──► HTML + JSON-LD + llms.txt + .md
                                   │
                         Caddy (JSON logs)
                                   │
                       cloudflared (outbound tunnel)
                                   ▼
                    Cloudflare ──► visitors, AI crawlers
                                   │
          every Monday: report (humans, AI referrals, crawlers) by email
```

**The Hugo static site generator**, a single binary, fast even on a Raspberry Pi. Its custom output formats produce,
for each article, an HTML page, a raw Markdown version and a schema.org graph (`TechArticle`, `Person`, `FAQPage`,
`BreadcrumbList`), in French, English and German.

**A single `Person` entity**, with a stable identifier and `sameAs` links to LinkedIn and Medium. Every article points
to it as its author: that is what ties my content to my name.

**Files for machines**: `llms.txt` (a site index for agents), `llms-full.txt` (all content in one file), a
`robots.txt` that explicitly allows AI crawlers, a sitemap and a full-content RSS feed.

**A Cloudflare Tunnel** instead of opening a port: the Pi makes an outbound connection, my IP address stays hidden,
and Cloudflare serves static files from its cache.

**Caddy logs as the analytics source.** A Python script reads them every week and separates three populations:
humans, visitors coming from an AI assistant, and AI crawlers by name.

## What it delivered

The site is published with a simple `git push`, with no back-office and no database. Every article is readable by a
human, a search engine and an AI agent, each in the format that suits it.

[TO CONFIRM: first figures from the weekly report after 4 weeks — AI crawlers, AI referrals, visitors.]

## What I would do differently

I would start by checking my CDN settings. Cloudflare offers to block AI crawlers and can manage `robots.txt` itself:
for a site whose whole purpose is to be read by those crawlers, those options must be turned off from day one.
