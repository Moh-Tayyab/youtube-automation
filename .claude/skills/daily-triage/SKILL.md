---
name: daily-triage
description: >-
  Runs the morning maintenance pass. Reads the progress file, gathers overnight
  CI failures, open issues, and new audit advisories, drafts safe fixes (each
  one checked by a separate reviewer agent), opens pull requests for what passes,
  and writes anything risky to the progress file for a human. Use this for the
  scheduled morning maintenance loop.
---

# Daily triage

You are the morning maintenance loop. Work through these steps in order.
Do not skip the progress file. It is your only memory between runs.

## 1. Read your memory first

- Open `progress.md`. Read the "In progress" and "Open / needs a human" sections.
- Do not redo anything already listed under "Done".

## 2. Find the work

Gather candidates in this order, and stop once you have at most 5:

1. CI runs that failed since the last entry in `progress.md`.
2. Open issues labelled `bug` or `maintenance`.
3. New advisories from `npm audit` (or this project's audit command).

## 3. Work each candidate

- Create an isolated checkout: a git worktree, or a fresh branch named `claude/<short-slug>`.
- Draft the smallest fix that solves the one problem. Do not bundle changes.
- Send the diff to the reviewer agent. Wait for its verdict before going on.

## 4. Decide from the verdict

- PASS, and the change is low risk (no public API change, no data migration, no file deletion): open a pull request. Title it `fix: <one short line>` and link the issue.
- FAIL, or the change touches anything risky: do NOT open a pull request. Add a short entry to the "Open / needs a human" section of `progress.md`. Say what you tried and why you stopped.

## 5. Update your memory last

- Move finished items to "Done" with today's date.
- Save `progress.md`. This is the file tomorrow's run will read.

## Rules

- Never open more than 5 pull requests in one run.
- Never change `main` directly. Only `claude/*` branches.
- When in doubt, escalate. A flagged item a human checks is always safer than a wrong fix shipped while no one was watching.