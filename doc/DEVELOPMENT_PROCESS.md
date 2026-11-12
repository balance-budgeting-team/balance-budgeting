# Development process

Balance's development process is defined in this single document. It covers repository architecture, branching, review, code quality, testing, CI, and merging for the prototype and continued development.

## Repository architecture

The repository separates the native iOS application, Python FastAPI backend, documentation, and automated checks. Backend services contain financial calculations, transaction processing, and application logic. Provider adapters communicate with Plaid, Twilio, and AI/search providers through replaceable interfaces. Tests substitute provider fakes without changing financial logic.

```text
balance-budgeting/
├── .github/
│   ├── scripts/
│   ├── workflows/
│   └── pull_request_template.md
├── doc/
│   ├── DEVELOPMENT_PROCESS.md
│   └── verification/
├── ios/
│   ├── Balance/
│   │   ├── App/
│   │   ├── Features/
│   │   └── Core/
│   ├── BalanceTests/
│   └── BalanceUITests/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── adapters/
│   └── tests/
│       ├── unit/
│       └── integration/
├── tests/
│   ├── fixtures/
│   └── e2e/
├── .gitignore
├── .markdownlint-cli2.jsonc
├── .node-version
├── package.json
├── package-lock.json
├── Balance_Software_Development_Plan.docx
└── README.md
```

The tree shows the main organization. Reserved folders contain short READMEs so Git retains their purpose and location. Application build configuration, dependency files, and database migrations will live alongside the components they support. The root Node.js files support repository checks only; they do not introduce a web application. `.github/scripts/` contains the link/structure checker and the installer for the pinned workflow validator.

| Location | Purpose |
| --- | --- |
| `doc/` | Development process, architecture notes, and future project documentation. Existing planning documents remain at their current paths. |
| `doc/verification/` | Selected milestone reports and links to verification evidence. |
| `ios/Balance/App/` | Application entry point and app-level setup. |
| `ios/Balance/Features/` | Screens, view models, and related code grouped by features such as onboarding, dashboard, and budgets. |
| `ios/Balance/Core/` | Shared models, networking, and reusable interface components. |
| `ios/BalanceTests/` | iOS unit tests. |
| `ios/BalanceUITests/` | Automated interface, accessibility, and performance tests. |
| `backend/app/api/` | FastAPI routes and request handling. |
| `backend/app/core/` | Configuration, authentication, and security support. |
| `backend/app/models/` | Database models. |
| `backend/app/schemas/` | API request and response schemas. |
| `backend/app/services/` | Financial calculations, transaction processing, and other application logic. |
| `backend/app/adapters/` | Replaceable interfaces to external providers. |
| `backend/tests/unit/` | Isolated service and calculation tests using synthetic fixtures and provider fakes. |
| `backend/tests/integration/` | API, PostgreSQL, ownership, and provider-interface tests using simulated provider responses. |
| `tests/fixtures/` | Shared, versioned synthetic datasets and independently determined expected results. |
| `tests/e2e/` | Cross-component scenarios and supporting automation. |
| `.github/` | Actions workflows, check scripts, and the pull request template. |

This structure supports the [SDP](../Balance_Software_Development_Plan.docx) and the supplied Verification and Validation Plan. `doc/verification/` is the canonical archive location. Section 5, “Results archive location,” of the November 7, 2026 V&V plan uses `docs/verification/<milestone>/`; that reference needs correction to `doc/verification/<milestone>/` in the next planning-document revision. This scaffold does not modify the planning documents or relocate the SDP.

The current checkout contains no backend implementation, Xcode project, application tests, Docker Compose setup, or provider integrations. The SDP's NFR-05 supporting-context reference to an existing 40-test suite is not supported by the repository inspected on November 12, 2026. The V&V plan's Docker and Xcode commands describe future application checks and cannot run against this scaffold. Its referenced RVTM workbook and GANTT workbook are also absent from this checkout; no results are inferred from those references.

## Branching and workflow

We use a feature-branch workflow with `main` as the stable shared branch. Every task starts from the latest `main` within the team repository and returns through a PR. Do not create personal forks or introduce a `develop` branch.

| Branch | Purpose | Merge destination |
| --- | --- | --- |
| `main` | Stable code that has passed review and CI. | Receives approved PRs. |
| `feature/<issue#>-short-name` | One feature or development task associated with an issue. | `main` |
| `fix/<issue#>-short-name` | One defect fix associated with an issue. | `main` |
| `docs/<topic>` | Project documentation and related repository process work. | `main` |

For example, use `feature/12-budget-editor`, `fix/24-duplicate-transactions`, or `docs/development-process`. Keep names short and descriptive, with lowercase words separated by hyphens. Replace `<issue#>` with the issue number without a `#` character.

