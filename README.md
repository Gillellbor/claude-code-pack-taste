---
type: core
title: "Claude Code Pack - Taste edition"
status: approved
summary: "Baseline Claude Code configuration tuned for an agency power-user cohort: ambassadors and technically curious marketers who write Python scripts, build small apps with Claude Code, and do knowledge wo"
created: 2026-06-13 21:07
updated: 2026-06-13 21:07
owner: Šimon Hradní
client: ~
path: README.md
tags: [readme]
version: "1.0.0"
release: latest
---

# Claude Code Pack - Taste edition

Baseline Claude Code configuration tuned for an agency power-user cohort: ambassadors and technically curious marketers who write Python scripts, build small apps with Claude Code, and do knowledge work day-to-day.

Forked and adapted from [Gillellbor/claude-starter-pack](https://github.com/Gillellbor/claude-starter-pack). Differences from upstream are listed at the bottom.

> **Audience:** the 10–15 person ambassador / power-user layer in an agency. Smart enough to install dependencies and read errors. Not enterprise IT.

## Pro úplné začátečníky (česky)

Pokud je tvoje zkušenost s AI claude.ai a nic víc - začni krátkým [**`UZIVATELSKY-MANUAL.md`**](UZIVATELSKY-MANUAL.md). Přečteš za půl minuty, dozvíš se, co Pack dělá a proč.

## What you get

### Kernel (`~/.claude/`)
- **Restrictive `settings.json`** - destructive bash patterns, sensitive file reads, browser cookie/history dirs, and `--no-verify` style escapes are denied at the global level. Bypass mode is locked off.
- **Bash safety hook** - catches two-step download-execute, subshell bypasses, a recursive `rm` hidden in a chained command, a `mv` that would silently overwrite an existing file, secret-file reads (every `.env` / `.env.*` except the readable `.env.shared` soft tier and non-secret templates, via bash or the Read tool), browser data extraction, and `python -c` bypasses.
- **Context-bloat guard** - soft brake on `Read` of files larger than ~50k tokens. Forces Claude to either chunk the read or ask the user to confirm. Prevents the "Claude loaded an 80MB CSV and now the session is dead" scenario.
- **Auto-research hook** - detects unmarked notes in `notes.md`, dispatches background research via the Anthropic API, marks each as ✅ (research done) or ⏭️ (skipped).
- **Time-injection hook** - adds the current local time to Claude's context every prompt.
- **Statusline** - three-line live status (model · throughput · cost / project · branch · context / 5-hour and 7-day rate-limit usage). Lets you see when you're burning through your team-plan allotment.
- **Six rules** - documentation standard (incl. frontmatter standard pointer), respect-denies behavior (updated three-tier env model), subagent usage guide, notes convention, language (which language to use, plus native-Czech style: banned AI calques, typography), frontmatter standard.
- **Six skills** - `setup` (project scaffolding, with template-based gitignore/env schema and local git autosave), `skill-creator`, `prd-creator`, `dr-prompt`, `client-data-check` (PII scanner for files before they leave the machine), `idea-file-creator` (capture an idea as a self-contained, leak-free idea file for handoff or later).
- **Two agents** - `prompt-engineer` (author/refine/validate any prompt or skill, model-aware), `research-analyst` (focused single-topic lookup with sourced verdict inline).
- **Helper scripts** - `list-env-keys.sh` exposes *names* of credential env vars without ever revealing values; `env-key-classify.py` adds value-state classification (empty/placeholder/filled+kind); `git-autosave.sh` local-only git safety net for any work folder.
- **Ignore + env templates** - `gitignore`, `claudeignore`, and per-workspace-type `.env.example` schemas (`klient`, `dev`, `app`, `general`) plus `.env.shared` skeleton. The `setup` skill copies these automatically.

### Workspace (chosen path, default `~/Documents/`)
- `_CONTEXT/` - personal profile, notes, best-practices.
- `_CLIENTS/` - per-client engagements, including a pre-built `taste/` scaffold to start with.
- `_BUSINESS/` - your own work outside any single client (offers, training material, internal projects).
- `_APPS/` - small tools and apps you build (one example included).

You choose where these live during install - no `~/Documents/` lock-in.

### File convention
Every project root has both `AGENTS.md` (canonical, cross-tool standard) and `CLAUDE.md` (symlink to AGENTS.md). One source of truth, readable by Claude Code, Cursor, Codex, Gemini CLI, Aider, and any other AGENTS.md-aware tool.

## Install

You don't run an install script. You let Claude walk you through it.

```bash
git clone https://github.com/<your-org>/claude-code-pack-taste.git ~/Downloads/claude-code-pack-taste
cd ~/Downloads/claude-code-pack-taste
claude
```

Claude reads `INSTRUCTIONS.md` in the current directory, runs a pre-flight check (OS, dependencies, existing setup), and asks for your approval at every major step - including **where you want your workspace directories to live**. It does not assume `~/Documents/`.

If you already have a `~/.claude/` setup, the install respects it - backup is automatic, nothing is overwritten without your confirmation.

### Dependency expectations

The Pack assumes `python3`, `node`, `git`, `jq`, and `curl` are on PATH. If anything is missing, Claude stops and gives you the install command for your OS - it does not install dependencies for you (that's a system change you should make explicitly).

- **macOS:** Homebrew (`brew install python3 node git jq curl`)
- **Linux (Debian/Ubuntu):** `apt install python3 nodejs git jq curl`
- **Linux (Fedora/RHEL):** `dnf install python3 nodejs git jq curl`
- **Windows:** WSL2 strongly recommended. Native Windows works but requires manual path adjustments and PowerShell rewrites of Bash hooks - see the Windows addendum in `INSTRUCTIONS.md`.

## What this is not

- **Not a turnkey product.** You will edit files, add your own rules, and shape this to your work.
- **Not a hard cost cap.** Team-plan limits are per-seat, and hard token caps would block real work. The Pack ships the statusline so you can *see* your usage; what you do with that is up to you.
- **Not enterprise-grade.** The safety model protects against accidents and AI mistakes - not against a determined adversary on your machine. For locked-down environments, use endpoint-managed settings (`/Library/Application Support/ClaudeCode/managed-settings.json`).
- **Not a magic context for every AI tool.** AGENTS.md gives portable intent across tools, but each tool's deeper config (settings, permissions, hooks) is vendor-specific.

## Differences from the upstream starter pack

What changed in this fork:

- **Statusline added** (`kernel/statusline.sh`) - three-line live status with cost, context, and 5h/7d rate-limit usage. Important for team-plan visibility.
- **Browser data added to deny** - Safari/Chrome/Chromium/Firefox/Brave/Edge/Arc cookie and history directories are unreadable. Vibe-coded scripts shouldn't quietly mine your session cookies.
- **`context-bloat-guard.py` hook added** - soft brake on huge file reads.
- **Bash safety hook extended** - browser data extraction patterns, `python -c` bypass patterns, a recursive-rm-in-a-chained-command guard and a mv-overwrite guard, updated `.env.shared` soft-tier model.
- **`language.md` rule added** - single authority for which language to use (English for system files, Czech for chat and deliverables) plus native-Czech style that blocks AI calques.
- **`client-data-check` skill added** - offline PII scanner.
- **`inbox-processor.sh` hook removed** - per-edit API calls were nudging team-plan usage; teams can re-enable it from the upstream if they want.
- **`_CLIENTS/taste/` scaffold included** - pre-built example client workspace.
- **INSTRUCTIONS.md interactive interview rewritten** - explicit workspace-path prompt (no `~/Documents/` assumption), OS-specific dependency setup, conflict checks before any overwrite.
- **Frontmatter standard added** (`rules/frontmatter-standard.md`) - unified OKF-aligned YAML frontmatter for every markdown artifact, closed type buckets, predefined tag vocabulary.
- **Two agents added** - `prompt-engineer` and `research-analyst` with full validation and source-citing constraints.
- **`env-key-classify.py` + `git-autosave.sh` added** - env value-state classifier (names+kind only, never values); local-only git time machine for any work folder.
- **Ignore + env templates added** - `gitignore`, `claudeignore`, and per-type `.env.example` + `.env.shared` schemas; `setup` skill copies them automatically.
- **Env model updated** - three-tier model (global `~/.claude/.env` HARD / project `.env*` HARD / `.env.shared` SOFT) replaces the old `.env.local`-as-readable exception. `respect-denies.md`, `setup` skill, `INSTRUCTIONS.md`, `UZIVATELSKY-MANUAL.md`, and `docs/safety-model.md` document this consistently.
- **`idea-file-creator` skill added** - capture a thought as a self-contained, leak-free, machine-readable idea file (an ADR for ideas) for handoff or parking for later.
- **Permission lists tuned** - `allow` widened to cover safe day-to-day commands (read-only inspection, build tools, media tooling like `ffmpeg`/`magick`, broad `git`, `docker`/`ssh`) so they do not nag; install-class (`npm install`, `pip install`, `brew`), network-reaching (`scp`/`rsync`), and `git push`/`rebase`/`merge` stay in `ask`; destructive forms stay denied. Two `bash-safety-extended.py` guards added: recursive-rm in a chained command, and a mv that would overwrite an existing file.

## License

**All rights reserved.** This Pack is shared publicly so the Taste ambassador cohort (and other authorized individuals) can install it and use it as their daily Claude Code configuration - including for client work. That use is explicitly permitted.

What's **not** permitted without written approval: redistributing, republishing, rehosting, forking publicly, packaging it as a commercial product or service offering of your own, or using the contents for ML model training.

This Pack is derived from [Gillellbor/claude-starter-pack](https://github.com/Gillellbor/claude-starter-pack), which is MIT-licensed. The MIT-licensed upstream portions retain their original license. See `LICENSE` and `NOTICE` for the full terms.

For permissions beyond what the license covers: simon@hradni.net
