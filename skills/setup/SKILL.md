---
name: setup
description: Set up Vercel CI from a local checkout of a linked private GitHub repository. Use when selecting low-dependency Turborepo tasks, offering a stacked Turborepo migration when applicable, upgrading Turborepo when needed, enabling Vercel CI, and creating an onboarding pull request.
---

# Vercel CI Setup

Onboard a private GitHub repository to Vercel CI by selecting a small initial set of Turborepo tasks and opening a configuration pull request. When Turborepo migration is required, keep migration and CI setup in two stacked pull requests.

Read the current [Vercel CI documentation](https://vercel.com/docs/ci) before starting. Treat it as the source of truth for current product requirements, supported configuration syntax, and CLI behavior. If it is unavailable or does not specify the task opt-in syntax, use the bundled `tags: ["ci"]` fallback and note that current documentation could not be verified.

Read [references/local-onboarding.md](references/local-onboarding.md) before starting. It contains the task-selection rules, commands, and recovery behavior.

## Preconditions

1. Require a clean local Git checkout of the repository being onboarded. Never discard unrelated work.
2. Require authenticated `git`, GitHub CLI, and Vercel CLI access. Confirm that `vercel api` and `vercel ci list` are available from the installed CLI; otherwise stop with upgrade guidance.
3. Identify the Vercel team and either a project ID/name or GitHub `owner/repo`.
4. Resolve project input to its linked GitHub repository and ask the user to confirm the inferred `owner/repo`.
5. Require the local checkout's GitHub remote to match the confirmed repository.
6. Require a private GitHub repository linked to at least one project on the selected Vercel team. Automated Vercel CI onboarding and stacked pull requests do not support other Git providers.
7. Require a root `turbo.json` or `turbo.jsonc` and a declared `turbo` dependency. If either is absent, follow the migration handoff in the local onboarding reference.

## Workflow

### 1. Confirm the target

Resolve project input with the released Vercel CLI. Read Vercel CI repository settings and record the original `ciEnabledAt` value; its presence means Vercel CI is enabled.

Show the team, project when supplied, confirmed repository, local checkout, default branch, and current enablement state. Stop on any mismatch.

### 2. Analyze tasks locally

Inspect root and package-level Turborepo configurations, workspace package scripts, and GitHub Actions workflows without changing files or running `turbo`.

Summarize the available tasks by config path and task name, including how many package instances each task covers. Select at most five focused lint, type-check, formatter-check, or unit-test tasks that require no secrets, environment variables, deployments, or external services.

Record each selection's config path, task name, package count, concise supporting evidence, dependencies, and environment requirements for the pull-request summary. Never print every package-level instance by default.

### 3. Choose the initial tasks

Proceed with the conservative selections and create the onboarding pull request without a normal confirmation prompt. Ask only when the target repository is ambiguous or no safe initial task selection can be determined.

### 4. Prepare the setup change

Create a branch from the latest default branch, or from the Turborepo migration pull request's head when continuing a migration handoff.

If Turborepo is older than the currently documented minimum, update it with the repository's package manager and regenerate the lockfile. Never use a version below 2.11.7 or edit a lockfile manually.

Configure each selected task using the current syntax from the Vercel CI documentation without removing existing configuration or JSONC comments. If that syntax is unavailable, use the bundled `tags: ["ci"]` fallback. Validate the edited configuration and confirm every selected task still has a matching package script. Review the complete diff and commit it locally, but do not push yet.

### 5. Enable Vercel CI, push, and create the pull request

Enable Vercel CI and verify that it is enabled before pushing the setup branch. Push the prepared branch only after enablement so the push can create the initial Vercel CI invocation, then create one GitHub pull request. When continuing a migration handoff, base this pull request on the migration branch.

If the push or pull-request creation fails, leave Vercel CI enabled and report the failure so a retry or concurrent setup is not disabled. If an outcome is uncertain, check the remote branch or GitHub pull request before retrying.

Do not merge the pull request unless the user explicitly asks.

### 6. Report the result

Return the setup pull-request URL and, once available, the Vercel CI invocation URL. For a stack, also return the migration pull request, merge order, and retargeting requirement.

Look up the invocation for the pull-request branch and commit with `vercel ci list`. Use a bounded wait because invocation creation is asynchronous. If no invocation appears, return the exact lookup command the user can run later.