Before starting a branch, ensure the working tree is clean, fetch `main`, and create the branch from `origin/main`:

```sh
git status --short --branch
git fetch origin main
git switch -c docs/your-topic origin/main
```

Use the appropriate feature or fix name for application tasks. Keep each branch focused, commit meaningful progress with informative messages, and push regularly so the team can access the work. Draft PRs may be opened early for feedback. Before final review, update the working branch with the latest `main` and resolve conflicts. Never overwrite another contributor's work or force-push `main`.

## Development and review policy

| Policy | Rule |
| --- | --- |
| Pull requests | All changes to `main` require a PR. Direct pushes are prohibited. |
| Description | Explain the task, changes, related issue, validation, and known limitations. Identify relevant requirement or test IDs when applicable. |
| Commit messages | Describe what changed and why when the reason is not obvious. Avoid vague messages such as “updates” or “fix stuff.” |
| Approval | Require at least one approval from a team member other than the author. |
| Review frequency | Complete requested reviews within 48 hours. Communicate delays to the team. Authors address feedback before requesting another review. |
| Review scope | Check correctness, scope, readability, security, tests, and consistency with the SDP and this process. |
| CI and conversations | All CI must be green and review conversations resolved before merging. Correct failures before proceeding. |
| Merging | Use Squash Merge with an informative final commit message, then delete the merged branch. |

Use the [PR template](../.github/pull_request_template.md). Reviewers confirm the evidence and checklist; writing a checkbox does not constitute approval. Authors cannot supply the required independent approval themselves.

Run relevant checks locally before requesting review. Application behavior changes include tests for expected behavior, invalid inputs, and relevant failures. Defect fixes include regression coverage when practical. Use clear names and component formatting conventions. Keep financial logic separate from UI and external-service code. Never commit credentials or real financial data.

Shared fixtures remain synthetic and versioned, with the version identified in each file or an accompanying manifest. Expected financial values are calculated independently of the code being tested. Changes to expected values require review by a second team member; record the fixture version in the RVTM as described by the V&V plan. Store secrets in local configuration or the appropriate secret store, separate from fixtures. Only dummy values belong in committed configuration examples.

## Checks available now

The [Repository checks workflow](../.github/workflows/scaffold.yml) runs on every PR targeting `main` and every push to `main`, without path filters. Its check name is **Scaffold checks**. It uses read-only repository permissions and runs real documentation/configuration checks. It does not build or verify the application.

On macOS or Linux, install Node.js 24 with npm, Git, Bash, curl, tar, and either `sha256sum` or `shasum`. From the repository root:

```sh
npm ci --ignore-scripts
bash .github/scripts/install-actionlint.sh
npm run check
git diff --check
```

`npm ci` installs the versions in `package-lock.json`. The installer downloads actionlint 1.7.11 to ignored `.tools/`, verifies a pinned SHA-256 digest, and supports macOS/Linux on Intel and ARM64. Dependency and tool installation require internet access; the checks themselves make no network requests. ShellCheck is disabled consistently in the actionlint command so local and CI results do not depend on an optional ShellCheck installation.

The individual commands are:

| Command | Evidence |
| --- | --- |
| `npm run lint:markdown` | Markdown syntax/style checks, including the process, READMEs, and PR template. Line length is unrestricted for readable policy tables. |
| `npm run check:docs` | Parses Markdown links and images, checks repository-local targets and Markdown heading anchors, and checks every entry of this document's tree against Git-tracked files and directories. |
| `npm run check:workflows` | actionlint validates workflow YAML, events, job structure, expressions, and action usage. |
| `git diff --check` | Checks unstaged diff whitespace. Also run `git diff --cached --check` after staging changes. |

Stage newly added documentation and structural files with an explicit `git add <paths>` before running `check:docs`, because it reads the Git index. It validates current file contents against that tracked-file list; CI checks a clean checkout. Markdown linting also includes untracked Markdown outside ignored tool directories. External URLs are not fetched by the local link checker, and raw HTML links or custom HTML anchors are outside its scope; use Markdown links and headings for repository documentation. Link checks validate paths, not the contents of binary documents.

Empty suites, echo-only jobs, fabricated reports, and `continue-on-error` do not count as successful verification. A passing scaffold check provides no evidence for financial correctness, provider integration, PostgreSQL acceptance, or iOS behavior.

## Application gates to add with implementation

Add backend checks with the first backend implementation, and iOS checks with the first iOS implementation. Introduce real dependency/build configuration and tests alongside the code; do not add empty targets merely to make CI green.

Backend gates must include:

