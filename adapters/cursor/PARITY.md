---
title: "Cursor adapter - parity with Claude Code (canonical)"
summary: "Honest degradation report for the Cursor adapter: what of Claude Code's safety model it enforces, what it drops, and why."
status: draft
type: devops
version: "0.1.0"
release: latest
tags: [starter-pack, cursor, safety, dev-tools, parity]
created: 2026-07-14 00:00
updated: 2026-07-14 00:00
owner: Šimon Hradní
client: ~
path: adapters/cursor/PARITY.md
---

# Cursor adapter - parity with Claude Code

Claude Code (`kernel/`) is canonical. This adapter derives from it and realizes as
much of `kernel/safety/safety-policy.md` as Cursor's own mechanisms allow. Where it
falls short, that gap is named here rather than silently accepted.

## 1. The deterministic deny lives ENTIRELY in the hook - there is no native backstop

Claude Code has two independent layers: `settings.json`'s `deny` array (exact
pattern match, enforced by the Claude Code binary itself, before any hook even
runs) and the `safety_check.py` hook underneath it. Codex has an analogous second
layer (`rules/*.rules`, Starlark prefix-match). Cursor has **no equivalent** -
its own native "allowlist" (`permissions.json` / `block_instructions`) is,
by Cursor's own documentation, **an LLM classifier reading plain-English
instructions**, explicitly described as "best-effort guardrails rather than a
hard security boundary" (cursor.com/docs/agent/security/run-modes). It is not
deterministic and this pack does not rely on it for anything.

Consequence: for this adapter, `cursor_safety_hook.py` wired to
`beforeShellExecution` / `beforeReadFile` in `hooks.json` **is** the entire
deterministic safety boundary. If that hook does not run (misconfigured path,
Cursor version drops the event, the process crashes before checking in), there
is nothing else in Cursor stopping a destructive command or a secret-value read
- only the classifier, which is explicitly not a security boundary.

Because the hook is Cursor's only deterministic layer, the shared core carries the
FULL canonical policy for it, not just the bypass-detection subset: `safety_check.py`'s
POLICY_DENY (sudo, chmod -R, chown, git push --force, git reset --hard, git clean,
git branch -D, git commit --no-verify, npm publish/-g, pkill, shutdown/reboot/halt,
mkfs, dd, launchctl, mv -f) and SENSITIVE_READ (ssh/aws/gnupg/kube/gh/keychains/browser)
are enforced here through this hook exactly as they are for Claude Code.

This is why `hooks.json` sets `"failClosed": true` on both hook entries here,
unlike the implicit "hook failure just doesn't block" posture that is
acceptable in Claude Code (which still has `settings.json` deny as a backstop).
On Cursor, a hook that times out or crashes with `failClosed: true` blocks the
action instead of silently letting it through with zero deterministic
protection. `timeout: 5` (seconds) bounds how long a misbehaving hook can hang
the agent before Cursor gives up and (per `failClosed`) denies. The check
itself is pure regex/stat work and should return in low single-digit
milliseconds in the overwhelming majority of cases, so this is not expected to
cause real friction - it is a deliberate trade of rare added friction for
never silently losing the only deny mechanism this tool has.

## 2. Global behavioral rules cannot be a home-dir file (Cursor-specific gap)

Claude Code's `~/.claude/CLAUDE.md` (symlinked from `kernel/AGENTS.md`) is a real
file on disk, installed once, read on every project. Cursor's "User Rules"
equivalent lives inside the app's own settings storage - **there is no
`~/.cursor/rules/*.mdc` global drop-in the bootstrap can write to** (confirmed:
cursor.com/docs/context/rules; community discussion at
forum.cursor.com/t/support-global-agents-md/150406 tracks this as an open gap,
not yet shipped).

