# Shared synthetic fixtures

Reserved for versioned datasets used across components: financial profiles, transaction changes, scripted conversations, calendar events, and simulated locations. Include each dataset's version in its file or an accompanying manifest. Never store real financial records, account numbers, or provider credentials here.

Expected financial values must be calculated independently of application code. Changes to expected values need a PR reviewed by a second team member; record the new version in the RVTM. Keep component-specific fakes in their component's test suite.
