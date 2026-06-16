---
type: core
title: "AGENTS"
status: active
summary: ""
created: 2026-06-13
updated: 2026-06-13
created_by: Šimon Hradní
client: ~
path: workspace/_CLIENTS/taste/AGENTS.md
tags: [agents-manifest]
---

<purpose>
Client project: Taste
{{ONE_LINE_DESCRIPTION}}
</purpose>

<client>
- Company: Taste
- Industry/segment: {{INDUSTRY}}
- Engagement type: {{ENGAGEMENT_TYPE — e.g. fractional ATO, project-based, advisory}}
- Key contacts: {{CONTACTS}}
</client>

<scope>
## What we're building/doing
{{DESCRIPTION}}

## Tech stack (this project)
{{TECH_STACK}}
</scope>

## Structure

| Path | Purpose |
|------|---------|
| `docs/knowledge-base/` | Knowledge about the client — AI reads as source of truth |
| `docs/knowledge-base/drafts/` | Staging area from inbox processing — AI MUST NOT read as source of truth |
| `docs/meetings/transcripts/` | Raw meeting transcripts |
| `docs/assets/` | Logos, images, active visual materials |
| `docs/inbox/` | Client materials (PDFs, presentations) — drop here for processing |
| `docs/inbox/done/` | Processed inbox files |
| `docs/presales/` | Proposals, discovery, scope |
| `docs/strategy/` | Strategic documents (versioned) |
| `docs/strategy/archive/` | Previous major versions |
| `docs/research/` | Per-topic research outputs |
| `docs/review/` | Documents for review |
| `docs/final/` | Finalized documents |
| `projects/` | Concrete projects (each in own subfolder) |
| `research/` | Research outputs |
| `notes.md` | Brain dump, ideas — new notes trigger auto-research |
| `log.md` | Audit trail of automations |
| `docs.md` | Index of finalized documents |
| `meetings.md` | Meeting index — when, topic, key points |
| `worklog.md` | Work log — basis for invoicing |

<constraints>
- Communication language with the client: {{LANGUAGE}}
- Never expose internal tooling, pricing, or other personal context to client-facing outputs
- `docs/knowledge-base/drafts/` is staging — AI must NOT read as source of truth, only review and promote
- `docs/inbox/` is for processing only, not for context
</constraints>

<documentation>
Per-feature documentation in docs/ — every concern gets its own file.
Doc changes belong in the same commit as code changes when applicable.
</documentation>
