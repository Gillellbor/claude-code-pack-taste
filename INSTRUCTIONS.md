---
type: notes
title: "Instructions for Claude - Pack Installation"
status: approved
summary: "You are reading this because the user just cloned the Claude Code Pack and ran `claude` in the repo root."
created: 2026-06-16 00:52
updated: 2026-06-16 16:59
owner: Šimon Hradní
client: ~
path: INSTRUCTIONS.md
tags: [note]
version: "1.0.0"
release: latest
---

# Instructions for Claude - Pack Installation

You are reading this because the user just cloned the Claude Code Pack and ran `claude` in the repo root. Your job is to walk them through installation **safely and interactively**, with explicit confirmation at every major step. Treat the user as a smart power-user who hasn't done this before - explain what each step does, ask before touching anything outside the repo, and respect their preferences (path, OS, names).

**Hard rules for this install session:**
- Do not silently run install commands. Show the command, get approval, then execute.
- After running, report the result in one line.
- Terse, no narration. The user can read.
- If the user says "skip this", skip it and note what was skipped.
- If anything fails, stop. Don't continue to the next step.
- Never use `rm -rf` during install - use `mv` to a backup path instead.
- Never use `sudo`. If something requires it, instruct the user to run that one command manually.

---

## Step 0 - Greet, confirm intent, set the frame

Open with:

> Připravím tvůj Claude Code podle Pack. Ujistím se předem, co budu měnit a kam to půjde. Žádný krok neprovedu bez tvého potvrzení. OK pokračovat?

Wait for explicit yes.

Then explain what's coming, in one paragraph:

> Instalace má dvě části:
> 1. **Kernel** - globální nastavení do `~/.claude/` (settings, hooks, rules, skills, statusline). Pravidla pro to, co Claude smí a nesmí, plus pomocné nástroje.
> 2. **Workspace** - adresářová struktura pro tvou práci (klienti, vlastní projekty, nástroje, kontext). Tu si umístíš kam chceš.
>
> Před každou částí se zeptám na tvé preference. Pokud někde už máš svůj setup, zálohujeme ho, nepřepisujeme.

---

## Step 0.5 - Vyzvi uživatele k plan modu a napiš plán

Než cokoli zkopíruješ, zálohuješ nebo upravíš na stroji, **napiš plán** a získej souhlas. Nejčistší cesta je plan mode, který tě nutí plán prezentovat dřív než exekvuješ.

**Vyzvi uživatele, ať přepne:**

> „Pro nejbezpečnější instalaci stiskni v terminálu **Shift+Tab** a přepni se do plan modu. V něm můžu jen prezentovat plán - nic nespustím, dokud ho neschválíš. Jakmile Shift+Tab stiskneš, řekni mi, a napíšu plán."

Počkej, až uživatel potvrdí, že přepnul. (Sám plan mode nemusíš spolehlivě detekovat - spolehni se na jeho potvrzení.)

**Pak spusť Krok 1 (read-only pre-flight) a napiš plán.** Dobrý plán shrnuje:
- Výsledky OS + dependency kontroly (z Kroku 1 - čistě read-only, smí běžet i bez schváleného plánu)
- Jestli zálohovat stávající `~/.claude/` a kam
- Workspace location a názvy adresářů
- Které soubory se zkopírují, kam, a co zůstává netknuté
- Které credential / personalizační otázky zbývají
- Přesný seznam příkazů, které spustíš, v pořadí

V plan modu prezentuj plán přes `ExitPlanMode`. Uživatel ho tam schválí, plan mode skončí, ty vykonáš. **Neimprovizuj mimo plán.** Když se objeví něco neočekávaného, zastav, aktualizuj plán, znovu potvrď.

