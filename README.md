# Obsidian AI Learning

A small macOS automation project that uses Gemini to draft a morning study plan and an evening learning review in an Obsidian vault. This repository contains code, tests and configuration examples only—no personal notes or credentials.

## Current status

- Morning and evening real API dry runs passed with `gemini-3.5-flash-lite`.
- Seven offline safety tests pass.
- The evening prompt distinguishes missing records from lack of actual progress and proposes a concrete next action.
- Scheduled writes are **not enabled**. The launchd files are templates with placeholder paths, not installed jobs.
- `DRY_RUN=true` is the default. A dry run still sends the selected context to the configured API; it does not modify vault files.

## Project structure

| File | Purpose |
| --- | --- |
| `automation/daily_planner.py` | Morning entry point |
| `automation/daily_review.py` | Evening entry point |
| `automation/runner.py` | Context collection, prompts, JSON validation, diff preview and logging |
| `automation/obsidian_utils.py` | Markdown sections, active notes, backup and guarded writes |
| `automation/ai_provider.py` | Provider boundary: `generate_text(prompt)` |
| `automation/config.py` | Loads environment settings relative to the scripts |
| `automation/test_safety.py` | Offline preservation, conflict, validation and template tests |
| `automation/.env.example` | Configuration without a key |
| `launchd/*.plist.example` | Daily 08:00 / 22:30 LaunchAgent templates |
| `REVIEW_GUIDE.md` | Context and questions for a human or AI reviewer |

## Setup

Requires macOS and Python 3.10 or newer. Tested locally with Python 3.14, `google-genai` 2.31.0 and `python-dotenv` 1.2.4. The dependencies have bounded version ranges rather than a complete lockfile.

1. Copy `automation/` into your vault, or keep it in this repository and set `VAULT_PATH` to your vault's absolute path.
2. Create a virtual environment outside iCloud, then install dependencies:

```sh
python3 -m venv "$HOME/Library/Application Support/ObsidianLearning/venv"
source "$HOME/Library/Application Support/ObsidianLearning/venv/bin/activate"
python -m pip install -r automation/requirements.txt
```

3. Create the private configuration without overwriting an existing one:

```sh
cp -n automation/.env.example automation/.env
chmod 600 automation/.env
```

4. Edit `.env` locally, setting `GEMINI_API_KEY` and, when needed, `VAULT_PATH`. Keep `DRY_RUN=true` until both API tests pass. Never paste the key into a chat, commit it or put it in a plist.

