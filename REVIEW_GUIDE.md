# Review context

## Goal

A minimal, maintainable macOS study assistant for an iCloud-synced Obsidian vault. Morning output is exactly three prioritized tasks, optional review tasks and one deep-work focus. Evening output summarizes recorded progress and proposes tomorrow's first step.

Reliability and preservation of handwritten notes matter more than feature breadth. Do not recommend uploading the whole vault or embedding secrets in code.

## Suggested review prompt

> Review this repository as a Python/macOS automation project. Read README.md, then runner.py, obsidian_utils.py, ai_provider.py, config.py and test_safety.py. Identify concrete correctness, data-loss, privacy and reliability risks. Prioritize findings, cite code locations, give a reproducible scenario for each, and recommend the smallest useful fix. Distinguish confirmed bugs from limitations and optional improvements. Pay particular attention to iCloud/editor concurrency, Markdown section handling, repeat runs, context limits, API failure handling and launchd behavior. Do not assume the scheduling templates are installed.

## Evidence and scope

Seven offline tests passed. Real morning and evening dry runs succeeded using gemini-3.5-flash-lite. The revised evening prompt was tested to avoid treating a blank note as proof of no progress. No note writes were performed during these API tests. launchd template syntax was checked, but scheduled execution and real editor/iCloud races have not been validated end to end.

This repository contains the improved evening prompt. The earlier vault-installed copy may still need that update; deployment is separate from publishing code. No personal vault content or raw API responses are included here.

## Areas worth assessing

- File checks plus atomic replacement cannot eliminate every editor/iCloud race; backups mitigate but do not prevent conflicts.
- Fixed alphabetic selection can miss relevant active notes, and truncation can omit useful context.
- Checkbox extraction and heading recognition are intentionally lightweight rather than a full Markdown parser.
- Existing generated content is treated as user-owned and never refreshed automatically.
- HTTP failures have minimal diagnostics, and there is no persistent retry queue.
- Provider extensibility currently means one interface with only Gemini implemented.
- There is no automated launchd integration test or complete dependency lockfile.

Please preserve the safe default of DRY_RUN=true in any proposed patch.
