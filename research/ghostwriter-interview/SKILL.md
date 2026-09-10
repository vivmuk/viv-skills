---
name: ghostwriter-interview
description: Use when running the daily chapter interviews for Medical Affairs Singularity — one chapter per day, ghostwriter questions emailed at 9:30 PM.
version: 1.0.0
author: Hermes Agent (Pani)
license: MIT
metadata:
  hermes:
    tags: [book, ghostwriting, interview, daily]
    related_skills: [book-writing-mastery, himalaya]
---

# Ghostwriter Interview System

## Setup
- Book DB: `~/book-medical-affairs-singularity/`
- Chapter order: from `chapter-guide/chapter-guide.md` (19 entries in 6 parts)
- State file: `~/book-medical-affairs-singularity/interview-state.json` tracks: next chapter index, answered questions, drafts done
- Interview Qs per chapter: `~/book-medical-affairs-singularity/interviews/chNN-questions.md` + answers appended as they come back

## Daily job (cron, 21:30 America/New_York)
1. Load next chapter from state file
2. Compose email: chapter number/title, 6-8 ghostwriter questions (mix: factual grounding, story/anecdote mining, opinion/stance, definition of terms, what's changed, pushback)
3. Send via himalaya to vivgatesai@gmail.com, subject `[Medical Affairs Singularity] Ch N Interview — <title>`
4. Increment chapter index in state file
5. If the user replies with answers, fold them into `interviews/chNN-answers.md` before the next send

## Question design rules (ghostwriter craft)
- Ask about STORIES first (books live on narrative): "Tell me about the moment you realized X"
- Ask for SPECIFICS: names (only ones he can disclose), dates, numbers, outcomes
- Ask for the counter-argument he wants to defeat
- Ask what he wants the reader to DO after the chapter
- Never ask yes/no. Ask for scenes, artifacts, receipts.
- 6-8 questions max; mark the 2 that MUST be answered vs nice-to-have

## Email template
```
Subject: [Medical Affairs Singularity] Chapter N Interview — Title

Hi Vivek,

Today's chapter: **N. Title** (Part X)

The 2 questions I need most:
1. ...
2. ...

Also helpful (answer if you have time):
3-8. ...

Reply to this email (or just voice-note me on Telegram) and I'll fold your answers into the chapter file.

— Pani (your ghostwriter)
```