The official SDK is [`google-genai`](https://googleapis.github.io/python-genai/). The tested model is `gemini-3.5-flash-lite`, discovered through the Gemini model-list API; availability depends on the account and may change. During testing, `gemini-flash-latest` returned HTTP 503 and `gemini-2.5-flash` was unavailable to new users.

`.gitignore` prevents ordinary accidental Git inclusion of `.env`, logs, backups and the standard vault folders. It does not prevent iCloud from syncing a `.env` placed inside the vault.

## Expected vault layout

```text
00 Inbox/
01 Daily/             # YYYY-MM-DD.md
02 Knowledge/
03 Projects/
04 Courses/
05 Reading/
06 Career/
07 Templates/
99 Archive/
automation/
```

New notes use `07 Templates/Daily Learning Template.md`, falling back to `Learning Template.md`, then the built-in template. Supported date placeholders: `{{date}}` and `{{date:YYYY-MM-DD}}`. No Templater code is executed.

Standard sections are Today's Top 3, Review, Deep Work, What I Learned, What I Practiced, Problems & Questions, Reading, Daily Review and Tomorrow's First Step. Existing English headings work with or without emoji.

## Context sent to Gemini

The morning planner sends yesterday's unfinished tasks and selected active-note summaries. It inspects only the first 40 alphabetically sorted Markdown files directly inside each of Projects, Courses and Career; it does not recurse. It includes at most three active notes per folder, preferring `Priority: High`. Each summary includes Current Goal, Next Actions and Blockers, capped at 1,200 characters.

Example active-note format:

```markdown
# My project
Status: Active
Priority: High

## Current Goal
Finish a small working prototype.

## Next Actions
- [ ] Implement one testable component.

## Blockers
None recorded.
```

The evening review sends the first 14,000 characters of today's note with an explicit truncation flag. Individual files larger than 200 KB are rejected. Other vault folders are not used for AI context.

## Tests and manual runs

```sh
python -m unittest discover -s automation -p test_safety.py -v
python automation/daily_planner.py --dry-run
python automation/daily_review.py --dry-run
```

Each dry run shows files read, prompt size and purpose, the generated response, and the proposed unified diff. `--dry-run` overrides `DRY_RUN=false`. `--date YYYY-MM-DD` selects another day. An evening run requires the day's note to already exist.

For an offline preview, pass `--fixture /absolute/path/to/response.json`; this forces dry run and is explicitly labelled as a fixture rather than a real API result. Response shapes are defined in `runner.py`.

Only after reviewing successful morning and evening API dry runs, set `DRY_RUN=false` locally to allow writes. Run the same scripts without `--dry-run` to write.

### Preservation behavior

Only blank sections, or sections containing empty checkbox placeholders, are filled. Nonempty sections and duplicate headings are preserved. Missing target sections are appended. Repeated runs preserve prior generated text instead of regenerating it.

Existing notes are backed up before a guarded atomic replacement. New notes use exclusive creation. The script checks for concurrent changes before saving and serializes its own local runs with a lock. This does not provide a transaction across Obsidian editors or multiple iCloud devices: finish syncing before writing, and retain backups.

## Logs

Real-writing runs put rotating status logs in `automation/logs/planner.log` and `review.log`. Logs contain timestamps, result, note path and API status, not the key or note content. Backups are created in `automation/backups/`.

Dry-run status logs and the shared lock live outside the vault, under the system temporary directory:

```sh
python -c 'import os,tempfile; print(tempfile.gettempdir()+"/obsidian-learning-"+str(os.getuid()))'
```

Interactive stdout includes the response and diff; treat captured console output as private. The launchd templates discard stdout and direct stderr to `automation/logs/*-launchd-error.log`.

## Optional launchd setup

Do this only after both real API dry runs pass and you intend to enable scheduled writes.

1. Replace every `/ABSOLUTE/PATH/TO/...` placeholder in both `.plist.example` files. The Python path must point to the virtual environment; script and working-directory paths must point to your installation.
2. Create `automation/logs/`. Set `DRY_RUN=false` only when ready to allow writes.
3. Save the edited files as `~/Library/LaunchAgents/local.obsidian.learning.planner.plist` and `local.obsidian.learning.review.plist`. Do not overwrite existing jobs without checking and backing them up.
4. Validate and load them:

```sh
plutil -lint "$HOME/Library/LaunchAgents/local.obsidian.learning.planner.plist"
plutil -lint "$HOME/Library/LaunchAgents/local.obsidian.learning.review.plist"
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/local.obsidian.learning.planner.plist"
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/local.obsidian.learning.review.plist"
```

Morning runs at 08:00, evening at 22:30, using the Mac's local timezone. `RunAtLoad` is false, so loading does not immediately run a job. The user must be logged in; sleep can delay execution, and a powered-off Mac cannot run jobs.

Check jobs and logs:

```sh
launchctl print "gui/$(id -u)/local.obsidian.learning.planner"
launchctl print "gui/$(id -u)/local.obsidian.learning.review"
tail -n 50 automation/logs/planner.log automation/logs/review.log
```

Disable loaded jobs safely:

```sh
launchctl bootout "gui/$(id -u)/local.obsidian.learning.planner"
launchctl bootout "gui/$(id -u)/local.obsidian.learning.review"
```

Restore `DRY_RUN=true`; move the plist files out of LaunchAgents to prevent loading on a later login. This leaves notes and backups intact.

## Troubleshooting and extension

- Missing key: edit the local `.env`; do not print it for diagnostics.
- API failure: check connectivity, model availability, credentials and quota. SDK error bodies are intentionally not printed. There is currently no durable retry queue or automatic model fallback.
- Missing modules: use the virtual environment's Python.
- No diff: the target sections already contain text and are intentionally preserved.
- Concurrent edit: wait for sync to finish and retry a dry run.
- Missing active note: check the folder depth, file-selection limit and `Status: Active` marker.

To add OpenRouter, OpenAI or Ollama, extend the provider selection in `ai_provider.py`, keep secrets in environment variables, and return text matching the current JSON schemas. These providers are not implemented yet.
