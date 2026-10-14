# Local Vercel CI Onboarding

Use this reference while following the goals and workflow in the parent `SKILL.md`.

## Check CLI capabilities

Require the installed Vercel CLI to support both commands:

```bash
vercel api --help
vercel ci list --help
```

If either command is unavailable, stop and ask the user to upgrade Vercel CLI. Do not silently substitute operation-ID dispatch or an unreleased command.

## Resolve the repository

If the user supplies a Vercel project, prefer its immutable project ID over its name:

```bash
vercel api "/v9/projects/<url-encoded-project-id-or-name>" \
  --scope <team> \
  --raw
```

Require the response `accountId` to match the selected team and `link.type` to equal `github`. Read the repository only from `link.org` and `link.repo`; do not infer it from the project name.

Compare the resulting `owner/repo` with the local checkout's GitHub remote. Ask the user to confirm the repository before continuing. A local `.vercel/project.json` can provide a candidate project ID, but does not establish the team or authorize setup.

Read repository settings:

```bash
vercel api "/v1/vercel-ci/repository-settings?provider=github&organizationId=<url-encoded-owner>&repository=<url-encoded-repository>" \
  --scope <team> \
  --raw
```

Record `ciEnabled`, `ciEnabledAt`, and the canonical repository identity. Stop if the repository is public, unlinked, linked only to another team, or does not match the local checkout.

## Discover runnable tasks

Keep discovery read-only:

1. Require a root `turbo.json` or `turbo.jsonc` and a declared `turbo` dependency. Stop and report that this skill supports only Turborepo repositories if either is absent.
2. Detect the package manager from the root `package.json` and lockfile.
3. Read the root `package.json`, workspace definition, root Turbo configuration, package manifests, and package-level Turbo configurations.
4. Collect each task declared under `tasks` that has a matching non-empty script in the root or at least one applicable workspace package.
5. Preserve the task's Turbo config path and full task name. A task name alone is not unique across package-level configurations.
6. Inspect `.github/workflows/**/*.yml` and `.github/workflows/**/*.yaml` for Turbo tasks already exercised in CI.

Do not install dependencies or invoke Turbo during discovery. If dependencies are absent, invoking Turbo can use a different global version or create repository guidance files, violating read-only analysis. Perform runtime validation only after approval when the repository's declared version is installed.

Use task names as initial recommendation signals:

- lint tasks;
- type-checking tasks such as `typecheck`, `type-check`, `check-types`, or `tsc`;
- unit-test tasks such as `unit-test`, `unittest`, or `test:unit`;
- other focused test tasks.

Task names are only signals. Confirm scripts, dependencies, and environment requirements before recommending them.

## Prefer low-dependency tasks

Prefer focused lint, type-check, and unit-test tasks that require no secrets, environment variables, deployments, or external services.

Strong candidates:

- linting;
- static type checking;
- unit tests with no external services;
- focused tests already running in GitHub Actions.

Do not recommend these by default:

- builds;
- end-to-end, integration, smoke, or deployment tasks;
- tasks that deploy applications or depend on deployment tasks;
- tasks requiring databases, browsers, cloud credentials, or external services;
- tasks whose environment requirements cannot be determined.

Inspect applicable Turbo definitions for:

- `env`;
- `passThroughEnv`;
- `globalEnv`;
- `globalPassThroughEnv`;
- dependencies on deployment or environment-provisioning tasks.

Also inspect package scripts and existing workflows for environment setup. Do not claim that a task needs no environment variables merely because Turbo declares none. Describe the available evidence and call uncertainty out explicitly.

Group available tasks by config path and task name. Present the recommended subset with:

- task name and config path;
- recommendation reason;
- whether GitHub Actions already runs it;
- relevant dependencies;
- declared or observed environment requirements.

Offer the complete available-task list on request instead of printing every package-level instance.

Present the recommended tasks, exclusions, Turbo upgrade, and files to change. Ask once: “Proceed with these tasks and create the onboarding PR?” Explain that approval covers repository enablement, file changes, push, and pull-request creation. After approval, complete the workflow without asking again.

## Prepare the combined change

Require a clean working tree. Fetch the remote default branch and create a new branch from its latest commit. Never discard unrelated local work.

Determine the Turborepo version from the repository's dependency declaration and lockfile. If it is older than 2.11.7:

1. Show the current and proposed versions before obtaining approval.
2. Preserve the repository's dependency style and version policy.
3. Update the root Turborepo dependency to a compatible release at or above 2.11.7.
4. Run the detected package manager's install command to regenerate its lockfile.
5. Never hand-edit the lockfile.

If dependencies are absent and no upgrade is needed, install the lockfile's existing dependency versions after approval so validation uses the repository's declared Turbo version.

For each approved task, add `ci` to its `tags` array in the applicable Turbo configuration:

```json
{
  "tasks": {
    "test": {
      "tags": ["ci"]
    }
  }
}
```

Preserve existing tags, formatting, and JSONC comments. Do not add a task that is absent from that configuration.

Validate that:

- the resolved Turborepo version is at least 2.11.7;
- each edited Turbo configuration parses;
- every selected task still has a matching non-empty package script;
- every selected task has the `ci` tag;
- no unapproved task was changed.

Review the complete diff, commit it using the repository's commit style, and push the branch. Do not open the pull request yet.

## Enable Vercel CI

Only after the branch is ready and pushed, enable Vercel CI immediately before pull-request creation:

```bash
enable_request=$(mktemp)
chmod 600 "$enable_request"
trap 'rm -f "$enable_request"' EXIT
printf '%s\n' '{"ciEnabled":true}' > "$enable_request"
vercel api "/v1/vercel-ci/repository-settings?provider=github&organizationId=<url-encoded-owner>&repository=<url-encoded-repository>" \
  --scope <team> \
  -X PATCH \
  --input "$enable_request" \
  --raw
rm -f "$enable_request"
trap - EXIT
```

Read settings again and require `ciEnabled: true`. If enablement fails or cannot be verified, do not create the pull request.

## Create the pull request

Create one pull request containing both the Turborepo upgrade, when required, and the approved task tags:

```bash
gh pr create \
  --base <default-branch> \
  --head <setup-branch> \
  --title "Set up Vercel CI" \
  --body "<summary of selected tasks, Turbo upgrade, and validation>"
```

If the command outcome is uncertain, look for an open pull request with the same head branch before retrying.

If pull-request creation definitively fails and the repository was disabled before this workflow, restore the previous state:

```bash
disable_request=$(mktemp)
chmod 600 "$disable_request"
trap 'rm -f "$disable_request"' EXIT
printf '%s\n' '{"ciEnabled":false}' > "$disable_request"
vercel api "/v1/vercel-ci/repository-settings?provider=github&organizationId=<url-encoded-owner>&repository=<url-encoded-repository>" \
  --scope <team> \
  -X PATCH \
  --input "$disable_request" \
  --raw
rm -f "$disable_request"
trap - EXIT
```

Verify the rollback. Never disable a repository that was enabled before onboarding.

## Find the invocation

After the pull request exists, get its head branch and commit SHA. Poll with bounded waits:

```bash
vercel ci list \
  --branch "<setup-branch>" \
  --commit "<commit-sha>" \
  --scope <team> \
  --json
```

When an invocation appears, report its status and construct its dashboard URL:

```text
https://vercel.com/<team-slug>/~/ci/<invocation-id>
```

Return the pull-request URL and, once available, the Vercel CI invocation URL. Do not wait indefinitely. If no invocation appears, report that it is still pending and return the exact lookup command with the pull-request URL.
