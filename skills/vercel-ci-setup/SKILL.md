---
name: vercel-ci-setup
description: Set up Vercel CI from a local checkout of a linked private GitHub Turborepo. Use when selecting low-dependency Turbo tasks, upgrading Turborepo when needed, enabling Vercel CI, and creating one onboarding pull request.
---

# Vercel CI Setup

Onboard one locally available Turborepo and finish with:

- a user-approved set of Turbo tasks selected from local repository evidence;
- one pull request that upgrades Turborepo when necessary and adds `ci` tags;
- Vercel CI enabled immediately before pull-request creation;
- links to the pull request and its Vercel CI invocation.

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

Group the available tasks by config path and task name. Recommend a small initial set of Turbo tasks to run in Vercel CI. Prefer:

- `lint`;
- `typecheck`, `type-check`, `check-types`, or `tsc`;
- `unit-test`, `unittest`, or `test:unit`;
- other focused `test` tasks.

Prefer tasks already run in GitHub Actions and tasks with no declared environment variables, deployment dependencies, or external-service setup. Do not recommend `build`, end-to-end, integration, deployment, or smoke tasks by default.

For every recommendation, show its config path, task name, concise supporting evidence, dependencies, and environment requirements. Offer the complete available-task list on request instead of printing every package-level instance.

### 3. Obtain approval

Before changing files or remote state, present:

- the exact tasks to tag;
- the current Turborepo version;
- the proposed Turborepo upgrade when it is older than 2.11.7;
- the files expected to change;
- the branch and pull-request plan.

Ask once: “Proceed with these tasks and create the onboarding pull request?” Make clear that approval covers the exact task selection, any dependency upgrade, repository enablement, file changes, push, and pull-request creation. After approval, complete the workflow without additional confirmation prompts.

### 4. Prepare one local pull request

After approval, create a branch from the latest default branch.

If Turborepo is older than 2.11.7, update it to a compatible version at or above 2.11.7 using the repository's package manager and regenerate the lockfile. Never edit a lockfile manually.

Add the `ci` tag to each approved task without removing existing tags or JSONC comments. Validate the edited configuration and confirm every selected task still has a matching package script. Review the complete diff, commit it, and push the branch.

### 5. Enable Vercel CI and create the pull request

Immediately before opening the pull request, enable Vercel CI through the repository-settings API using a mode-`600` temporary JSON file and `--input`. Read settings again and require `ciEnabled: true`.

Create one GitHub pull request from the prepared branch. If pull-request creation definitively fails and this workflow enabled a previously disabled repository, restore `ciEnabled: false` and verify the rollback. If the outcome is uncertain, check GitHub for the branch's pull request before deciding whether to roll back.

Do not merge the pull request unless the user explicitly asks.

### 6. Report the result

After creating the pull request, look up the Vercel CI invocation for the pull-request branch and commit with `vercel ci list`. Use a bounded wait because invocation creation is asynchronous.

Return:

- the pull-request URL;
- the invocation URL and current status;
- the repository and team;
- the selected tasks;
- whether Turborepo was upgraded;
- the final `ciEnabled` state.

If no invocation appears within the bounded wait, return the pull-request URL and the exact `vercel ci list` command the user can run later.
