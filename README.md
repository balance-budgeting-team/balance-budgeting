# balance-budgeting

A budgeting app that helps users track spending, create personal goals, and maintain a balanced budget.

Contributors: Aishwarya Aswin, Jackson Graff, Srikar Mallajosyula, Hitaesh Saravanarajan

## Project navigation

- [Development process](doc/DEVELOPMENT_PROCESS.md): repository architecture, branches, reviews, CI, merge policy, and repository protection settings.
- [Software Development Plan](Balance_Software_Development_Plan.docx): project scope and requirements; retained at its original path.
- [Verification evidence](doc/verification/README.md): milestone report and evidence archive conventions.
- [iOS application area](ios/README.md): reserved source and XCTest locations.
- [Backend area](backend/README.md): reserved FastAPI source and test locations.
- [Shared fixtures](tests/fixtures/README.md) and [cross-component scenarios](tests/e2e/README.md).
- [Pull request template](.github/pull_request_template.md) and [repository check workflow](.github/workflows/scaffold.yml).

## Current status

This repository contains planning documents and a development scaffold. Backend and iOS code, an Xcode project, Docker Compose, and application test suites have not been implemented. There is no runnable application setup yet. The SDP's reference to an existing 40-test suite is not supported by this checkout; the V&V plan's backend commands are future setup instructions.

Use `doc/verification/` for verification reports. The `docs/verification/` reference in Section 5 of the supplied V&V plan needs correction in its next revision.

## Repository checks

On macOS or Linux, use Node.js 24 with npm, Git, Bash, curl, tar, and `sha256sum` or `shasum`. From the repository root:

```sh
npm ci --ignore-scripts
bash .github/scripts/install-actionlint.sh
npm run check
git diff --check
```

Installation needs internet access. The checks lint Markdown, validate local documentation links and the tracked repository tree, and validate GitHub Actions with actionlint 1.7.11. Stage new documentation files before the tree/link check; see the [exact checks and limitations](doc/DEVELOPMENT_PROCESS.md#checks-available-now). No provider credentials are needed.

GitHub Actions runs **Scaffold checks** on PRs to `main` and pushes to `main`. Backend/PostgreSQL and Xcode acceptance gates must be added with their first implementation. A green scaffold check does not verify application behavior.

## Contributing

Start from the latest `main` in this team repository. Use `feature/<issue#>-short-name`, `fix/<issue#>-short-name`, or `docs/<topic>`. All changes to `main` require a PR, one non-author approval, green CI, and resolved conversations. Complete requested reviews within 48 hours. Squash merge and delete the merged branch.

The team repository is [balance-budgeting-team/balance-budgeting](https://github.com/balance-budgeting-team/balance-budgeting). Its [main protections](doc/DEVELOPMENT_PROCESS.md#repository-settings-and-enforcement) enforce the review and CI requirements for all contributors, including administrators. Only squash merging is enabled, and merged branches are deleted automatically.
