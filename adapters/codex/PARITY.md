---
title: "Codex CLI adapter - parity with Claude Code (canonical)"
summary: "What the Codex adapter enforces deterministically, what rides only on the shared hook, the documented coverage gaps, and what has no equivalent at all."
status: ai-generated
type: devops
version: "0.1.0"
release: latest
tags: [starter-pack, codex, safety, parity, dev-tools]
created: 2026-07-14 00:00
updated: 2026-07-14 00:00
owner: Šimon Hradní
client: ~
path: adapters/codex/PARITY.md
---

# Codex CLI adapter - parity with Claude Code

Claude Code (`kernel/`) is this pack's canonical, reference implementation. This document
is the honest degradation report for the Codex adapter, required by the design spec's
"honest degradation" principle: what maps, what is narrower, and why - so nobody assumes
Codex is as safe as Claude Code without reading this first.

## Two independent layers, same as every adapter

1. **The shared brain** - `kernel/safety/safety_check.py`, wired in via
   `codex_safety_hook.py` on Codex's `PreToolUse` hook. This is the ONE enforced core
   shared with Claude Code, Cursor, and (best-effort) Antigravity.
2. **Codex's own native layer** - `rules/default.rules` (Starlark `prefix_rule(...)`), the
   direct analog of Claude Code's `settings.json` `deny` array. This is Codex-specific,
   hand-mirrored from the canonical deny-list, not shared code.

Both layers must be installed for the adapter to mean anything; either one alone is a
partial defense. See install-notes.md for exact install locations.

## Enforced deterministically via Rules (`rules/default.rules`)

Prefix-matched, hard `forbidden` (no prompt), directly mirroring `kernel/settings.json`'s
`deny` array:

- Recursive `rm` in all its flag-bundle forms (`-r`, `-R`, `-rf`, `-rR`, `-fr`, `-fR`)
- Forced `mv -f`
- `sudo`, `chown`
- `chmod -R` / `chmod 777` / `chmod 666` / `chmod +s`
- `mkfs` (bare form only - see gap below)
- `dd` (all invocations - broader than canonical, see gap below)
- `git push --force` / `git push -f` (fixed argv position only - see gap below)
- `git reset --hard`, `git clean -f`, `git clean -d`, `git branch -D`, `git commit --no-verify`
- `npm publish`, `npm install -g`, `npm install --global`
- `pkill`, `shutdown`, `reboot`, `halt`

## Enforced via the shared hook (`codex_safety_hook.py` -> `safety_check.py`)

Cross-cutting, catches these regardless of where in a chained/compound command they hide
(the exact thing a prefix-only Rules match cannot do):

1. Reading secret env VALUES into context (`cat`/`grep`/`source`/redirection/`python -c
   ...read()` etc. targeting `.env` / `.env.*`, excluding `.env.shared` and placeholder
   files) - **for bash-mediated reads only**; see the file-read gap below for the other half.
2. Recursive + forced `rm` **anywhere** in a chained/compound command (`cd build && rm -rf
   .`), not just at argv position 0 - this is exactly what Rules' prefix-only matching
   cannot catch, and the reason the hook exists as a second, independent layer.
3. A plain `mv` that would silently overwrite an existing destination.
4. `curl|sh` / `wget|sh` and two-step download-then-execute.
5. Subshell/eval bypasses carrying a destructive command (`bash -c "...rm -rf..."`, `eval
   "...sudo..."`, `python -c` invoking `os.system`/`shutil.rmtree`/sensitive paths).
6. Reading `~/.ssh` keys, `~/.aws/credentials`, `~/.gnupg`, `~/.git-credentials`, browser
   cookie/session stores - **only when read via a bash command** (`cat`, `less`, `grep`,
   etc.). See the file-read gap below.
7. `dd` to a physical device, `mkfs.*` on a device, `fdisk /dev/*`, fork bombs.
8. Dangerous docker flags: host-root mount (`-v /:/`), `--privileged`, mounting a sensitive
   host path (`.ssh`/`.aws`/`.gnupg`/`.kube`/`.docker`/`.config/gh`).

## Documented coverage gaps (Codex-specific)

- **Rules is prefix-only.** `git push origin --force` (force flag not at argv position 2)
  is not caught by `git push --force` / `git push -f` prefix rules, and the shared hook has
  no force-push check either (it is not in `safety_check.py`'s DANGEROUS list - that check
  is Claude-`settings.json`-native only, same limitation Claude Code itself has today).
- **`mkfs` family.** Only the bare `mkfs` binary is a Rules prefix match; `mkfs.ext4`,
  `mkfs.xfs`, etc. are different `argv[0]` strings Rules cannot generically match. The hook
  backstops the dotted forms via `safety_check.py`'s `mkfs\.[a-z0-9]+\s+/dev/` regex.
- **`dd`.** Rules forbids `dd` outright (broader than canonical, which only targets
  `if=`/`of=` device writes) because Starlark prefix matching cannot express that narrower
  condition at the token level. Documented as an intentional over-block, not an error.
- **Codex does not intercept every shell call.** Per Codex's own hook documentation, the
  newer `unified_exec` execution path is not guaranteed to route through `PreToolUse`, and
  WebSearch / other non-shell tools are not covered either. Edits are only partially
  covered. Neither this hook nor `rules/default.rules` can enforce anything against a call
  Codex itself never routes through a hookable mechanism.
- **File-path reads are a real gap, not just a documented one.** Rules is scoped to command
  execution only - it has zero mechanism to block a file-path read. `safety_check.py`'s
  `check_file_read` only protects `.env` / `.env.*` files (mirroring Claude Code's own
  `Read` hook branch exactly). Claude Code's *additional* protection for `~/.ssh/**`,
  `~/.aws/**`, `~/.gnupg/**`, browser cookie stores, keychains, etc. when read via a
  **native** Read-style tool (not bash) lives entirely in `settings.json`'s `deny` array -
  a Claude-native permission-engine feature Codex's Rules mechanism cannot express at all
  (see the mechanism note in `rules/default.rules`). For Codex, those same sensitive paths
  are protected only when accessed **via a bash command** (covered by item 6 above); if
  Codex has (or gains) a native, non-shell file-read tool, reading `~/.ssh/id_rsa` through
  it directly is currently **unprotected** for Codex. This is the single largest real gap
  in this adapter and should be re-verified once Codex's native read-tool behavior is
  confirmed hands-on.
- **Codex hook JSON schema is an educated guess.** `codex_safety_hook.py`'s field-extraction
  paths (`COMMAND_PATHS`, `FILE_PATH_PATHS`) are assumptions, clearly marked in that file's
  docstring, because the exact PreToolUse payload shape was not published in the research
  this adapter was built from. If the real shape differs, the hook may silently find
  nothing to check (fails open, per its own design) rather than fail loudly - re-verify
  against a real Codex install before trusting this in production, per install-notes.md's
  verification step.

## What has no equivalent at all for Codex

- **`disableBypassPermissionsMode`.** Claude Code's setting that locks off its own bypass
  mode has no confirmed Codex analog in the research this adapter was built from. Not
  addressed here - flag for follow-up if Codex ships an equivalent "skip all
  sandboxing/approval" flag.
- **`~/.bashrc` / `~/.zshrc` / `~/.ssh/**` Edit-and-Write denies.** These are Claude-native
  permission-engine entries with no Rules equivalent (again: Rules is command-execution
  only). Codex's `sandbox_mode = "workspace-write"` (see config.toml) provides a coarser,
  different kind of protection - it restricts writes to the workspace root rather than
  naming specific sensitive files - so the two are not equivalent, just both present.
