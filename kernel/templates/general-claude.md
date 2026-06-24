---
type: notes
title: "general-claude"
status: approved
summary: "Template document for organizing project metadata, scope, context, status, and file structure guidelines."
created: 2026-05-13 12:08
updated: 2026-05-13 12:08
owner: Šimon Hradní
client: ~
path: kernel/templates/general-claude.md
tags: [note]
version: "1.0.0"
release: latest
---

<purpose>
{{PROJECT_NAME}}: {{ONE_LINE_DESCRIPTION}}
</purpose>

<context>
- Type: {{community | initiative | research | experiment | other}}
- Status: {{planning | active | paused | completed}}
- Key people: {{WHO_IS_INVOLVED — optional}}
</context>

<scope>
{{WHAT_THIS_IS_ABOUT}}
</scope>

<constraints>
- When code/scripts emerge, put them in scripts/ or src/
- Per-feature docs in docs/ if the project grows
</constraints>
