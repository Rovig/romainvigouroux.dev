---
title: "Grading 72 English essays with an LLM, without letting it decide the grade"
description: "An essay-correction pipeline where the AI finds and explains mistakes, while code computes the grade, checks every quote and protects minors' data."
date: 2026-11-27
slug: grading-essays-with-an-llm
tags: [AI architecture, Agentic coding, Local LLM]
keywords: [automated grading, LLM, Claude Code, Ollama, GDPR, education, structured JSON output]
tldr: "The AI analyses each essay and returns JSON; code checks that every quoted mistake really exists, computes the grade and lays out the corrections. Next step: replace the API with a local model, chosen through a measured benchmark."
problem: "A middle-school English teacher has to return detailed individual corrections to three classes for every assignment, which takes entire evenings."
context: "French middle school, three Year 10 classes, writing assignment (CEFR levels A1 to B1), typed or handwritten essays by minors."
constraints:
  - "A fair, explainable grade, to the half point, following an existing rubric"
  - "No invented mistakes: every quoted error must exist in the essay"
  - "Feedback written in French, using the formal « vous », for 14-15-year-olds"
  - "Minors' data: nothing may be versioned or exposed"
stack: [Claude Code, Python, Jinja2, WeasyPrint, python-docx, Ollama, YAML]
outcome: "All 72 essays of the “Yearbook” assignment corrected: a PDF and Word correction per student, an anonymous class feedback sheet, a report per class and a grades file. Contesting a grade takes about a minute. [TO CONFIRM: time spent before / after, teacher feedback]"
faq:
  - q: "Can you let an LLM grade essays?"
    a: "Not on its own. In this project the model awards points per criterion and explains mistakes, but the total is computed by the program, the length criterion is counted mechanically and every quoted mistake is checked against the student's text. The teacher reviews and can change a grade with one line in a file."
  - q: "How do you stop an LLM from inventing mistakes?"
    a: "By requiring the exact excerpt from the essay for every mistake, then checking in code that the excerpt exists. A missing excerpt triggers a new request to the model. It is a simple rule that removes most of the hallucinations a student would see."
  - q: "Why move to a local model instead of an API?"
    a: "So that essays written by minors never leave the school or the home. The architecture is ready for it: only the analysis step changes engine, through an OpenAI-compatible API served by Ollama or vLLM, and a benchmark compares every local model with the reference before any choice."
  - q: "What hardware does a local grading LLM need?"
    a: "A 16 GB M1 Mac can run an 8 to 9 billion parameter model and process a 75-essay assignment overnight, according to the estimates in the architecture document. A more powerful machine is only worth buying if the benchmark shows the quality is not good enough."
---
For a middle-school English teacher, I built an essay-correction pipeline in which an LLM analyses each student's
text, while code stays in charge of everything that must be exact: the grade, the quotes, the layout and data
protection. The result: 72 essays corrected with an individual correction per student, and an architecture ready to
move to a local model.

## The situation

For each writing assignment, the teacher wants to return far more than a grade: underlined mistakes, their
correction, an explanation, exercises built from the student's own sentences, and a class report. Across three
classes, that level of detail costs entire evenings.

The first assignment processed, “Yearbook”, had 72 essays, typed or handwritten, at CEFR levels A1 to B1.

## Why it's harder than it looks

**The grade must be fair and defensible.** Grades get contested. They must follow a precise rubric, to the half
point, and be explainable criterion by criterion.

**An LLM invents.** Ask it to “correct this essay” and it will sometimes find mistakes that are not there. For a
14-year-old, a false mistake is worse than a missed one.

**Tone matters.** Feedback for students must be in French and use the formal « vous ». A single informal « tu »
slipped in by the model makes a document unusable.

**This is minors' data.** Essays carry names and sometimes personal details. Nothing may be versioned, and in the
end nothing should leave the school.

## The options I ruled out

| Option | Why I ruled it out |
|---|---|
| A “correct and grade” prompt | Non-reproducible grades, invented mistakes, no control |
| A grammar checker alone (LanguageTool-type) | Catches spelling, but neither grades nor explains; kept as a possible pre-pass |
| An online grading platform | Students' essays sent to a third party |

## The architecture I chose

```text
.docx/.pdf/photo essays ─► extract ─► ANALYSIS (LLM) ─► verify ─► exercises ─► render
                                       JSON per essay    code       code         PDF, Word,
                                                                                 reports, grades.csv
```

**The LLM only writes one JSON file per essay**: mistakes (exact excerpt, correction, category, explanation), points
per criterion, strengths and advice. Today Claude produces it in a Claude Code session: I ask it to “correct the
essays of this assignment” and it follows the rules written in the repository.

**Code does everything that must be exact.** The length criterion is counted by the program (words excluding the
quote, fixed thresholds); the total is never copied from the model but recomputed. A `verify` step checks that every
quoted excerpt exists in the essay, that grades are in half points, that categories exist and that no text uses the
informal « tu ».

**A mistake taxonomy** gives each category a rule, an example and an exercise. The same categories feed the
individual corrections, the anonymous class feedback sheet that can be projected in class, and the needs-based
groups in the teacher's report.

**Contesting a grade costs one line.** The teacher adds the change to a `corrections.yaml` file and re-runs the
rendering: everything is regenerated in about a minute, without redoing the analysis.

**Handwritten essays** are photographed; the model produces a faithful transcription, mistakes included, which the
teacher checks before correction.

### Towards a local model

The architecture document changes only one component: the analysis goes through an OpenAI-compatible gateway (Ollama
on a Mac, vLLM on a PC), with output constrained by a JSON schema. For an 8 to 30 billion parameter model, the task is
split: mistakes paragraph by paragraph, checklist, grading, writing.

A **benchmark** compares each candidate model with the 72 reference analyses on a stratified sample of 16 essays:
mistake recall and precision, grade gap (at most 1.5 points on average, never more than 3), CEFR level, formal
address, speed. A model below the threshold on precision or grade gap is eliminated, whatever its overall score.

## What it delivered

All 72 essays of the “Yearbook” assignment were corrected: a PDF and Word correction per student, every correction
of a class ready to print, an anonymous feedback sheet, a report per class and a grades file criterion by criterion.
The gateway to local models and the benchmark are implemented.

[TO CONFIRM: correction time before / after, benchmark results on local models, teacher feedback.]

## What I would do differently

The benchmark's reference is the set of analyses produced by Claude, not the truth. The architecture document says
so explicitly and plans for the teacher to grade ten essays herself, to serve as the yardstick for every model,
Claude included. Until that human yardstick exists, no benchmark figure says a model “grades well”: it only says it
grades like Claude.
