# Backend integration tests

Reserved for API, PostgreSQL, ownership, persistence, and provider-interface tests. Use simulated providers; leave live credentials unset and restrict outbound test traffic to the database. Keep reusable provider fakes within backend tests when introduced.

SQLite may support quick development checks, but only PostgreSQL results count for backend acceptance. Add real setup and reset commands with the implementation. Do not treat an empty directory as an executed suite.
