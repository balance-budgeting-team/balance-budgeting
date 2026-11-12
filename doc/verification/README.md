# Verification evidence

The canonical repository archive is `doc/verification/`. Section 5 of the supplied November 7, 2026 V&V plan uses `docs/verification/<milestone>/`; update that reference during the next planning-document revision.

At milestones M0–M5, retain selected sanitized reports under a milestone subfolder. Identify the suite, commit SHA, run number, environment, date, requirement/test IDs, actual outcomes, and links to supporting evidence. Future automated report artifacts follow `<suite>-<commit SHA>-<run number>`. Do not fabricate reports for unimplemented suites.

The V&V plan places detailed recordings, screenshots, XCTest results, and validation records in the team SharePoint evidence store. Use participant codes, follow its access/retention rules, and link authorized supporting evidence rather than committing sensitive records. Fixture versions and test results belong in the RVTM when available.

- [Development process and current checks](../DEVELOPMENT_PROCESS.md)