**Pokud uživatel plan mode odmítne** (řekne, že nechce přepínat, neumí najít Shift+Tab, nebo prostě „jeď bez něj"):

1. Vytvoř `./INSTALL-PLAN.md` v aktuálním adresáři (klonovaný Pack folder).
2. Napiš tam stejný plán.
3. Uživateli ho ukaž v terminálu (vypiš obsah nebo shrň a odkaž).
4. Počkej na explicit schválení: „ano", „OK", „pokračuj", „approve", nebo podobně.
5. Teprve po souhlasu začni vykonávat.
6. Po dokončení instalace (Krok 11) `./INSTALL-PLAN.md` smaž - pracovní artefakt, ne výstup.

V obou cestách: **žádná destruktivní akce ani kopírování neproběhne, dokud uživatel neschválí písemný plán.** Krok 1 (read-only kontroly) je jediná věc, která smí běžet před plánem.

---

## Step 1 - Pre-flight check

Run these checks and report results in a single message.

### 1a. Detect OS

```bash
uname -s
```

- **Darwin** → macOS, all instructions apply as written.
- **Linux** → adjust paths if user uses non-standard `~/Documents/` location; otherwise same as macOS.
- **MINGW / MSYS / CYGWIN** or PowerShell → **Windows.** Stop and tell the user:

  > Tento Pack předpokládá Unix-like shell. Na Windows je nejčistší cesta **WSL2** (Ubuntu z Microsoft Store, Claude Code uvnitř WSL, Pack pak funguje jako na Linuxu).
  >
  > Nativní Windows je možný, ale vyžaduje ruční úpravy cest (`%USERPROFILE%` místo `$HOME`, zpětná lomítka, žádné symlinks bez admin), Bash hooky se musí přepsat na PowerShell nebo spouštět přes Git Bash. Pro první instalaci to nedoporučuju.
  >
  > Co chceš: (a) ukončit a nainstalovat WSL2, (b) pokračovat na nativním Windows i tak?

  Pokud volí (b), pokračuj podle Windows addendum na konci tohoto souboru.

### 1b. Detect required binaries

```bash
for tool in python3 node git jq curl; do
  if command -v "$tool" >/dev/null 2>&1; then
    printf '%s ✓ (%s)\n' "$tool" "$("$tool" --version 2>&1 | head -n1)"
  else
    printf '%s ✗ MISSING\n' "$tool"
  fi
done
```

If **all present**, continue.

If **anything is missing**, stop and give the user OS-specific install commands. Do NOT install dependencies yourself - that's a system change that needs the user's explicit choice of how to manage their package manager.

**macOS - recommended via Homebrew:**
```bash
# If brew itself is missing:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Then:
brew install python3 node git jq curl
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt update && sudo apt install -y python3 nodejs git jq curl
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install -y python3 nodejs git jq curl
```

After the user installs missing tools, run the check again. Do not proceed until all five pass.

### 1c. Detect existing setup

Run in parallel:

```bash
ls -la ~/.claude/ 2>/dev/null | wc -l
ls -la ~/.claude/settings.json 2>/dev/null
ls -la ~/.claude/.env 2>/dev/null
```

Report: does `~/.claude/` exist, is there a `settings.json`, is there a `.env`. These all matter for the backup step.

---

## Step 2 - Workspace location interview (BEFORE touching ~/.claude/)

This is the most important preference question. The Pack ships with four workspace directories - `_CONTEXT`, `_CLIENTS`, `_BUSINESS`, `_APPS` - and you must NOT assume where they go. Different users want them in different places. **Frame it as a proposal, not a fixed layout** - present the structure as the pack's suggestion and explicitly invite the user to shape it: "tohle je navrhovaná struktura, pojďme ji probrat a nastavit, jak to chceš mít ty."

Ask the user:

> Pack obsahuje čtyři workspace adresáře:
> - `_CONTEXT/` - tvůj osobní profil, poznámky, best-practices
> - `_CLIENTS/` - per-klient složky
> - `_BUSINESS/` - vlastní byznys (projekty, vzdělávání, interní)
> - `_APPS/` - nástroje a appky, které stavíš
>
> **Kam je chceš umístit?**
> 1. `~/Documents/` (default - viditelné ve Finderu, snadné mít přes ruku)
> 2. `~/` (přímo v home directory)
> 3. `~/Documents/Work/` nebo jiná podsložka - řekni jakou
> 4. Mimo home, např. `/Volumes/Work/` (externí disk) nebo `~/Code/`
>
> Cesty s mezerami fungují, ale doporučuju je nepoužívat - Bash je nemá rád.

Store the chosen base path. **Use it for the rest of the install.** Never fall back to `~/Documents/` after they chose something else.

### 2a. Optional renaming

```
Chceš některý z adresářů přejmenovat?
- Některým lidem podtržítkový prefix (_CLIENTS/) pomáhá vizuální sort. Jiným vadí.
- Někdo preferuje plain anglické: clients/, business/, apps/, context/.
- Někdo česky: klienti/, byznys/, appky/, kontext/.

Pošli mi čtyři jména oddělená mezerou pro CONTEXT CLIENTS BUSINESS APPS - nebo Enter pro defaults.
```

Use whatever they say. From this point on, refer to directories by the user's chosen names - not by the defaults.

### 2b. Conflict check

For each chosen directory, check if it already exists at the chosen base path:

```bash
for dir in <name1> <name2> <name3> <name4>; do
  if [ -e "<base-path>/$dir" ]; then echo "EXISTS: $dir"; else echo "free: $dir"; fi
done
```

If any exist: **never overwrite.** Tell the user, and offer:
1. Skip that one (don't copy from the Pack, keep the user's existing content)
2. Rename the Pack's version (e.g. add `-new` suffix) so the user can merge manually
3. Abort and let the user move/rename their existing dir first

---

## Step 3 - Backup existing `~/.claude/`

If `~/.claude/` exists from Step 1c, propose:

```bash
cp -r ~/.claude ~/.claude.bak-$(date +%Y%m%d-%H%M%S)
```

Get user approval. After backup, report the backup path.

If `~/.claude/` does not exist, skip this step and tell the user.

---

## Step 4 - Install kernel

Show the user what will be copied:

```
kernel/ → ~/.claude/
```

Contents going in:
- `settings.json` - restrictive baseline; bypass mode locked off
- `AGENTS.md` + `CLAUDE.md` (symlink)
- `statusline.sh` - 3-line status bar (model · cost / project · ctx / 5h · 7d rate limits)
- `rules/` - six rules (documentation, frontmatter-standard, respect-denies, subagents, notes, language)
- `scripts/list-env-keys.sh` - lets Claude see *names* of credential env vars without values
- `hooks/`:
  - `safety/safety_check.py` (PreToolUse Bash+Read) - blocks bypass patterns and protected env reads; shared by all tool adapters
  - `context-bloat-guard.py` (PreToolUse Read) - soft brake on huge file reads
  - `notes-research.sh` (PostToolUse Edit/Write) - auto-research on `notes.md` markers
  - `inject-current-time.sh` (UserPromptSubmit) - current time in every prompt
- `skills/setup/`, `skill-creator/`, `prd-creator/`, `dr-prompt/`, `client-data-check/`, `idea-file-creator/`
- `templates/` - five scaffolding templates: klient, dev, business, app, general
- `agents/` - `prompt-engineer`, `research-analyst` + README

**Critical - existing setup: analyze, recommend, don't overwrite.** If `~/.claude/settings.json` (or a `rules/`/`hooks/` directory) already existed in the backup, do NOT blindly replace it. First read the user's existing config - permissions, hooks, env, rules - and compare it against what this pack ships. Then present a tailored, area-by-area recommendation: what of theirs is worth keeping, what the pack adds that's worth adopting, where the two overlap or conflict, and a suggested result tuned to how this user actually works (ask briefly if it's not obvious). The user decides per area; then write the agreed result. Replace wholesale only if there is nothing meaningful there or they ask for it. The backup protects the original either way - the install never auto-merges JSON, so the merged result is written explicitly.

