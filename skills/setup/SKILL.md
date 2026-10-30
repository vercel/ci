---
name: setup
description: Set up Vercel CI for a private GitHub Turborepo linked to Vercel and open the pull request that turns it on. Use when asked to set up, onboard, enable, or add Vercel CI for a repository, to choose which Turborepo tasks Vercel CI runs, or to upgrade Turborepo for Vercel CI.
---

# Vercel CI Setup

Open one pull request that gets this repository's checks running on Vercel CI: its Turborepo tasks opted in to Vercel CI, with Turborepo upgraded when needed, and Vercel CI enabled before the branch reaches GitHub.

The [Vercel CI documentation](https://vercel.com/docs/ci) is the source of truth for requirements, configuration syntax, and CLI behavior; read it first. [references/local-onboarding.md](references/local-onboarding.md) has the detailed rules, example commands, and fallbacks for each step below.

## What you need

Use whatever tools your environment provides. Commands in the reference are examples, not requirements.

- A checkout of the target repository: the current one, or a fresh clone.
- A way to publish a branch and open a pull request: `git push` and `gh pr create`, or your environment's pull-request tool.
- Vercel API access for the team, such as the Vercel CLI.
- The Vercel team, and a project or GitHub `owner/repo`.

## Defaults

- **Coverage over caution.** Include a task unless there is concrete evidence that it needs secrets, deployments, or running services. When unsure, include it and say so in the pull request.
- **Builds only with proof.** Include a build task only when GitHub Actions already runs it without secrets.
- **Surface existing failures.** Keep a task that already fails on the default branch, and flag it in the pull request.
- **Never wait for a reply** when nobody can answer, such as a run started from the Vercel dashboard. Use these defaults, or stop and explain the blocker.

## Workflow

1. **Confirm the target.** Resolve the repository from the project's Git link and read its Vercel CI settings. Use the repository the request names; otherwise confirm it with the user when one is available. Stop if it is public, unlinked, linked only to another team, does not match the checkout, or does not use Turborepo.
2. **Check for earlier setup.** If an open setup pull request already exists, report it instead of opening another.
3. **Choose tasks.** Discover runnable tasks without changing files, then choose with the defaults above. Show the selected tasks and the other candidates in your plan, when you make one, and in the pull request, so the user can ask for more. If nothing would change, report that the repository is already set up.
4. **Prepare the change.** Branch from the latest default branch, upgrade Turborepo when it is below the documented minimum, opt the selected tasks in, validate the configuration, commit, and run the selected tasks.
5. **Enable Vercel CI, then publish.** Enable and verify Vercel CI before the branch reaches GitHub, so the first push creates the initial run. Then publish the branch and open one pull request titled "Set up Vercel CI".
6. **Report.** Return the pull-request URL, the selected tasks, the candidates left out and why, any tasks already failing, any Turborepo upgrade, and the Vercel CI run URL once available.

Never merge the pull request unless the user explicitly asks.
