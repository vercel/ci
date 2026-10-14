---
name: vercel-ci-setup
description: Set up Vercel CI from a local checkout of a linked private GitHub Turborepo. Use when selecting low-dependency Turbo tasks, upgrading Turborepo when needed, enabling Vercel CI, and creating one onboarding pull request.
---

# Vercel CI Setup

Onboard a private GitHub repository to Vercel CI by recommending a small initial set of Turbo tasks and opening one configuration pull request.

Read [references/local-onboarding.md](references/local-onboarding.md) before starting. It contains the task-selection rules, commands, and recovery behavior.

## Preconditions

1. Require a clean local Git checkout of the repository being onboarded. Never discard unrelated work.
2. Require authenticated `git`, GitHub CLI, and Vercel CLI access. Confirm that `vercel api` and `vercel ci list` are available from the installed CLI; otherwise stop with upgrade guidance.
3. Identify the Vercel team and either a project ID/name or GitHub `owner/repo`.
4. Resolve project input to its linked GitHub repository and ask the user to confirm the inferred `owner/repo`.
5. Require the local checkout's GitHub remote to match the confirmed repository.
6. Require a private GitHub repository linked to at least one project on the selected Vercel team.
7. Require a root `turbo.json` or `turbo.jsonc` and a declared `turbo` dependency. Stop if the repository does not use Turborepo.

## Workflow

### 1. Confirm the target

Resolve project input with the released Vercel CLI. Read Vercel CI repository settings and record the original `ciEnabled` state.

Show the team, project when supplied, confirmed repository, local checkout, default branch, and current enablement state. Stop on any mismatch.

### 2. Analyze tasks locally

Inspect root and package-level Turbo configurations, workspace package scripts, and GitHub Actions workflows without changing files or running Turbo.

Summarize the available tasks by config path and task name, including how many package instances each task covers. Recommend at most five focused lint, type-check, or unit-test selections that require no secrets, environment variables, deployments, or external services.

For every recommendation, show its config path, task name, package count, concise supporting evidence, dependencies, and environment requirements. Never print every package-level instance by default; offer a filtered or paginated full list on request.

### 3. Obtain approval

Present the recommended tasks, exclusions, Turbo upgrade, and files to change. Ask once: “Proceed with these tasks and create the onboarding PR?”

Make clear that approval covers repository enablement, file changes, push, and pull-request creation. After approval, complete the workflow without additional confirmation prompts.

### 4. Prepare one local pull request

After approval, create a branch from the latest default branch.

If Turborepo is older than 2.11.7, update it to a compatible version at or above 2.11.7 using the repository's package manager and regenerate the lockfile. Never edit a lockfile manually.

Add the `ci` tag to each approved task without removing existing tags or JSONC comments. Validate the edited configuration and confirm every selected task still has a matching package script. Review the complete diff, commit it, and push the branch.

### 5. Enable Vercel CI and create the pull request

Immediately before opening the pull request, enable Vercel CI through the repository-settings API using a mode-`600` temporary JSON file and `--input`. Read settings again and require `ciEnabled: true`.

Create one GitHub pull request from the prepared branch. If pull-request creation definitively fails and this workflow enabled a previously disabled repository, restore `ciEnabled: false` and verify the rollback. If the outcome is uncertain, check GitHub for the branch's pull request before deciding whether to roll back.

Do not merge the pull request unless the user explicitly asks.

### 6. Report the result

Return the pull-request URL and, once available, the Vercel CI invocation URL.

Look up the invocation for the pull-request branch and commit with `vercel ci list`. Use a bounded wait because invocation creation is asynchronous. If no invocation appears, return the exact lookup command the user can run later.