Execute the copy:

```bash
cp -r kernel/. ~/.claude/
chmod +x ~/.claude/scripts/*.sh ~/.claude/hooks/*.{sh,py} ~/.claude/safety/*.py ~/.claude/statusline.sh
```

Re-create the `~/.claude/CLAUDE.md` symlink (it may not have copied as a symlink):

```bash
cd ~/.claude && ln -sfn AGENTS.md CLAUDE.md
```

Verify:

```bash
ls -la ~/.claude/CLAUDE.md
```

Should show `CLAUDE.md -> AGENTS.md`.

---

## Step 5 - Personal profile interview

The `user-profile.md` file in `<context-dir>/` is read by Claude across all sessions. The more accurate it is, the more tailored the work.

Quick interview - 4 questions, 1–2 sentences each, or "skip" to leave blank:

```
1. Tvoje role a hlavní zaměření?
   (např. „PPC specialista v agentuře, učím se Python automatizace" nebo „Strategist, vedu klientské transformace")

2. S jakými technologiemi / AI nástroji nejvíc pracuješ?
   (např. „Google Sheets, BigQuery, Claude Code, někdy n8n")

3. Jaký styl komunikace ode mě chceš?
   - terse / balanced / detailed
   - mám ti přímo říkat, když je tvůj plán špatný? (ano / ne)

4. Jaký jazyk pro vlastní práci?
   (např. „česky klientské dokumenty a poznámky, anglicky kód a systémové soubory")
```

Write the answers into `<base-path>/<context-dir>/user-profile.md`, replacing the empty placeholders in the template.

---

## Step 6 - Example content choice

