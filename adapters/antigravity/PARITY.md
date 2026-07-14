---
title: "Antigravity adapter - parity with the canonical safety policy"
summary: "Honest gap assessment: enforcement of kernel/safety/safety-policy.md via this adapter is unverified end-to-end; Antigravity's native permission modes are coarse; treat every guardrail here as absent until proven by a hands-on test."
client: ~
status: ai-generated
type: devops
version: "0.1.0"
release: latest
tags: [antigravity, dev-tools, starter-pack, audit, security]
created: 2026-07-14 10:49
updated: 2026-07-14 10:49
owner: Šimon Hradní
path: adapters/antigravity/PARITY.md
---

# Antigravity adapter - parity with the canonical safety policy

`kernel/safety/safety-policy.md` is the single source of truth for what this
pack blocks and why (env-value reads, recursive+forced `rm`, silent-overwrite
`mv`, download-and-execute, subshell/eval bypasses, sensitive credential
reads, destructive disk ops, dangerous docker flags). Claude Code is the
reference implementation - full parity by construction, since it IS what
`safety_check.py` was extracted from. This document says, honestly, how far
that parity reaches for Antigravity - which is: **unverified, at every
layer.**

## Layer 1 - does the hook even run?

Claude Code and Codex have documented, confirmed hook mechanisms. Cursor's
hook mechanism is documented and confirmed (near-1:1 with Claude Code).
**Antigravity's `.agents/hooks.json` is, per the research this adapter is
built from, "mostly community-documented"** - there is no official schema,
and more importantly **no source confirms the editor-less desktop app (this
adapter's actual target) reads `.agents/hooks.json` at all.** The IDE variant
is documented to read `.agents/agents.md` / skills / workflows; whether the
standalone desktop Agent-Manager app shares that same convention is an open
question. If the hook never fires, `antigravity_safety_hook.py` never runs,
and there is zero enforcement - not degraded enforcement, none.

**Verdict: unverified. Do not assume the hook fires until you have tested it
by hand inside the real desktop app** (see `install-notes.md`).

## Layer 2 - if the hook DOES run, does the payload match what we assume?

`antigravity_safety_hook.py` guesses at several plausible JSON field paths for
the command / file path in the hook's stdin payload (documented in the
script's own header as EXTRACTION ASSUMPTIONS). None of those field names are
confirmed. If Antigravity's real payload uses different field names than all
of the guesses, the wrapper will find nothing to check and will allow the
tool call through silently - it does not know the difference between "no
command in this payload" and "a command exists, but under a field name we
didn't guess."

**Verdict: unverified. A wrong guess degrades to zero enforcement, silently,
from the wrapper's point of view** (though not silently from the pack's - see
`install-notes.md`'s hands-on verification step, which is exactly designed to
catch this failure mode before trusting it).

## Layer 3 - if the payload DOES match, does check_command / check_file_read fire correctly?

This layer has real parity. `antigravity_safety_hook.py` imports and calls the
same `check_command()` / `check_file_read()` functions from
`kernel/safety/safety_check.py` that Claude Code, Codex, and Cursor call - not
a re-implementation, the identical decision logic. Anything this layer
receives a well-formed command or file path for, it evaluates exactly like
every other tool in this pack. This is the one layer where "full parity" is
a true statement, conditional on layers 1 and 2 actually delivering the input.

## Layer 4 - Antigravity's own native mechanism (the bonus second layer)

Every other tool in this pack pairs the shared hook with a native
deterministic deny-list as a belt-and-suspenders second layer (Claude Code's
`settings.json` deny array, Codex's Starlark Rules). **Antigravity has no
such mechanism for this adapter to lean on.** Per the research this pack is
built from, Antigravity offers only coarse **permission modes** (broad
allow/ask/deny postures, not pattern-level deny rules) and an **exact-match
allow-list**, plus a `proceed-in-sandbox` mode that has its own documented
bypass bug (`--dangerously-skip-permissions` silently disables `--sandbox` -
see `WARNING.md` §3). None of this is a deterministic pattern-matched
guardrail comparable to what Claude Code or Codex ship natively.

**Verdict: no meaningful native second layer exists to fall back on if the
hook fails to fire.** Unlike Codex (where Starlark Rules still catch most
things if the hook has a gap) or Claude Code (where `settings.json` deny is
a hard OS-level backstop), Antigravity's permission modes are the kind of
coarse, mode-level control the research explicitly calls out as weaker than
a real deny-list.

## Bottom line

**Treat every guardrail in this adapter as absent until you have personally
verified, by hand, inside the real Antigravity desktop app, that (a) the hook
actually fires on a destructive command and (b) the block actually stops the
tool call.** This is not a hedge - it is the honest state of verification as
of this writing. See `install-notes.md` for the exact verification step, and
`WARNING.md` for why this matters more than it would for a tool without
Antigravity's documented security track record.
