import XCTest
@testable import Balance

final class BudgetTests: XCTestCase {
    /// The app must read the backend's snake_case JSON (backend/app/schemas/budget.py).
    func testDecodesBackendResponse() throws {
        let json = """
        {"budget_id": 1, "period": "weekly", "amount": 350.0, "spent_so_far": 152.0,
         "progress_percent": 43, "safe_to_spend_today": 49.6}
        """
        let budget = try BudgetAPI.decoder.decode(BudgetSummary.self, from: Data(json.utf8))

        XCTAssertEqual(budget, BudgetSummary(budgetId: 1, period: .weekly, amount: 350,
                                             spentSoFar: 152, progressPercent: 43, safeToSpendToday: 49.6))
    }

    /// The backend expects exactly {"period": ..., "amount": ...} and rejects extra fields.
    func testEncodesSaveRequest() throws {
        let data = try JSONEncoder().encode(BudgetUpdate(period: .weekly, amount: 400))
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]

        XCTAssertEqual(json?["period"] as? String, "weekly")
        XCTAssertEqual(json?["amount"] as? Double, 400)
        XCTAssertEqual(json?.count, 2)
    }
}
