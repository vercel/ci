---
name: vercel-ci-setup
description: Set up Vercel CI for a Vercel project or linked private GitHub repository. Use when onboarding a repository, selecting recommended Turbo tasks, creating the task-tag pull request, or enabling Vercel CI.
---

# Vercel CI Setup

## Preconditions

1. Run the skill from a local checkout of the repository being onboarded.
2. Identify the Vercel team and either a project ID/name or GitHub `owner/repo`. Do not infer the team from a local project link.
3. Resolve a project to its GitHub link, then confirm the resulting `owner/repo` with the user.
4. Confirm the repository is private and connected to at least one project owned by that team.
5. Confirm the repository uses Turborepo 2.11.7 or newer. If it does not, stop and report the required minimum version; upgrading Turborepo is outside this workflow.
6. Use the installed Vercel CLI and its authenticated context. Pass the intended team with `--scope <team-slug-or-id>` and never put a token in a command or output.

Vercel CI currently onboards private GitHub repositories that are linked to a project on the selected team. Public repositories, unlinked repositories, and repositories linked only to another team are not supported.

The released `vercel ci` namespace inspects and reruns existing CI runs; it does not provide onboarding commands. Use the raw `vercel api "/v1/vercel-ci/..."` commands below, not operation-ID dispatch. For mutations, write JSON to a temporary file, set mode `600`, pass it with `--input`, and remove it afterward. URL-encode path and query values.

## Workflow

### 1. Resolve and confirm the repository

The goal is one confirmed private GitHub repository linked to the selected Vercel team.

If the user supplies a project, prefer its immutable project ID over its name and fetch it in the explicit team scope:

```bash
vercel api "/v9/projects/<url-encoded-project-id-or-name>" \
  --scope <team> \
  --raw
```

Require the response `accountId` to match the selected team. Read the repository only from `link.org` and `link.repo`; do not infer it from the project name. Require `link.type` to be `github`.

Stop if the project does not exist in that team, has no `link`, uses another Git provider, or lacks `link.org` or `link.repo`. If a project name could refer to more than one intended target, ask for the project ID.

Show the project ID/name, team, and inferred GitHub `owner/repo`, then ask the user to confirm that repository before starting analysis. A local `.vercel/project.json` may supply a candidate project ID, but it does not establish team scope or authorize setup.

If the user supplies `owner/repo` directly, retain it as the candidate and continue to the linked-repository checks. The repository remains the canonical target for every setup endpoint even when setup starts from a project.

Require the local checkout's remote to match the confirmed repository.

### 2. Inspect repository settings

The goal is to record whether Vercel CI was enabled before this workflow so a failed setup can restore the original state.

Read settings with:

```bash
vercel api "/v1/vercel-ci/repository-settings?provider=github&organizationId=<url-encoded-github-owner>&repository=<url-encoded-github-repository>" \
  --scope <team> \
  --raw
```

Record `ciEnabled`, `ciEnabledAt`, and the canonical repository identity returned by the API. A disabled result is expected for a repository being onboarded.

### 3. Start task analysis

The goal is a completed, read-only analysis of the confirmed repository before any onboarding writes.

Starting analysis is asynchronous and does not modify the repository:

```bash
analysis_request=$(mktemp)
chmod 600 "$analysis_request"
printf '%s\n' '{"owner":"<github-owner>","repo":"<github-repository>"}' > "$analysis_request"
vercel api "/v1/vercel-ci/task-analyses" \
  --scope <team> \
  -X POST \
  --input "$analysis_request" \
  --raw
rm -f "$analysis_request"
```

Keep the returned `analysisId` for status, task-list, and pull-request requests. If the request outcome is uncertain, do not start another analysis because an unknown ID cannot be recovered.

### 4. Wait for completion

The goal is a completed analysis from the current default-branch revision.

Poll the same analysis with bounded waits:

```bash
vercel api "/v1/vercel-ci/task-analyses/<url-encoded-analysis-id>" \
  --scope <team> \
  --raw
```

- `pending`: wait, then inspect the same ID again. Large monorepos can take several minutes.
- `completed`: continue.
- `failed`: show `failureReason` and offer to start a new analysis.

Analysis results expire after 24 hours. Never treat an unchanged `pending` state as failure by itself.

### 5. Collect and review tasks

The goal is an exact user-approved selection of recommended tasks before enabling Vercel CI or creating a pull request.

List tasks with `limit=100`, following every `pagination.nextCursor` until absent:

```bash
vercel api "/v1/vercel-ci/task-analyses/<url-encoded-analysis-id>/tasks?limit=100" \
  --scope <team> \
  --raw
```

Append `&cursor=<url-encoded-next-cursor>` for each subsequent page.

