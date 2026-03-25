# Code Review Report

**Date:** {YYYY-MM-DD}
**Branch:** {branch-name} → {base-branch}
**PR:** [#{pr-number}]({pr-url}) — {pr-title}
**Files Changed:** {n} (+{additions} / -{deletions})

---

## Overall Rating: {A / B / C / D}

| Metric | Count |
|--------|-------|
| Critical Issues | {n} |
| Required Improvements | {n} |
| Recommendations | {n} |

**Rating guide:**
- **A** — Ready to merge with minor nits only
- **B** — A few things to fix but solid overall; can merge after addressing required items
- **C** — Significant issues; needs meaningful rework before merge
- **D** — Fundamental problems; needs a rethink or substantial rewrite

---

## Critical Issues *(must fix before merge)*

{Leave this section out if there are none.}

**[CRITICAL] {file/path.py}:{line}** — *{short title}*
> **What:** {What is wrong}
> **Why:** {Why it matters — what can break}
> **Fix:** {Specific, concrete suggestion with example code if helpful}

---

## Required Improvements *(should fix before merge)*

**[REQUIRED] {file/path.py}:{line-range}** — *{short title}*
> **What:** {What is wrong}
> **Why:** {Why it matters}
> **Fix:** {How to fix it}

---

## Recommendations *(worth doing, not blocking)*

**[REC] {file/path.tsx}:{line}** — *{short title}*
> {Concise suggestion}

---

## Summary

{Brief overall assessment. What's good about this PR? What's the main theme of the issues? What does the author need to focus on?}
