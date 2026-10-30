---
name: setup
description: Set up Vercel CI for a private GitHub Turborepo linked to Vercel. Use when enabling Vercel CI, choosing which Turborepo tasks it runs, upgrading Turborepo when needed, and opening the setup pull request.
---

# Vercel CI Setup

Open one pull request that gets this repository's checks running on Vercel CI: the Turborepo tasks it relies on, configured for Vercel CI, with Turborepo upgraded when needed and Vercel CI enabled before the branch reaches GitHub.

Read the current [Vercel CI documentation](https://vercel.com/docs/ci) before starting. Treat it as the source of truth for current product requirements, supported configuration syntax, and CLI behavior. If it is unavailable or does not specify the task opt-in syntax, use the bundled `tags: ["ci"]` fallback and note that current documentation could not be verified.

Read [references/local-onboarding.md](references/local-onboarding.md) before starting. It contains the task-selection guidance, example commands, and recovery behavior.

## What you need

Use whatever tools your environment provides. Commands in the reference are examples, not requirements.

- A checkout of the target repository: the current one, or a fresh clone. Never discard unrelated work in an existing checkout.
- A way to publish a branch and open a pull request, such as `git push` and `gh pr create`, or your environment's pull-request tool.
- Vercel API access for the team, such as the Vercel CLI.
- The Vercel team, and a project or GitHub `owner/repo`.

The repository must be a private GitHub repository linked to a project on that team, with a root `turbo.json` or `turbo.jsonc` and a declared `turbo` dependency. If it does not use Turborepo, stop and explain that Vercel CI requires Turborepo, linking the [Vercel CI documentation](https://vercel.com/docs/ci).

When nobody is available to answer questions, such as a run started from the Vercel dashboard, never wait for a reply: make the conservative choice described here, or stop and explain the blocker.

## Workflow

### 1. Confirm the target

Resolve the project to its linked GitHub repository and read Vercel CI repository settings, recording the original `ciEnabledAt` value; its presence means Vercel CI is enabled. Confirm the repository with the user when one is available; when the request already names it, use it. Stop if the repository is public, unlinked, linked only to another team, or does not match the checkout.

### 2. Find runnable tasks

Inspect root and package-level Turborepo configurations, workspace package scripts, and GitHub Actions workflows without changing files or running `turbo`. Summarize the available tasks by config path and task name, including how many packages each task covers.

### 3. Choose tasks

Recommend the checks the repository relies on, then include more where the evidence supports it. There is no fixed limit.

- Start with lint, type-check, formatter-check, and unit-test tasks that need no secrets, deployments, or external services, across every package that defines them.
- Add other runnable tasks, such as builds or other tests, when evidence shows they run without secrets or services, for example because GitHub Actions already runs them that way.
- Leave out tasks that deploy, need secrets or external services, or whose requirements are unclear, and list them in the pull request with the reason so they can be added later.

When a user is available, show the recommended tasks and the other candidates, and let them add more before you edit anything. Otherwise, proceed with the recommended tasks and the well-supported additions. Do not stop because some tasks are uncertain; leave those out and say so.

### 4. Prepare the change

Create a branch from the latest default branch. If Turborepo is older than the currently documented minimum, update it with the repository's package manager and regenerate the lockfile. Never use a version below 2.11.7 or edit a lockfile manually.

Configure each selected task using the current syntax from the Vercel CI documentation without removing existing configuration or JSONC comments. If that syntax is unavailable, use the bundled `tags: ["ci"]` fallback. Validate the edited configuration, confirm every selected task still has a matching package script, review the complete diff, and commit it.

### 5. Enable Vercel CI, then publish

Enable Vercel CI and verify that it is enabled before the setup branch reaches GitHub, so the first push creates the initial Vercel CI invocation. Skip enabling when it is already enabled. Then publish the branch and open one pull request, with whatever tool your environment provides.

If publishing fails, leave Vercel CI enabled and report the failure so a retry or concurrent setup is not disabled. If an outcome is uncertain, check the remote branch or open pull requests before retrying, and never open a second setup pull request.

Do not merge the pull request unless the user explicitly asks.

### 6. Report the result

Return the pull-request URL, the tasks you enabled, the tasks you left out and why, any Turborepo upgrade, and, once available, the Vercel CI invocation URL. Invocation creation is asynchronous, so use a bounded wait; if none appears, say how to look it up later.