- Formatting/linting and meaningful unit and integration tests.
- PostgreSQL acceptance tests. SQLite may support quick local checks, but SQLite alone does not count as backend acceptance.
- Simulated Plaid, SMS, and AI/search providers with live provider credentials unset.
- Outbound network access during test execution restricted to the test database. Install dependencies before imposing this restriction.
- Success, error, and timeout tests for every implemented provider adapter, plus invalid responses when relevant.
- At least 80% line coverage for each implemented adapter and the complete backend suite finishing in under 10 minutes.
- All tests passing, including financial-calculation fixtures, ownership/security tests, and relevant regression cases.

The V&V plan proposes Python 3.12, pytest, pytest-cov, FastAPI TestClient, freezegun, and Docker PostgreSQL. Pin and validate the real backend dependencies when implementing that component. Its proposed `docker compose` commands require a Compose file, an API service, a test database, and test configuration that do not exist yet. Staging sandbox/live-provider system tests are separate from isolated CI acceptance and are not part of this scaffold task.

iOS gates must include a successful Xcode build and relevant XCTest, UI, and performance checks. Specify the real project/workspace, shared scheme, simulator destination, and Xcode version when introducing those checks. User-facing changes also receive manual workflow walkthroughs and accessibility checks when affected, including VoiceOver and Dynamic Type requirements from NFR-04.

Keep backend suites in `backend/tests/`, iOS suites in their respective iOS test folders, and cross-component scenarios in `tests/e2e/`. Link requirements and RVTM test IDs in PRs and evidence. Automated reports should identify the suite, commit SHA, environment, and run, with milestone evidence retained under `doc/verification/`. Restrict participant records and sensitive evidence to the team-approved evidence store; commit only sanitized reports and authorized links.

## Repository settings and enforcement

Written policy does not enforce GitHub settings. On November 12, 2026, the connected account reported push access with `admin: false` and `maintain: false`. GitHub's `main` branch response reported `protected: false`, status-check enforcement off, and no required check contexts. The rulesets endpoint returned an empty list. The detailed branch-protection and collaborator-permission endpoints returned HTTP 403 (“Resource not accessible by integration”). Squash/merge/rebase and automatic branch-deletion settings were not exposed by the available repository metadata, so their values remain unverified. No settings were changed.

A repository owner or administrator must apply and verify these settings:

1. Open **Settings → General → Pull Requests**. Enable **Allow squash merging**; disable **Allow merge commits** and **Allow rebase merging**. Enable **Automatically delete head branches**.
2. Open **Settings → Branches → Add classic branch protection rule** and enter the exact branch pattern `main`.
3. Enable **Require a pull request before merging**, then **Require approvals**, with **1** required approval. GitHub excludes the author's own approval. Enable **Dismiss stale pull request approvals when new commits are pushed** so the approved diff stays current.
4. Enable **Require status checks to pass before merging** and **Require branches to be up to date before merging**. Once this PR has produced a run, select the exact **Scaffold checks** context from GitHub Actions. Add backend/iOS contexts when those real workflows are introduced.
5. Enable **Require conversation resolution before merging** and **Do not allow bypassing the above settings**. Keep **Allow force pushes** and **Allow deletions** disabled. Do not add bypass exceptions. These settings require reviewed PRs for `main`, including administrator changes.
6. Save the rule, reopen it to verify the saved values, and inspect the PR merge box for the approval and check requirements. Verify that `main` is now reported protected and the required context is listed. Recheck merge-method and branch-deletion settings separately.

All enforcement settings above remain outstanding until an administrator applies and verifies them. Review within 48 hours, descriptive messages, review quality, and evidence requirements remain team responsibilities. Automatic branch deletion occurs after merge; it must not delete `main`. This task leaves its PR open for an independent reviewer and does not merge or approve it.

## References

- FastAPI: [Bigger Applications — Multiple Files](https://fastapi.tiangolo.com/tutorial/bigger-applications/), for backend modules and routers.
- Apple: [Managing files and folders in your Xcode project](https://developer.apple.com/documentation/xcode/managing-files-and-folders-in-your-xcode-project), for application and test organization.
- pytest: [Good Integration Practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html), for application test organization.
- GitHub: [Creating an example workflow](https://docs.github.com/en/actions/tutorials/create-an-example-workflow), for workflow configuration.
- GitHub: [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches), for approvals, status checks, conversation resolution, and bypass restrictions.
- GitHub: [Managing automatic deletion of branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-the-automatic-deletion-of-branches), for deleting merged branches.
- [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2), for documentation linting.
- [actionlint installation](https://github.com/rhysd/actionlint/blob/main/docs/install.md) and [pinned 1.7.11 release](https://github.com/rhysd/actionlint/releases/tag/v1.7.11), for workflow validation and installer digests.
