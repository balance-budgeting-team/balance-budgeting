# Core

Code shared across screens.

- `Budget.swift`: the budget data the backend sends and receives.
- `BudgetAPI.swift`: the backend calls, `GET /budgets/current` and `PUT /budgets/{budget_id}`.

Do not put provider credentials in the app or repeat the backend's financial calculations here.
