# Pull request

## Task and issue

Explain the problem or task. Link the issue (for example, `Closes #123`), or explain why no issue applies. Include relevant requirement, RVTM test, or UAT IDs when applicable.

## Changes

Describe what changed and why. Identify any behavior, architecture, dependency, or fixture-version changes.

## Validation

List the exact commands, environments, and results. Link CI and supporting evidence. Identify unavailable checks and explain why. Scaffold checks alone do not verify backend or iOS behavior.

## Limitations

Describe known limitations, deferred work, and remaining risks. State “None” if there are none.

## Author and reviewer checklist

- [ ] The branch is focused, starts from the latest `main`, and follows `feature/<issue#>-short-name`, `fix/<issue#>-short-name`, or `docs/<topic>`.
- [ ] The PR description and commit messages explain the task and changes.
- [ ] Relevant local checks pass; behavior changes have appropriate tests and evidence.
- [ ] No credentials, real financial data, or unrelated changes are included.
- [ ] A team member other than the author has reviewed correctness, scope, readability, security, tests, and consistency with the SDP and development process.
- [ ] The requested review was completed within 48 hours, or the delay was communicated to the team.
- [ ] All CI is green and review conversations are resolved.
- [ ] Merge using Squash Merge with an informative message, then delete the merged branch.

Review policy: [Development process](../doc/DEVELOPMENT_PROCESS.md). When viewing this template in a PR description, use the repository's **doc → DEVELOPMENT_PROCESS.md** navigation.
