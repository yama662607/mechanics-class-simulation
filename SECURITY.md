# Security Policy

## Reporting a Vulnerability

If you discover a security issue in this template (for example, a workflow
that leaks secrets, an unsafe default permission, or a vulnerable pinned
dependency), please report it privately:

- Open a [private security advisory](https://github.com/yama662607/quarto-textbook-template/security/advisories/new), or
- Email the maintainer

Please **do not** open a public issue for security reports.

## Scope

This is a project template — derived repositories own their own deployments.
The maintainers will:

1. Acknowledge receipt within 7 days.
2. Patch the template repository for issues that affect the scaffolding
   itself (e.g. CI permissions, default actions, dependency pins).
3. Note the fix in `CHANGELOG.md`.

## Hardening recommendations for derived repositories

### GitHub Actions
- **Pin third-party Actions to commit SHAs**. The template ships with tag
  pins (`@v3`, `@v4`) for readability; once you go public, replace each
  pin with the corresponding commit SHA. Dependabot is preconfigured
  (`.github/dependabot.yml`) to bump those SHAs weekly.
- Enable **branch protection** on `main`: require the `Quality Checks`
  workflow to pass before merging, and require PR review for production
  textbooks.
- Review `.github/workflows/publish.yml`'s `permissions:` block before
  enabling additional features (downloads, citations, etc.).
- The check workflow drops Git credentials (`persist-credentials: false`)
  to limit token reuse — preserve that when adding new jobs.

### Dependencies
- Run `uv pip audit` (or `uv pip list --outdated`) periodically and
  enable Dependabot security updates in GitHub Settings → Code security.
- Run `npm audit --omit=dev` for Node dependencies.
- Optional features (`easyocr`, `pix2text`, `qiskit`, `shinylive`, etc.)
  pull large transitive trees including ML model frameworks. Only enable
  the extras you actually need (`uv sync --extra <name>`); the default
  base install ships only `pymupdf` + `watchdog`.

### Bootstrap script
- `scripts/bootstrap.py` uses `curl … | sh` for upstream installers (uv,
  just). Inspect `scripts/bootstrap.py` before running on shared machines;
  prefer your distro's package manager when available.

### Secrets and assets
- Never commit files under `quarto/assets/raw/`, `quarto/assets/private/`,
  or `research/inbox/*/` — they are gitignored by default. Verify with
  `git status` before pushing.
- Keep `uv.lock` committed and pin a Python version in CI.

### Migrating to GitHub Pages official deploy artifact
The template uses the legacy `gh-pages` branch deploy (broad `contents:
write` permission). For tighter permissions, migrate to the official
`actions/deploy-pages` artifact workflow — that lets you drop
`contents: write` and use `pages: write` + `id-token: write` only.
See https://github.com/actions/deploy-pages for the migration recipe.