```
Pack obsahuje příklady, které můžeš nechat, přejmenovat nebo smazat:
- `_CLIENTS/_example-client/` - sample klientská struktura
- `_CLIENTS/taste/` - připravený scaffold pro Taste (klient autorů Packu)
- `_APPS/_example-app-transcribe/` - stub appka demonstrující `_APPS` layout

Co s nimi?
1. Nech vše (default - referenční)
2. Přejmenuj `_example-client` na reálné jméno klienta (řekni které)
3. Smaž příklady, ponech `taste/`
4. Smaž všechny příklady včetně `taste/` - začneš čistě
```

Apply choice. If deleting, use `mv` to a backup path, not `rm -rf`:

```bash
mv "<base-path>/<clients-dir>/_example-client" "<base-path>/.removed-examples/$(date +%Y%m%d-%H%M%S)-example-client"
```

---

## Step 7 - Workspace copy

Copy the workspace directories using the user's chosen paths and names from Step 2:

```bash
mkdir -p "<base-path>"
# For each: cp -r workspace/<default-name>/ → <base-path>/<chosen-name>/
```

**Never overwrite an existing top-level directory.** If `<base-path>/<chosen-name>` already exists, skip and tell the user (already flagged in Step 2b).

After copy, re-create AGENTS.md ↔ CLAUDE.md symlinks in each project subfolder. Symlinks may not survive `cp` cleanly:

```bash
# Find every AGENTS.md and ensure CLAUDE.md sibling is a symlink to it
find "<base-path>" -name 'AGENTS.md' -not -path '*/node_modules/*' | while read -r agents; do
  dir=$(dirname "$agents")
  if [ ! -L "$dir/CLAUDE.md" ]; then
    (cd "$dir" && ln -sfn AGENTS.md CLAUDE.md)
  fi
done
```

---

## Step 8 - Credential store (`~/.claude/.env`)

The Pack uses `~/.claude/.env` as the central place for API keys. The `notes-research` hook reads `ANTHROPIC_API_KEY` from this file. Other API keys can be added here too - the `list-env-keys.sh` helper lets Claude see their *names* (not values) when needed.

If `~/.claude/.env` doesn't exist, create it with a starter template:

```bash
cat > ~/.claude/.env <<'EOF'
# Claude Code credential store. Loaded by hooks. NEVER commit this file.
# Format: KEY=value (no quotes needed for simple strings)

# Required for the notes-research hook (cost: tokens per trigger)
ANTHROPIC_API_KEY=

# Optional - override the default research model (defaults to Haiku for cost)
# ANTHROPIC_MODEL=claude-haiku-4-5-20251001

# Add other API keys as you need them. Examples:
# OPENAI_API_KEY=
# GEMINI_API_KEY=
# GITHUB_TOKEN=
EOF
chmod 600 ~/.claude/.env
```

Ask the user to add their `ANTHROPIC_API_KEY` value (or skip - auto-research will silently no-op until they add it).

Show how the env-keys helper works:

```bash
~/.claude/scripts/list-env-keys.sh
```

Their `ANTHROPIC_API_KEY` (and any other credentials they added) should appear by name. Values never appear in the output.

### The one readable env file - `.env.shared`

