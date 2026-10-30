# Vercel CI Details

Vercel-specific facts for the setup skill. Prefer the [Vercel CI documentation](https://vercel.com/docs/ci) when it covers the same thing; use these when it is unavailable or silent, and say so in the pull request.

## Requirements

- Turborepo 2.11.7 or later.
- A private GitHub repository linked to a Vercel project on the team.

## Opting tasks in

Add the `ci` tag to each selected task in the Turborepo configuration where the task is defined. Keep every other property, existing tag, and JSONC comment.

```json
{
  "tasks": {
    "lint": { "tags": ["ci"] }
  }
}
```

To opt a task in for specific packages only, tag it in those packages' configurations instead of the root, when the documentation supports it:

```json
{
  "extends": ["//"],
  "tasks": {
    "build": { "tags": ["ci"] }
  }
}
```

## Repository settings

Read the settings:

```bash
vercel api "/v1/vercel-ci/repository-settings?provider=github&organizationId=<owner>&repository=<repo>" --scope <team> --raw
```

The repository is enabled when `ciEnabledAt` is present.

Enable Vercel CI with `vercel ci enable --remote <remote> --scope <team>`. If that command is unavailable, send `{"ciEnabled":true}` as a `PATCH` to the same settings route. Never set `ciEnabledAt` yourself. Read the settings again to confirm.

## Finding the run

Runs are created asynchronously after the push, so poll briefly:

```bash
vercel ci list --branch <branch> --commit <sha> --scope <team> --json
```

A run's dashboard URL is `https://vercel.com/<team-slug>/~/ci/<invocation-id>`. Read a run's logs with `vercel ci logs <invocation-id> --scope <team>`.
