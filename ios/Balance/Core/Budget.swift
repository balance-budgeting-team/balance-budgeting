import Foundation

/// How often a budget resets. Matches the backend's "period" values.
enum BudgetPeriod: String, Codable, CaseIterable {
    case daily, weekly, monthly

    /// "Weekly"
    var title: String { rawValue.capitalized }

    /// "week", for text like "per week"
    var unit: String {
        switch self {
        case .daily: "day"
        case .weekly: "week"
        case .monthly: "month"
        }
    }
}

/// What the backend returns for a budget (GET /budgets/current, PUT /budgets/{id}).
/// JSON keys are snake_case (budget_id) and are converted to camelCase (budgetId) when decoding.
struct BudgetSummary: Codable, Equatable {
    var budgetId: Int
    var period: BudgetPeriod
    var amount: Double
    var spentSoFar: Double
    var progressPercent: Int
    var safeToSpendToday: Double
}

/// What the app sends to save a budget: {"period": "weekly", "amount": 400}
struct BudgetUpdate: Encodable {
    var period: BudgetPeriod
    var amount: Double
}
