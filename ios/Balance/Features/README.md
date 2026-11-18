# Features

Screens grouped by feature. Each screen's state and logic live in a view model; the views only display it.

`Home/` is Flow 1 (set a budget), all on one screen:

| File | What it shows |
| --- | --- |
| `HomeView.swift` | The Home screen (F1-1). Swaps the budget card for the editor or review as the user goes. |
| `HomeViewModel.swift` | What's on screen and the actions: load, edit, review, save, cancel. Start here. |
| `BudgetEditorCard.swift` | Editing the budget (F1-2), including the $0 error (F1-2e). |
| `BudgetReviewCard.swift` | Reviewing the change before saving (F1-3). |
| `HomeCards.swift` | Safe to Spend card, spending card, saved notice (F1-4), badges, and recent transactions. |
