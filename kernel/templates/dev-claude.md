---
type: notes
title: "dev-claude"
status: approved
summary: "A project documentation template establishing standard format for purpose, status, architecture, local development setup, and feature documentation guidelines."
created: 2026-05-13 12:08
updated: 2026-05-13 12:08
owner: Šimon Hradní
client: ~
path: kernel/templates/dev-claude.md
tags: [note]
version: "1.0.0"
release: latest
---

<purpose>
{{PROJECT_NAME}}: {{ONE_LINE_DESCRIPTION}}
</purpose>

<project>
- Status: {{draft | prototype | mvp | production | archived}}
- Tech stack: {{TECH_STACK}}
- Deploy target: {{WHERE — optional, fill when known}}
</project>

<architecture>
{{KEY_DECISIONS — fill as project evolves}}
</architecture>

<development>
## Run locally
{{HOW_TO_RUN}}

## Dependencies
{{KEY_DEPENDENCIES}}
</development>

<documentation>
Per-feature documentation — every concern gets its own file in docs/features/.
One page = one MD file. Larger topics = subdirectory. Mix granularity freely.
Doc changes belong in the same commit as code changes.
</documentation>
