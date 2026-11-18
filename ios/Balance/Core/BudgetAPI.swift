import Foundation

/// Talks to the Balance backend. These are the prototype's API calls.
struct BudgetAPI {
    /// The backend running on this Mac. The iOS Simulator can reach it at 127.0.0.1.
    var baseURL = URL(string: "http://127.0.0.1:8000")!

    /// GET /budgets/current: the budget and spending shown on Home.
    func currentBudget() async throws -> BudgetSummary {
        let url = baseURL.appendingPathComponent("budgets/current")
        return try await send(URLRequest(url: url))
    }

    /// PUT /budgets/{id}: saves a new period and amount, returns the updated totals.
    func saveBudget(id: Int, period: BudgetPeriod, amount: Double) async throws -> BudgetSummary {
        var request = URLRequest(url: baseURL.appendingPathComponent("budgets/\(id)"))
        request.httpMethod = "PUT"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(BudgetUpdate(period: period, amount: amount))
        return try await send(request)
    }

    private func send(_ request: URLRequest) async throws -> BudgetSummary {
        let (data, response) = try await URLSession.shared.data(for: request)
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0

        guard status == 200 else {
            // The backend explains errors as {"detail": "Enter an amount greater than $0."}
            let detail = try? JSONDecoder().decode([String: String].self, from: data)["detail"]
            throw APIError(message: detail ?? "Something went wrong (error \(status)).")
        }
        return try BudgetAPI.decoder.decode(BudgetSummary.self, from: data)
    }

    static let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return decoder
    }()
}

/// An error with a message that can be shown to the user as-is.
struct APIError: LocalizedError {
    let message: String
    var errorDescription: String? { message }
}
