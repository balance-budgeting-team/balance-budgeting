import Foundation
import Observation

/// Everything the Home screen shows and does. The views only read this and call its functions.
///
/// Flow 1 in order:
/// viewing (F1-1) → editing (F1-2, F1-2e if the amount is invalid) → reviewing (F1-3) → viewing with a saved notice (F1-4)
@MainActor
@Observable
final class HomeViewModel {
    enum Mode {
        case viewing, editing, reviewing
    }

    // What's on screen
    var budget: BudgetSummary?
    var mode = Mode.viewing
    var errorMessage: String?
    var savedMessage: String?

    // The draft being edited
    var draftPeriod = BudgetPeriod.weekly
    var draftAmount = ""

    private let api = BudgetAPI()

    /// The typed amount as a number, or nil if it isn't a valid amount above $0.
    var draftValue: Double? { Self.parseAmount(draftAmount) }

    /// F1-2e: the error under the amount field. Nothing while the field is empty.
    var amountError: String? {
        if draftAmount.isEmpty || draftValue != nil { return nil }
        return "Enter an amount greater than $0."
    }

    /// F1-3: "Weekly limit: $350.00 → $400.00", or "Limit: $350.00 per week → $400.00 per month" if the period changed.
    var reviewSummary: String {
        guard let budget, let amount = draftValue else { return "" }
        if budget.period == draftPeriod {
            return "\(draftPeriod.title) limit: \(budget.amount.dollars) → \(amount.dollars)"
        }
        return "Limit: \(budget.amount.dollars) per \(budget.period.unit) → \(amount.dollars) per \(draftPeriod.unit)"
    }

    // MARK: - Actions

    /// F1-1: load the budget from the backend.
    func load() async {
        errorMessage = nil
        do {
            budget = try await api.currentBudget()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    /// F1-2: tap the budget card to start editing, filled in with the current budget.
    func startEditing() {
        guard let budget else { return }
        draftPeriod = budget.period
        draftAmount = String(format: "%.2f", budget.amount)
        savedMessage = nil
        errorMessage = nil
        mode = .editing
    }

    /// F1-3: go to review. Only allowed when the amount is valid.
    func review() {
        if draftValue != nil { mode = .reviewing }
    }

    func keepEditing() {
        mode = .editing
    }

    func cancel() {
        errorMessage = nil
        mode = .viewing
    }

    /// F1-4: save to the backend, then go back to Home with a notice.
    func save() async {
        guard let budget, let amount = draftValue else { return }
        do {
            self.budget = try await api.saveBudget(id: budget.budgetId, period: draftPeriod, amount: amount)
            savedMessage = "Your limit is now \(amount.dollars) per \(draftPeriod.unit)."
            errorMessage = nil
            mode = .viewing
        } catch {
            // Stay on review and show why, e.g. the backend isn't running.
            errorMessage = error.localizedDescription
        }
    }

    // MARK: - Helpers

    /// "$1,234.50" → 1234.5. Returns nil for blank, non-numeric, $0, or negative amounts.
    static func parseAmount(_ text: String) -> Double? {
        let cleaned = text.replacingOccurrences(of: "$", with: "").replacingOccurrences(of: ",", with: "")
        guard let value = Double(cleaned.trimmingCharacters(in: .whitespaces)), value > 0, value.isFinite else { return nil }
        return value
    }
}
