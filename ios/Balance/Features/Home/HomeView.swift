import SwiftUI

/// Placeholder Home: loads the budget from the backend to prove the API call works.
/// The Flow 1 screens replace this.
struct HomeView: View {
    @State private var budget: BudgetSummary?
    @State private var errorMessage: String?

    var body: some View {
        VStack(spacing: 8) {
            if let budget {
                Text("\(budget.period.title) budget")
                Text("$\(budget.spentSoFar, specifier: "%.2f") of $\(budget.amount, specifier: "%.2f")")
                    .font(.title)
            } else if let errorMessage {
                Text(errorMessage).foregroundStyle(.red)
            } else {
                ProgressView()
            }
        }
        .padding()
        .task {
            do {
                budget = try await BudgetAPI().currentBudget()
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }
}

#Preview {
    HomeView()
}
