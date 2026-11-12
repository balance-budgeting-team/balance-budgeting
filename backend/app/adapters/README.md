# Provider adapters

Reserved for Plaid, SMS, and AI/search provider interfaces and their implementations. Services use these interfaces rather than depending on a particular provider client. Tests substitute fakes for success, error, timeout, and invalid-response cases without live credentials.

With each implemented adapter, add those tests and enforce at least 80% adapter line coverage. Isolated CI test traffic may reach only the test database. No provider integration is implemented by this README.
