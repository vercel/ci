# Vercel CI Onboarding Reference

Detailed rules for each step in the parent `SKILL.md`. Commands assume the Vercel CLI, `git`, and the GitHub CLI; when your environment provides other tools for the same operation, use those instead.

## When Vercel CI documentation is unavailable

Continue with this reference when the documentation cannot be fetched or does not specify an operation, and note in the result that current documentation could not be verified. Use these fallbacks:

- Turborepo 2.11.7 is the minimum version.
- Opt tasks in with the `ci` tag under [Prepare the combined change](#prepare-the-combined-change).
- Enable Vercel CI with the commands under [Enable Vercel CI](#enable-vercel-ci).

## Check CLI capabilities

When using the Vercel CLI, prefer dedicated commands when they support the required operation. Fall back to `vercel api` only for onboarding operations that the installed CLI does not expose.

```bash
vercel api --help
vercel ci list --help
```

If neither the CLI nor another source of Vercel API access supports an operation you need, stop and explain what is missing, such as an outdated Vercel CLI. Do not use operation-ID dispatch or unreleased commands.

## Resolve the repository

If the request supplies a Vercel project, prefer its immutable project ID over its name. Start with the dedicated project command:

```bash
vercel project inspect <project-id-or-name> --scope <team>
```

If the command does not return the canonical GitHub link, fall back to the raw project route:

```bash
vercel api "/v9/projects/<url-encoded-project-id-or-name>" \
  --scope <team> \
  --raw
```

Require the response `accountId` to match the selected team and `link.type` to equal `github`. Read the repository only from `link.org` and `link.repo`; do not infer it from the project name. A local `.vercel/project.json` can provide a candidate project ID, but does not establish the team or authorize setup.

When the request names the repository, use it without asking again. Otherwise, confirm the resolved `owner/repo` with the user when one is available.

Read repository settings:

```bash
vercel api "/v1/vercel-ci/repository-settings?provider=github&organizationId=<url-encoded-owner>&repository=<url-encoded-repository>" \
  --scope <team> \
  --raw
```

The repository is enabled when `ciEnabledAt` is present; `ciEnabled` is derived from it. Stop if the repository is public, unlinked, linked only to another team, or does not match the checkout's GitHub remote.

## Check for an earlier setup

Look for an open pull request from an earlier setup run before doing any other work:

```bash
gh pr list --repo <owner>/<repo> --state open --search '"Set up Vercel CI" in:title' --json number,url,headRefName
```

If one exists, report its URL and stop. Do not open a second setup pull request; update the existing one only when the user asks.

Name the setup branch `vercel-ci/setup`. If that branch already exists on the remote without an open pull request, use `vercel-ci/setup-<short-default-branch-sha>` instead.

## Discover runnable tasks

Keep discovery read-only:

1. Require a root `turbo.json` or `turbo.jsonc` and a declared `turbo` dependency. If either is absent, stop and explain that Vercel CI requires Turborepo, linking the [Vercel CI documentation](https://vercel.com/docs/ci).
2. Detect the package manager from the root `package.json` and lockfile.
3. Read the root `package.json`, workspace definition, root Turborepo configuration, package manifests, and package-level Turborepo configurations.
4. Collect each task declared under `tasks` that has a matching non-empty script in the root or at least one applicable workspace package.
5. Preserve the task's Turborepo config path and full task name. A task name alone is not unique across package-level configurations.
6. Inspect `.github/workflows/**/*.yml` and `.github/workflows/**/*.yaml` for Turborepo tasks already exercised in CI.

Do not install dependencies or invoke `turbo` during discovery. If dependencies are absent, invoking `turbo` can use a different global version or create repository guidance files, violating read-only analysis. Perform runtime validation after selecting tasks, when the repository's declared version is installed.

## Choose tasks

Gather evidence for each discovered task before deciding:

- its Turborepo definition: `env`, `passThroughEnv`, `globalEnv`, `globalPassThroughEnv`, and any dependency on deployment or environment-provisioning tasks;
- its package scripts, for signs of databases, browsers, deployments, or required secrets;
- any GitHub Actions job that runs it, including the job's `secrets`, `env`, `services`, and setup steps.

Then decide with one rule: **select a task unless the evidence shows it needs secrets, deployments, or running services.** Missing evidence is not a reason to leave a task out; select it and note the uncertainty in the pull request. In practice:

- Lint, type-check, formatter-check, and unit-test tasks are usually selected, across every package that defines them.
- Select a build task only when GitHub Actions already runs it without secrets. Framework builds often read environment variables that Turborepo never declares.
- Leave out tasks that deploy or depend on deployment tasks, tasks that need databases, browsers, or other running services, and tasks whose scripts or workflows use secrets or cloud credentials. These become candidates.

Decide per package, not per task name. A shared task often qualifies in some packages and not others, such as a `build` that GitHub Actions runs only for one app. When the Vercel CI documentation supports opting a task in for specific packages, for example in a package-level Turborepo configuration, opt in only the packages that qualify and list the others as candidates. When it does not, leave the task out and explain which packages would qualify.

Record each selected task with its config path and task name, package count, the reason it qualifies, whether GitHub Actions already runs it, and any uncertainty. Record each candidate with the reason it was left out. Never print every package-level instance.

When a user is available, show the selected tasks and the candidates, and let them add or remove tasks before you edit files. When your environment asks you to propose a plan for approval, put both lists in the plan. Otherwise, proceed with the selection. Stop only when the repository is ambiguous or no task qualifies.

If Vercel CI is already enabled and every selected task already opts in, the repository is already set up. Report that instead of opening an empty pull request.

## Prepare the combined change

Work in a clean working tree. Fetch the remote default branch and create the setup branch from its latest commit. Never discard unrelated local work; if the existing checkout has unrelated changes, use a separate clone or worktree.

Determine the Turborepo version from the repository's dependency declaration and lockfile. If it is older than the minimum in the current Vercel CI documentation:

1. Record the current and proposed versions in the pull-request summary.
2. Preserve the repository's dependency style and version policy.
3. Update the root Turborepo dependency to a compatible release at or above the documented minimum, and never below 2.11.7.
4. Run the detected package manager's install command to regenerate its lockfile.
5. Never hand-edit the lockfile.

If dependencies are absent and no upgrade is needed, install the lockfile's existing dependency versions so validation uses the repository's declared `turbo` version.

Configure each selected task using the current task opt-in syntax from the Vercel CI documentation. Preserve existing task configuration, formatting, and JSONC comments. Do not add a task that is absent from that configuration.

If the documentation is unavailable or does not state the opt-in syntax, add the `ci` tag to each selected task:

```json
{
  "tasks": {
    "check-types": {
      "tags": ["ci"]
    }
  }
}
```

Preserve every other task property and existing tag, add `ci` only once, and apply the fallback in the Turborepo configuration where the selected task is defined. Do not use this fallback when the current documentation explicitly specifies different syntax.

Validate that:

- the resolved Turborepo version satisfies the current documented minimum and is at least 2.11.7;
- each edited Turborepo configuration parses;
- every selected task still has a matching non-empty package script;
- every selected task uses the current documented Vercel CI opt-in syntax or, when unavailable, the bundled `ci` tag fallback;
- no unselected task was changed.

Review the complete diff and commit it locally using the repository's commit style. Do not push or open the pull request yet.

## Run the selected tasks

Before publishing, confirm that each selected task resolves, then run it once with the repository's declared `turbo`:

```bash
turbo run <task> [<task>...] --dry=json
turbo run <task> [<task>...]
```

Time-box long runs, such as large test suites, and say in the pull request which tasks were not run. Act on the results:

- **Passes:** keep it.
- **Fails:** run it on the default branch. If it fails there too, keep it and flag it in the pull request as already failing. If it fails only with your change, fix the change, which is usually the Turborepo upgrade, or move the task to the candidates with the reason.
- **Fails for a missing environment variable or secret:** move it to the candidates with the variable name.

Running tasks must not change tracked files. If it does, discard those changes and say so in the pull request.

## Enable Vercel CI

Enable Vercel CI before the setup branch reaches GitHub, so the first push creates the initial run. Skip this step when `ciEnabledAt` is already present. Prefer the dedicated Vercel CLI command:

```bash
vercel ci enable --remote <remote> --scope <team>
```

If `vercel ci enable` is unavailable, use the released repository-settings API:

```bash
printf '%s\n' '{"ciEnabled":true}' |
  vercel api "/v1/vercel-ci/repository-settings?provider=github&organizationId=<url-encoded-owner>&repository=<url-encoded-repository>" \
    --scope <team> \
    --method PATCH \
    --input - \
    --raw
```

Send `ciEnabled: true`; never set `ciEnabledAt` directly because the service manages that timestamp. Read settings again and require `ciEnabledAt` to be present. If enablement fails or cannot be verified, do not publish the branch.

## Publish the pull request

If your environment publishes a branch and opens a pull request in one step, such as a pull-request tool without `git push`, use it now. Otherwise, push the setup branch, verify that the expected commit is on the remote, and open the pull request:

```bash
gh pr create \
  --base <default-branch> \
  --head <setup-branch> \
  --title "Set up Vercel CI" \
  --body "<pull-request summary>"
```

The summary covers:

- selected tasks, each with its reason and any uncertainty;
- candidates left out, each with its reason, and an invitation to ask for any of them;
- tasks already failing on the default branch, and tasks that were not run;
- any Turborepo upgrade;
- whether the current Vercel CI documentation was verified.

If publishing fails, leave Vercel CI enabled and report the failure, so a retry or concurrent setup is not disabled. If the outcome is uncertain, check for the remote branch and an open setup pull request before retrying.

## Find the run

After the pull request exists, get its head branch and commit SHA, and poll with bounded waits:

```bash
vercel ci list \
  --branch "<setup-branch>" \
  --commit "<commit-sha>" \
  --scope <team> \
  --json
```

When a run appears, report its status and dashboard URL:

```text
https://vercel.com/<team-slug>/~/ci/<invocation-id>
```

Do not wait indefinitely. If no run appears, report that it is still pending and give the lookup command.
