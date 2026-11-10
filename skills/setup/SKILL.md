---
name: setup
description: Set up Vercel CI for a private GitHub repository linked to Vercel. Use when asked to set up, onboard, enable, or add Vercel CI; choose Vercel CI tasks; add Turborepo through `vercel/turborepo@add` when needed; or upgrade Turborepo for Vercel CI.
---

# Vercel CI Setup

Open one Vercel CI setup pull request that gets this repository's checks running on Vercel CI. For eligible repositories that do not use Turborepo yet, include the minimal validated Turborepo addition needed for the selected CI tasks in that setup pull request, unless the user asks for separate review. Use whatever tools you have.

The [Vercel CI documentation](https://vercel.com/docs/ci) is the source of truth; read it first. Fall back on [references/vercel-ci.md](references/vercel-ci.md) for what the documentation does not cover, or when it is unavailable.

## Steps

1. Find the repository. It must be a private GitHub repository linked to a Vercel project on the team. If not, stop and explain why. Do not stop because the repository does not use Turborepo; add it in step 4 only when the repository is eligible and the Turborepo addition can be validated safely. If safe addition conditions are not met, stop and explain the blocker. If the user asks for separate review, create a Turborepo-only pull request first and tell the user to rerun setup after it merges.
2. If a setup pull request from an earlier run is still open, report it instead of opening another.
3. Choose tasks, as described below.
4. Make the change: if the repository does not use Turborepo yet, follow `vercel/turborepo@add` in setup-owned same-PR mode to add the minimal Turborepo configuration. Upgrade Turborepo if it is below the documented minimum, opt the chosen tasks in to Vercel CI while keeping existing task properties and comments, and run them.
5. Enable Vercel CI, then publish the branch and open one pull request titled "Set up Vercel CI".
6. Report the pull request, the tasks you enabled, the tasks you left out and why, any Turborepo addition or upgrade included in the setup pull request, and the Vercel CI run once it appears.

## Choosing tasks

- Select a task unless there is evidence that it needs secrets, deployments, or running services. When unsure, select it and say so.
- Without Turborepo, choose from package scripts: workspace packages when the repository declares workspaces, otherwise the root `package.json`.
- When setup must add Turborepo first through `vercel/turborepo@add`, only select tasks whose existing behavior, dependencies, outputs, and environment requirements can be validated safely. Leave uncertain tasks out and explain why.
- Select a build only when GitHub Actions already runs it without secrets; builds often read environment variables that Turborepo never declares.
- Decide per package. A shared task can qualify in one package and not in another.
- Keep a task that already fails on the default branch, and flag it.
- List the selected tasks and the ones you left out, with reasons, in the pull request, and in your plan if you make one, so the user can ask for more.
- If the setup pull request includes a Turborepo addition, include a separate Turborepo section in the pull request summary with the tasks configured, package coverage, validation performed, and deferred tasks.

## Adding Turborepo

Follow `vercel/turborepo@add` in setup-owned same-PR mode.

That skill owns the generic Turborepo addition guidance, including dependency installation, `turbo.json` configuration, `.gitignore`, package-manager declarations, preservation of existing scripts, and validation against existing commands. This setup skill owns selecting Vercel CI tasks, adding Vercel CI task configuration, enabling Vercel CI, and publishing the setup pull request.

## Upgrading Turborepo

When Turborepo is below the documented Vercel CI minimum, upgrade only to the minimum compatible version needed for Vercel CI unless the user asks for a broader upgrade. Do not ask for confirmation for this prerequisite upgrade. In the pull request summary and final report, include the previous version, new version, documented minimum, package manager command used, and validation result.

## Rules

- Vercel CI must be enabled before the setup branch reaches GitHub, because the first push creates the first run. If you cannot enable it, do not publish.
- If publishing fails, leave Vercel CI enabled.
- If the Vercel CI run fails for a reason you did not already flag, read the failed tasks' logs and explain the cause and the fix. Fix it in the pull request only when the setup caused it, such as a missing tag or environment variable declaration; report anything else, such as a bug in the code under test.
- Never opt in a persistent task, such as a dev server, even when asked. It never exits, so the run never finishes; explain this and suggest a short task that starts it, checks it, and exits.
- Never hand-edit a lockfile, change GitHub Actions workflows, enable Vercel CI in a Turborepo-only pull request, or merge any pull request.
- If nobody can answer questions, do not wait for a reply: use these defaults, or stop and explain the blocker.
