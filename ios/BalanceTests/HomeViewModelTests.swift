import XCTest
@testable import Balance

@MainActor
final class HomeViewModelTests: XCTestCase {
    /// F1-2e: only amounts above $0 can be reviewed.
    func testParsesOnlyPositiveAmounts() {
        XCTAssertEqual(HomeViewModel.parseAmount("400"), 400)
        XCTAssertEqual(HomeViewModel.parseAmount("$1,250.50"), 1250.5)
        XCTAssertNil(HomeViewModel.parseAmount("0"))
        XCTAssertNil(HomeViewModel.parseAmount("-5"))
        XCTAssertNil(HomeViewModel.parseAmount(""))
        XCTAssertNil(HomeViewModel.parseAmount("abc"))
    }

    /// F1-2e and F1-3: $0 shows the error; a valid amount shows the change to review.
    func testDraftErrorAndReviewText() {
        let model = HomeViewModel()
        model.budget = BudgetSummary(budgetId: 1, period: .weekly, amount: 350,
                                     spentSoFar: 152, progressPercent: 43, safeToSpendToday: 48)
        model.startEditing()

        model.draftAmount = "0"
        XCTAssertEqual(model.amountError, "Enter an amount greater than $0.")

        model.draftAmount = "400"
        XCTAssertNil(model.amountError)
        XCTAssertEqual(model.reviewSummary, "Weekly limit: $350.00 → $400.00")
    }
}
