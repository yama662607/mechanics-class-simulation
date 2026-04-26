# GEMINI.md

This file is intentionally short. The line below uses Gemini CLI's
**`@import` syntax** to pull in the full agent guide from `AGENTS.md`.
It is NOT a broken file or placeholder — Gemini CLI resolves `@AGENTS.md`
at load time and merges its contents into the active context. See:
https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md

@AGENTS.md

<!--
Prefer Gemini CLI to read AGENTS.md directly without this wrapper?
Configure ~/.gemini/settings.json:

  { "context": { "fileName": ["AGENTS.md", "GEMINI.md"] } }

All editing rules, the mandatory PDF ingestion workflow, and forbidden
actions live in AGENTS.md so every agent (Codex / Cursor / Copilot /
Gemini / Claude) sees the same rules.
-->
