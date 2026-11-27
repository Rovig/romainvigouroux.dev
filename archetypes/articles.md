---
title: "{{ replaceRE `^\d{4}-\d{2}-\d{2}-` "" .File.ContentBaseName | humanize }}"
description: "[Une phrase : problème + approche + résultat, ≤ 160 caractères]"
date: {{ .Date | time.Format "2006-01-02" }}
slug: "{{ replaceRE `^\d{4}-\d{2}-\d{2}-` "" .File.ContentBaseName }}"
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