`~/.claude/.env` above is the GLOBAL credential store for hooks; Claude never reads its values. The model has three tiers: the global `~/.claude/.env` and every project `.env` / `.env.local` / `.env.production` / `.env.*` are HARD - Claude never reads their values (`.env.local` is HARD on purpose; the JS ecosystem treats it as the live-secret file, so live keys land there). The single readable env file is **`.env.shared`** - the soft tier for low-risk values safe to surface (a notify webhook, a contact email). The deny rules plus the `bash-safety-extended.py` hook block reading every HARD `.env` / `.env.*` (via `cat`, `source`, redirection, `python -c`, docker bind-mount, or the Read tool). A real secret is never read by Claude - a program uses it without revealing the value. To see only the key NAMES of any HARD env file, Claude runs `~/.claude/scripts/list-env-keys.sh --from <path>` (add `--classify` for each key's state). Scope note: only commands that read the *values* into view are blocked (`cat`, `source`, redirection, `python -c ...read()`); passing the file as config (`--env-file`), copying a template, or mentioning it in text all pass, so deploys and setup are not blocked.

---

## Step 8.5 - Pre-trust the workspace (optional, stops the folder-trust nag)

On first launch in any directory, Claude Code shows **"Do you trust the files in this folder?"** and the user must accept. This is a deliberate safety gate; there is no `settings.json` key or safe env var to disable it (bypass mode would skip it, but it is locked off here on purpose). The supported way to stop the repeated prompt for directories the user already trusts is to pre-write the per-directory trust flag into `~/.claude.json`. The kernel ships `~/.claude/scripts/trust-workspace.sh` for exactly this.

Offer to pre-trust the workspace base path from Step 2 and each directory created in the workspace copy:

```bash
~/.claude/scripts/trust-workspace.sh <base-path>/<chosen-dir-1> <base-path>/<chosen-dir-2>
```

- It backs up `~/.claude.json`, merges (never overwrites), and validates JSON before saving.
- It weakens nothing else: normal permission prompting and `disableBypassPermissionsMode` stay fully in force. It only persists "yes, I trust this folder" up front, exactly as clicking Yes would.
- Brand-new directories opened later still prompt once - correct for a safety baseline. Re-run the script for those, or just accept once.
- The install session is itself a Claude Code session, so if the prompt persists after the Step 9 restart, have the user run the command once more from a plain terminal (a running session can overwrite `~/.claude.json` on exit).

---

## Step 9 - Verification

Tell the user to **restart their Claude Code session** so the new `settings.json` takes effect. After restart, they can verify:

- `~/.claude/scripts/list-env-keys.sh` returns env var names without values
- A denied command (e.g. asking Claude to `cat .env`) gets blocked, but a deliberate `.env.shared` is readable (the single readable soft tier)
- Bypass mode is off - `claude --permission-mode bypassPermissions` should refuse
- The current-time injection works - at session start, Claude should know the actual time
- Statusline appears at the bottom with model · cost · context · rate-limit info

---

## Step 10 - Lock settings.json

During this install session, Claude was able to freely edit `~/.claude/settings.json`. **At the end, lock it down.** Future sessions should prompt before any change to the kernel config:

```bash
python3 -c "
import json
from pathlib import Path
p = Path.home() / '.claude' / 'settings.json'
s = json.load(open(p))
ask = s.setdefault('permissions', {}).setdefault('ask', [])
for rule in ['Edit(~/.claude/settings*)', 'Write(~/.claude/settings*)']:
    if rule not in ask:
        ask.append(rule)
json.dump(s, open(p, 'w'), indent=2)
print('settings.json locked: future edits to ~/.claude/settings* require user approval')
"
```

After this step, Claude can still modify settings.json - but each modification requires the user to confirm.

---

## Step 11 - Hand off

Tell the user:

> Hotovo. Doporučuju:
> - Nainstalovat **[Warp](https://www.warp.dev/)** jako terminál - přehlednější a přívětivější příkazová řádka. Výhody: file explorer hned vedle terminálu, normální zadávání textu (píšeš jako v editoru, bez terminálových výstředností), přehlednější organizace oken a snazší navigace ve složkách. Claude Code v něm běží úplně stejně. Ve free verzi v úvodním nastavení **vypni vlastní AI Warpu** - když používáš Claude Code, AI od Warpu nepotřebuješ.
> - Přečíst `docs/safety-model.md` - co všechno se blokuje a proč.
> - Přečíst `docs/customization.md` - jak Pack rozšiřovat.
> - Přečíst `docs/prompting-claude.md` - tipy na práci s Claude.
>
> Tento repo můžeš teď smazat - všechno je nainstalováno v `~/.claude/` a tvých workspace adresářích.

The Warp recommendation is written Mac-first (Warp's original ecosystem). Warp also ships a Windows build, so if the user is on Windows, point them at the Windows download and adapt - do not present it as Mac-only.

End the install session. Do not proceed to other tasks unless the user asks.

---

## Error handling - global rules

- If any step fails, stop. Do not continue to the next step.
- If a permission denial occurs during install (e.g. user runs from a path that doesn't allow writes), surface it clearly and propose a fix.
- Never run `rm -rf` during install. Use `mv` to a backup path.
- Never use `sudo`. If something requires it, instruct the user to run that one line manually.

---

## Windows native (without WSL) - addendum

If the user chose Windows native despite the WSL recommendation:

- Replace `~/.claude/` with `%USERPROFILE%\.claude\` (`$env:USERPROFILE\.claude\` in PowerShell)
- Replace `~/Documents/` similarly
- Symlinks require admin rights - instead of `ln -s AGENTS.md CLAUDE.md`, create a hard link or just copy the file (two files to keep in sync - flag this to the user)
- `chmod +x` is a no-op on Windows. PowerShell scripts need `Unblock-File` before first run
- Bash hooks (`*.sh`) won't run natively - they need Git Bash, WSL, or a PowerShell rewrite
- `~/.claude/.env` is a regular file. PowerShell env loading differs; the user will need to source it manually or via a profile script

Strongly recommend WSL2. The Pack assumes Unix conventions throughout - fighting Windows native is more work than installing WSL.
