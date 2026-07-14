---
title: "Antigravity adapter - read this before you trust any of it"
summary: "Loud, unmissable warning that the Antigravity 2 adapter is experimental, unverified, and sits on top of a tool with open unresolved security findings - conclusion: do not use it on client data."
client: ~
status: ai-generated
type: devops
version: "0.1.0"
release: latest
tags: [antigravity, dev-tools, starter-pack, setup-guide, security]
created: 2026-07-14 10:49
updated: 2026-07-14 10:49
owner: Šimon Hradní
path: adapters/antigravity/WARNING.md
---

# WARNING - read this before touching the Antigravity adapter

## In one sentence

**This adapter is experimental, unverified, and installs on top of a tool that
security researchers found could be prompt-injected into leaking data or
running arbitrary code within 24 hours of its launch. Do not use it on client
data.**

## 1. Nobody has confirmed the desktop app even reads these files

Google Antigravity 2 ships two different products under one name: a classic
IDE (a real code editor, restored by patch on 23 May 2026 after the initial
editor-less release drew backlash) and a separate **standalone desktop
Agent-Manager app with no code editor at all**. This adapter targets the
editor-less desktop app, because that is the one relevant to a non-IDE,
tool-agnostic install.

The IDE is documented to read `.agents/agents.md`, `.agents/skills/*.md`,
`.agents/workflows/*.md`, and a global `~/.gemini/GEMINI.md`
(https://codelabs.developers.google.com/autonomous-ai-developer-pipelines-antigravity).
**No source anywhere confirms the editor-less desktop app reads any of
these same files.** The public docs have not caught up with the IDE/desktop
split. Everything in `adapters/antigravity/` is built against that
documented IDE convention as the closest available analog - it is a
best guess, not a verified fact. Treat every file in this adapter as
"might do nothing at all" until you have hands-on confirmed otherwise on a
real desktop-app install (see `install-notes.md` for the verification step).

Source: https://techcrunch.com/2026/05/19/google-launches-antigravity-2-0-with-an-updated-desktop-app-and-cli-tool-at-io-2026/,
https://www.marktechpost.com/2026/05/19/google-launches-antigravity-2-0-at-i-o-2026-a-standalone-agent-first-platform-with-cli-sdk-managed-execution-and-enterprise-support/

## 2. The global instruction file collides with a different tool

Antigravity's documented global instruction file is `~/.gemini/GEMINI.md` -
the exact same path the separate Gemini CLI tool already uses for its own
global context file. Installing this adapter globally can silently overwrite
or get overwritten by a user's existing Gemini CLI configuration, because
both tools hard-code the same file path.

Source: https://github.com/google-gemini/gemini-cli/issues/16058

## 3. Documented, unresolved security findings - not theoretical

Three independent research groups found serious issues within 24 hours of
Antigravity 2's launch:

- **Mindgard** found a persistent backdoor that survives a full reinstall of
  the app.
- **Adam Swanda** found the system prompt is unsanitized, making it easy to
  inject instructions through content the agent reads.
- **Wunderwuzzi** found five separate holes enabling prompt injection and
  data exfiltration.

**Google's own position is that "the agent follows instructions found in
untrusted content it reads" is accepted behavior, not a bug it intends to
fix.** In the same reporting round, a reviewer's agent read dummy "customer
data" from a test file without ever asking for permission first. Separately,
there is an open bug where the `--dangerously-skip-permissions` flag silently
disables the `--sandbox` protection as well - a user who sets one flag loses
both safeguards without being told.

Source: https://www.infoworld.com/article/4097714/security-researchers-caution-app-developers-about-risks-in-using-google-antigravity-2.html,
https://github.com/google-antigravity/antigravity-cli/issues/36

## 4. Not built for non-developers

There is an open, unresolved feature request on Google's own forum asking for
a "Simple Mode - Antigravity for Non-Developers." The typical non-developer
experience reported is "install, five minutes of confusion, uninstall."
Enterprise-grade compliance controls (data residency, audit logging) exist
only in the separate **Gemini Enterprise Agent Platform Cloud** product - not
in the local desktop app this adapter targets.

Source: https://discuss.ai.google.dev/t/feature-request-simple-mode-antigravity-for-non-developers/126819

## 5. The product itself is a moving target

The editor was removed, then restored, within four days of launch. The MCP
config file path has three different values across sources that are supposed
to describe the same thing. Anything written about Antigravity 2 has a short
shelf life - re-verify before relying on any claim in this adapter, including
the ones in this file.

## Bottom line

**DO NOT use this adapter, or Antigravity 2's desktop app more broadly, on
client data or any data with real confidentiality requirements - not without
the separate, paid Gemini Enterprise Agent Platform Cloud product, which is
the only place Google puts actual compliance controls.** This adapter exists
so a curious, consenting developer can experiment with it on throwaway data,
with eyes open about exactly what is - and is not - protected. See
`PARITY.md` for what the shared safety layer can and cannot enforce here, and
`install-notes.md` for the hands-on verification step you must do before
trusting any of it.
