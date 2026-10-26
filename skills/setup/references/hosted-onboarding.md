# Hosted Vercel CI Onboarding

Use this reference instead of the local workflow when the skill runs inside a hosted agent, such as Vercel Agent started from the Vercel dashboard, rather than in a user's local checkout.

A hosted run differs from a local run:

- The host supplies the Vercel team, project, and GitHub repository in the request. The user already chose them in the dashboard.
- The repository is cloned into a sandbox by the host's clone tool. There is no `gh`, and `git push` is unavailable.
- Pull requests are published by the host's pull-request tool, which creates the remote branch, commits, and pull request in one step.
- No user is available to answer questions during the run. Never wait for a reply; stop with a blocked result instead.

Read the current [Vercel CI documentation](https://vercel.com/docs/ci) first, exactly as in a local run. Then follow [local-onboarding.md](local-onboarding.md) for the sections named below, applying the substitutions in this reference.

## Detect a hosted run

Treat the run as hosted when any of these hold:

- the request says it was started from the Vercel dashboard or names hosted onboarding;
- a repository clone tool and a pull-request publishing tool are available, such as Vercel Agent's `GitHubClone` and `GitHubCreatePullRequest`;
- `gh` is unavailable and the working directory is not a checkout of the target repository.

## Resolve the target

Use the team, project, and `owner/repo` from the request. Do not ask the user to confirm them.

Clone the repository's default branch with the host's clone tool using the project target from the request. Record the returned checkout path, default branch, and commit SHA. Stop with `repository_unavailable` if the clone fails or the project is not linked to the requested repository.

If the Vercel CLI is available, read repository settings as described in [Resolve the repository](local-onboarding.md#resolve-the-repository) and stop with `repository_not_supported` if the repository is public, unlinked, or linked only to another team. If the CLI is unavailable or the settings request is not authorized, continue and record that eligibility was checked by the host.

## Select and prepare the change

Follow these local sections unchanged inside the cloned checkout:

- [Discover runnable tasks](local-onboarding.md#discover-runnable-tasks)
- [Prefer low-dependency tasks](local-onboarding.md#prefer-low-dependency-tasks)
- [Prepare the combined change](local-onboarding.md#prepare-the-combined-change), up to and including the local commit

Apply these substitutions:

- Stop with `turborepo_missing` when the repository has no root `turbo.json` or `turbo.jsonc` or no declared `turbo` dependency. Do not start a Turborepo migration in a hosted run; recommend running `vercel/ci@migrate-to-turborepo` locally in the result.
- Stop with `no_safe_tasks` instead of asking when no conservative selection can be determined.
- Create the setup branch locally from the cloned default-branch commit. Name it `vercel-ci/setup-<short-sha>` unless the request supplies a branch name.
- Never change files under `.github/workflows`. Hosted publishing tokens cannot write workflow files.
- Commit all intended changes, including a regenerated lockfile, and leave the worktree clean.

## Confirm enablement

The dashboard enables Vercel CI before starting a hosted run so that publishing the branch can create the initial invocation.

When the request states that Vercel CI is already enabled, verify `ciEnabledAt` if repository settings are readable, then continue. Otherwise, enable it as described in [Enable Vercel CI](local-onboarding.md#enable-vercel-ci). Stop with `ci_not_enabled` if enablement is required and cannot be performed or verified. Do not publish the branch before enablement is confirmed or stated by the host.

## Publish the pull request

Replace [Push the setup branch](local-onboarding.md#push-the-setup-branch) and [Create the pull request](local-onboarding.md#create-the-pull-request) with one call to the host's pull-request tool:

- `sourcePath`: the cloned checkout path;
- `sourceBranch`: the local setup branch;
- `baseBranch`: the default branch;
- `title`: `Set up Vercel CI`;
- `body`: the selected tasks with their evidence, any Turborepo upgrade, validation results, and whether current documentation was verified.

Publish a ready-for-review pull request unless the request asks for a draft.

If publishing fails, leave Vercel CI enabled. If the tool reports partial publication or an uncertain outcome, read the repository's open pull requests for the setup branch before retrying, and never create a second setup pull request.

Do not merge the pull request.

## Report the result

Look up the invocation as described in [Find the invocation](local-onboarding.md#find-the-invocation) when the Vercel CLI supports `vercel ci list`. Keep the wait short; the dashboard also tracks the invocation.

When the host requests a structured result, populate it with these fields. Otherwise, end with the same fields as a short summary.

- `status`: `pull_request_created` or `blocked`;
- `blockedReason`: one of `repository_unavailable`, `repository_not_supported`, `turborepo_missing`, `no_safe_tasks`, `ci_not_enabled`, or `publish_failed`, when blocked;
- `pullRequestUrl`, `branch`, and `commitSha`, when created;
- `tasks`: each selected task's config path, task name, package count, and recommendation reason;
- `turboUpgrade`: the previous and new Turborepo versions, when upgraded;
- `documentationVerified`: whether the current Vercel CI documentation was read;
- `invocationUrl`: the Vercel CI invocation URL, when found.
