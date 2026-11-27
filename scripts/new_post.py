#!/usr/bin/env python3
"""Crée le squelette d'un nouvel article.

    python3 scripts/new_post.py "Titre de l'article"            # date du jour
    python3 scripts/new_post.py "Titre" --date 2026-12-03
"""
import argparse
import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from build import slugify  # noqa: E402

TEMPLATE = '''---
title: "{title}"
description: "[Une phrase : problème + approche + résultat, ≤ 160 caractères]"
date: {date}
tags: []
keywords: []
tldr: ""
problem: ""
context: ""
constraints: []
stack: []
outcome: ""
faq:
  - q: ""
    a: ""
linkedin: false
linkedin_post: |
  
draft: true
---
[Premier paragraphe = la réponse, 40 à 70 mots, autonome.]

## La situation

## Pourquoi c'est plus difficile qu'il n'y paraît

## Les pistes écartées

## L'architecture retenue

## Ce que ça a donné

## Ce que je referais différemment
'''


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("title")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    args = ap.parse_args()
    slug = slugify(args.title)[:60].rstrip("-")
    path = ROOT / "content" / "posts" / f"{args.date}-{slug}.md"
    if path.exists():
        sys.exit(f"Existe déjà : {path}")
    path.write_text(TEMPLATE.format(title=args.title.replace('"', '\\"'), date=args.date), encoding="utf-8")
    print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
