# Vercel CI setup evals

This suite compares how Cursor models apply the task-discovery and selection
rules in the `vercel-ci-setup` skill. Each run gets a fresh, committed fixture
repository and an installed copy of the skill.

The runner uses Cursor Agent in plan mode. It cannot edit fixtures, install
dependencies, or perform the GitHub and Vercel mutations from the full
onboarding workflow.

## Run the matrix

Authenticate Cursor Agent, then run:

```bash
python3 skills/vercel-ci-setup/evals/run.py
```

The default matrix uses these model IDs:

- `gpt-5.6-sol-medium`
- `claude-sonnet-5-5-high`
- `gemini-4-argon-medium`

Override models, cases, repetitions, or concurrency:

```bash
python3 skills/vercel-ci-setup/evals/run.py \
  --models gpt-5.6-sol-medium,claude-sonnet-5-5-high \
  --cases basic-safe-tasks,environment-risk \
  --runs 3 \
  --jobs 2
```

Validate the fixtures and print the matrix without using model credits:

```bash
python3 skills/vercel-ci-setup/evals/run.py --dry-run
```

By default, raw responses, grades, and a Markdown summary are written under
`.git/vercel-ci-evals/<timestamp>` so eval output does not dirty the checkout.
Use `--output <directory>` to retain results elsewhere.

## Fixtures

`cases.json` covers:

- safe lint, type-check, and unit-test selection;
- environment-variable and deployment risks;
- duplicate task names in package-level Turborepo configurations;
- JSONC and an outdated Turborepo dependency;
- repositories with no safe initial tasks;
- repositories that do not use Turborepo.

Fixtures store virtual file trees in one manifest. The runner materializes each
tree into a temporary Git repository before invoking a model.

## Scoring

Each run receives up to 100 points:

- 20: correct `ready` or `stop` outcome;
- 10: correct stop reason;
- 10: package-manager detection;
- 10: Turborepo dependency detection;
- 10: upgrade determination;
- 40: task-selection precision and recall.

Selecting a forbidden task or more than five tasks is a hard failure and caps
the score at 49. Results include the model's complete structured response so
qualitative evidence and uncertainty can also be reviewed.

This benchmark intentionally isolates read-only analysis. Full workflow tests
for enablement ordering, pull-request failure recovery, rollback, and invocation
polling should use stubbed `gh` and `vercel` commands before any live canary is
added.