`rules/pack-baseline.mdc` in this adapter is therefore a **workspace-level**
rule (`alwaysApply: true`), copied into every project's `.cursor/rules/` by the
bootstrap - once per project, not once for the whole machine. It intentionally
does not duplicate `kernel/AGENTS.md`'s full text (see "Derive, don't
duplicate" in the design spec); it points to the project's own `AGENTS.md`
(which Cursor also reads natively at the project root) and inlines only the
handful of non-negotiables that must survive even if the AGENTS.md pickup does
not fire in some Cursor surface. Practical effect: a user who works across
many small Cursor projects gets the baseline reapplied per project by the
bootstrap, not for free the way a single home-dir file would give Claude Code.

## 3. Sandbox is an OS-level bonus layer, not the enforcement mechanism, and is weaker on native Windows

`sandbox.json` (this adapter) is Cursor's own OS-level jail - a genuinely
separate, useful defense layer, but it is *not* what `safety-check.py` is: it
is optional (ships here, but nothing requires it to be installed), and its
strength depends on the OS. On macOS and Linux it is a real OS-enforced
boundary (Seatbelt / Landlock+seccomp per the research doc). **On native
Windows, Cursor's sandbox does not have an equivalent native primitive and
runs inside WSL2** - so a user on native (non-WSL2) Windows either does not get
this layer at all, or must be routed through WSL2 to get it, same as Claude
Code's own Windows story in the design spec ("WSL2 = recommended path").
`cursor_safety_hook.py` itself has no such gap - it is plain Python and runs
identically on native Windows, WSL2, macOS, and Linux; only `sandbox.json`'s
protection degrades on native Windows, not the deterministic hook.

## 4. No "ask" tier - the shared core is binary (allow/deny), Cursor's schema supports a third state it never gets

Cursor's documented output schema for `beforeShellExecution` allows
`"permission": "ask"` in addition to `allow`/`deny`. The shared
`safety_check.py` core (`check_command` / `check_file_read`) only ever returns
a block reason or `None` - a pure binary decision, by design, so it behaves
identically across every tool adapter. `cursor_safety_hook.py` therefore never
emits `"ask"`. Anything Cursor might want to gate as "ask a human first"
(package installs, `git push`, `docker rm`, ...) is out of scope for this
deterministic layer in every tool, including Claude Code, where the equivalent
sits in `settings.json`'s separate `ask` array - Cursor has no matching native
mechanism to receive that list today (its own allowlist being the LLM
classifier described in point 1), so that tier of protection does not port to
Cursor at all in this version of the adapter.

## 5. `cwd` handling - a correctness nuance specific to Cursor's hook shape, not a gap

`safety_check.py`'s `mv_overwrite_target()` check does real filesystem stats
(`os.path.isdir`, `os.path.lexists`) against relative paths, which only work if
the process's actual working directory matches where the command would really
run. Claude Code's hook subprocess presumably inherits the session's real cwd;
Cursor's `beforeShellExecution` stdin instead hands the wrapper an explicit
`"cwd"` field. `cursor_safety_hook.py` `os.chdir()`s into that path before
calling `check_command()` for exactly this reason - documented here so a
future maintainer does not "clean up" what looks like a redundant chdir.

## Summary table

| Layer | Claude Code (canonical) | Cursor (this adapter) |
|---|---|---|
| Deterministic deny | `settings.json` deny (pre-hook) + `safety_check.py` hook | `safety_check.py` hook only - no native backstop |
| Global behavioral baseline | `~/.claude/CLAUDE.md`, one file, whole machine | `.cursor/rules/pack-baseline.mdc`, one file per project |
| OS sandbox | permission model only (no OS jail) | `sandbox.json` - real OS jail on macOS/Linux, WSL2-only on native Windows |
| Third "ask" tier | `settings.json` `ask` array | not available - Cursor's only native alternative is a non-deterministic LLM classifier |
| Windows | native, bash hooks need Git Bash / rewrite | hook script is native Python (fine); sandbox needs WSL2 |