For each task, present:

- `configPath`
- `name`
- `recommendationReasons`

Reasons currently include `lint`, `typecheck`, `test`, `unit-test`, and `github-actions`. An empty reasons array means the task is not recommended.

Ask the user to approve the exact recommended-task selection before creating a pull request. The endpoint accepts only tasks from this analysis with at least one recommendation reason, rejects duplicates, and accepts 1–100 tasks. Preserve both `configPath` and `name`; task names alone are not unique across multiple Turbo configs.

### 6. Link variables only when needed

The goal is to identify required credentials without exposing or copying secret values.

Do not copy or expose secret values during setup. If tasks need credentials, offer to link existing Shared Environment Variables to the repository through the Shared Variable repository-link API before enablement. Show variable names and targets only, ask the user to approve each link, and never print values.

Repository task analysis and pull-request creation do not require variable linking. Skipping this step is valid.

### 7. Enable CI and create the configuration pull request

The goal is an enabled repository and a configuration pull request containing the approved tasks, with no enabled-but-unconfigured repository left behind after a definitive failure.

After task and variable selections are approved, ask for confirmation to enable Vercel CI and create the setup pull request as one workflow. If the repository was disabled, enable it first:

```bash
enable_request=$(mktemp)
chmod 600 "$enable_request"
printf '%s\n' '{"ciEnabled":true}' > "$enable_request"
vercel api "/v1/vercel-ci/repository-settings?provider=github&organizationId=<url-encoded-github-owner>&repository=<url-encoded-github-repository>" \
  --scope <team> \
  -X PATCH \
  --input "$enable_request" \
  --raw
rm -f "$enable_request"
```

Read the settings again and require `ciEnabled: true` before continuing. If enablement fails or cannot be verified, do not create the pull request.

Immediately submit the exact task selection:

```bash
selection_request=$(mktemp)
chmod 600 "$selection_request"
printf '%s\n' '{"tasks":[{"configPath":"turbo.json","name":"build"}]}' > "$selection_request"
vercel api "/v1/vercel-ci/task-analyses/<url-encoded-analysis-id>/pull-request" \
  --scope <team> \
  -X POST \
  --input "$selection_request" \
  --raw
rm -f "$selection_request"
```

The API adds `ci` tags to the selected runnable tasks and returns the pull-request URL plus `changedTaskNames`. It refuses stale analysis when the default branch head changed; start a new analysis instead of applying stale recommendations.

If the request outcome is uncertain, repeat it only with the exact same analysis and selection. The endpoint uses a deterministic branch and returns an existing open pull request for that selection.

If pull-request creation definitively fails and the repository was disabled before this workflow, restore the previous state:

```bash
disable_request=$(mktemp)
chmod 600 "$disable_request"
printf '%s\n' '{"ciEnabled":false}' > "$disable_request"
vercel api "/v1/vercel-ci/repository-settings?provider=github&organizationId=<url-encoded-github-owner>&repository=<url-encoded-github-repository>" \
  --scope <team> \
  -X PATCH \
  --input "$disable_request" \
  --raw
rm -f "$disable_request"
```

Verify the rollback. Do not disable a repository that was already enabled before setup. If the pull-request outcome remains uncertain, resolve it with the exact same analysis and selection before deciding whether rollback is appropriate.

Do not merge the pull request unless the user explicitly asks. Review its diff and Vercel CI result while the repository remains enabled.

## Recovery

- `public_repository_not_supported`: stop; this setup path supports private repositories only.
- `not_found`: verify team scope, GitHub owner/repository spelling, and that the team has a linked project for the repository.
- `task_analysis_dispatch_failed`: the analysis was marked failed; a new analysis can be started.
- `task_analysis_not_completed`: continue polling rather than listing tasks or creating a PR.
- `task_analysis_expired` or `task_analysis_stale`: if setup enabled a previously disabled repository, restore its disabled state; then start a new analysis and obtain selection approval again.
- `task_analysis_has_no_recommended_tasks`: report that automated setup found no eligible tasks; do not invent a selection.
- `invalid_task_selection`: refresh all task pages and rebuild the selection from recommended tasks only.
- `turbo_config_unavailable` or `turbo_config_invalid`: restore a previously disabled repository, then stop and report the affected configuration; do not hand-edit it as though the endpoint succeeded.
- `task_configuration_unchanged`: report that the selected tasks already have CI tags. If setup enabled a previously disabled repository, ask whether to keep CI enabled because no setup pull request will be created.

## Completion

Report the repository, team, analysis ID, approved task count, pull-request URL, variable links created, and final `ciEnabled` state. Clearly distinguish analysis completion, pull-request creation, pull-request merge, and repository enablement; none implies the next.
