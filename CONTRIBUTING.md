# Contributing & Git Workflow

This repo follows a **Git Flow** branching model and **Conventional Commits**.
The rules below are enforced by a commit-message hook (see [Setup](#setup)).

---

## Branching model

| Branch | Purpose | Branches from | Merges into |
|--------|---------|---------------|-------------|
| `main` | Production. Auto-deploys the Quarto site via GitHub Actions. | — | — |
| `develop` | Integration branch. Default base for new work. | `main` | `main` (via release) |
| `feature/*` | A new analysis or feature. | `develop` | `develop` |
| `fix/*` | A non-urgent bug fix. | `develop` | `develop` |
| `release/*` | Prep a batch for publishing (final checks, version bump). | `develop` | `main` **and** `develop` |
| `hotfix/*` | Urgent fix to the live site. | `main` | `main` **and** `develop` |

**Only `release/*` and `hotfix/*` merge into `main`.** Everything else flows through `develop`.

### Branch naming

```
feature/2026-canada-analysis
feature/track-dominance-map
fix/tyre-degradation-nan
release/v2026.r08
hotfix/broken-chart-link
```

Use lowercase, hyphen-separated slugs. For race work, prefix with the season + round/name.

---

## Weekly race-analysis workflow

```bash
# 1. Start from an up-to-date develop
git checkout develop
git pull

# 2. Branch for this race
git checkout -b feature/2026-canada-analysis

# 3. Do the work, committing in small, conventional steps
git add notebooks/2026/Canada/
git commit            # opens the template; write a conventional message

# 4. Fold it back into develop (keep the merge commit for history)
git checkout develop
git merge --no-ff feature/2026-canada-analysis
git branch -d feature/2026-canada-analysis

# 5. When ready to publish, cut a release → main → site deploys
git checkout -b release/v2026.r08 develop
# (final checks)
git checkout main
git merge --no-ff release/v2026.r08
git tag -a v2026.r08 -m "Round 8 — Canada"
git push origin main --tags
git checkout develop
git merge --no-ff release/v2026.r08    # keep develop in sync
```

Tags follow `v2026.r<round>` (e.g. `v2026.r08`). Pushing `main` triggers the Pages deploy.

---

## Commit messages — Conventional Commits

Format:

```
<type>(<optional scope>): <subject>

<optional body — what & why, wrapped ~72 cols>

<optional footer — BREAKING CHANGE: ... / Refs #123>
```

### Types

| Type | Use for |
|------|---------|
| `feat` | A new analysis, chart, or capability |
| `fix` | A bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Restructuring without behavior change |
| `perf` | Performance improvement |
| `test` | Adding or fixing tests |
| `build` | Dependencies, packaging (`requirements.txt`) |
| `ci` | GitHub Actions / workflow changes |
| `chore` | Tooling, config, housekeeping |
| `revert` | Reverting a previous commit |

### Suggested scopes

`site`, `utils`, `etl`, `data`, `ci`, `docs`, or a race name (`barcelona`, `canada`).

### Examples

```
feat(barcelona): add corner-by-corner delta-time analysis
fix(site): convert styles.css to scss with layer boundary
refactor: restructure repo into notebooks/, data/, and site layout
build: add pyarrow for parquet output
ci: deploy Quarto site to GitHub Pages on push to main
docs: document the weekly race-analysis workflow
```

The subject is imperative mood ("add", not "added"), ≤ 100 chars, no trailing period.

---

## Setup

Run once after cloning to enable the commit-message hook and template:

```bash
# Windows (PowerShell)
./scripts/setup-git.ps1

# macOS / Linux / Git Bash
sh scripts/setup-git.sh
```

This sets `core.hooksPath=.githooks` and `commit.template=.gitmessage`.

## Recommended branch protection (GitHub)

In **Settings → Branches**, protect `main`:
- Require a pull request before merging
- Require the *Publish Quarto site* status check to pass
