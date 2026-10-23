---
name: migrate-to-turborepo
description: Migrate an existing JavaScript or TypeScript package-manager workspace to Turborepo in a separate draft pull request. Use when Vercel CI setup finds a repository without Turborepo or when a user asks to adopt Turborepo without changing package managers or repository structure.
---

# Migrate to Turborepo

Adopt Turborepo conservatively in an existing workspace, preserving package scripts and current behavior. This skill prepares migration for Vercel CI but does not enable Vercel CI.

Read the current [Turborepo documentation](https://turborepo.dev/docs) before changing files. Treat it as the source of truth for current configuration and package-manager commands.

## Applicability

Require all of the following:

1. A clean local Git checkout. Never discard unrelated work.
2. A root `package.json` and one lockfile for npm, pnpm, Yarn, or Bun.
3. An existing package-manager workspace with at least two packages.
4. A workspace layout that can remain unchanged.
5. Package scripts whose current orchestration and environment requirements can be determined from repository configuration and CI workflows.

Stop instead of migrating when:

- the repository is a single package or has no package-manager workspace;
- migration requires changing package managers, moving packages, or restructuring applications;
- multiple conflicting lockfiles make package-manager ownership ambiguous;
- required task ordering, generated outputs, or environment dependencies cannot be inferred safely.

Explain the failed condition and leave the repository unchanged.

## Workflow

### 1. Analyze without changing files

Inspect:

- the root package manifest, workspace definition, lockfile, and package manifests;
- root scripts that orchestrate workspace commands;
- scripts shared by multiple packages;
- package dependency relationships;
- GitHub Actions and other CI configuration for task ordering, filters, outputs, services, and environment variables;
- existing build artifacts and ignored generated directories.

Summarize:

- detected package manager and workspace layout;
- candidate tasks and package coverage;
- observed dependencies, outputs, and environment requirements;
- behavior that cannot be inferred.

Ask for explicit confirmation before making the migration. Do not treat confirmation to set up Vercel CI as confirmation to migrate the repository.

### 2. Establish the migration boundary

Migrate only tasks whose behavior is clear. Prefer focused lint, type-check, formatter-check, unit-test, and build tasks already run across workspaces.

Do not:

- rename or move packages;
- change package managers or workspace definitions;
- rewrite package-level scripts;
- add remote caching;
- enable Vercel CI or add Vercel CI task tags;
- migrate deployment, end-to-end, integration, or environment-provisioning tasks unless the user explicitly requests them.

Preserve existing root scripts by default. When retaining an existing root orchestrator, name its Turbo alternative `<task>:turbo`. Replace an existing orchestration script only when the Turbo command is demonstrably equivalent.

### 3. Create the migration

Create a branch from the latest remote default branch.

Install `turbo` as a root development dependency with the repository's existing package manager. Preserve its dependency style and regenerate the lockfile through the package manager; never edit the lockfile manually.

Create a root `turbo.json` or `turbo.jsonc` using the current documented schema. Configure only the selected tasks:

- encode task dependencies only when repository evidence establishes them;
- declare generated outputs when they can be identified confidently;
- include shared root files used by package tasks in task `inputs`;
- disable caching for side-effecting tasks or tasks whose meaningful outputs cannot be captured safely;
- declare environment variables according to current Turborepo guidance when repository evidence establishes them;
- leave uncertain tasks out of the initial migration.

Do not add speculative `dependsOn`, `inputs`, `outputs`, or environment configuration.

Preserve existing ignore rules. Ensure the package manager's dependency directory and Turborepo's local `.turbo` directory are ignored without replacing the repository's `.gitignore`.

### 4. Validate behavior

Install dependencies using the lockfile and repository's normal immutable or frozen mode when available.

First inspect the Turbo dry-run output and confirm:

- only intended packages and tasks are selected;
- task dependencies match observed ordering;
- no package with a matching script is unexpectedly omitted;
- no package without the script is forced to run it;
- changing a shared root input invalidates the affected task cache.

Then run the existing command and its Turbo equivalent for each selected low-risk task. Compare package coverage, ordering where material, exit status, and expected outputs. Do not claim equivalence from a successful Turbo command alone.

If validation reveals uncertain behavior, narrow the migration or stop. Never conceal a behavioral difference by deleting the old command.

### 5. Open a separate draft pull request

Review the complete diff, commit using the repository's commit style, push the migration branch, and open a draft pull request.

The pull-request summary must include:

- why Turborepo is being adopted;
- the tasks migrated and package coverage;
- preserved scripts and any root script intentionally replaced;
- inferred dependencies, outputs, and environment configuration;
- validation comparing existing and Turbo commands;
- deferred or unsupported tasks.

Do not include Vercel CI enablement or task tags in this pull request. Do not merge it unless the user explicitly asks.

## Handoff to Vercel CI

Return the draft pull-request URL and tell the user to merge it before running `vercel/ci@setup` again. After merge, the setup skill performs task selection, adds Vercel CI configuration, enables the repository, and creates its separate onboarding pull request.
