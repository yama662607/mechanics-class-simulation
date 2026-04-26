# CLAUDE.md

This file is intentionally short. The line below uses Claude Code's
**memory import syntax** (`@path/to/file`) to pull in the full agent
guide from `AGENTS.md`. It is NOT a broken file or placeholder — Claude
Code resolves `@AGENTS.md` at load time and merges its contents into
the active context. See:
https://docs.claude.com/en/docs/claude-code/memory#claude-md-imports

@AGENTS.md

<!--
Add Claude-specific overrides BELOW this line if you ever need them.
They will merge with the imported AGENTS.md content. By default, all
editing rules, the mandatory PDF ingestion workflow, and forbidden
actions live in AGENTS.md so every agent (Codex / Cursor / Copilot /
Gemini / Claude) sees the same rules.
-->
