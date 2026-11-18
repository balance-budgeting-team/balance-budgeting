import SwiftUI

/// Home (Flow 1). One screen whose budget card changes as the user edits:
/// F1-1 Home → F1-2 editor → F1-3 review → F1-4 saved notice.
struct HomeView: View {
    @State private var model = HomeViewModel()

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                header

                if let budget = model.budget {
                    content(budget)
                } else if let error = model.errorMessage {
                    loadError(error)
                } else {
                    ProgressView().frame(maxWidth: .infinity)
                }
            }
            .padding(24)
        }
        .background(Theme.background)
        .task { await model.load() }
    }

    private var header: some View {
        HStack {
            Text("Balance").font(.largeTitle)
            Spacer()
            Image(systemName: "person").font(.title2)
        }
    }

    @ViewBuilder
    private func content(_ budget: BudgetSummary) -> some View {
        if let saved = model.savedMessage {
            SavedNotice(title: "\(budget.period.title) budget saved", message: saved)
        }

        if model.mode == .viewing {
            SafeToSpendCard(budget: budget, justSaved: model.savedMessage != nil)
        }

        SpendingCard(budget: budget)
            .onTapGesture {
                if model.mode == .viewing { model.startEditing() }
            }

        switch model.mode {
        case .viewing:
            Text("Tap your budget to edit it ›")
                .font(.footnote)
                .foregroundStyle(Theme.accent)
        case .editing:
            BudgetEditorCard(model: model)
        case .reviewing:
            BudgetReviewCard(model: model)
        }

        RecentTransactions()
    }

    /// Shown when the backend can't be reached on launch.
    private func loadError(_ message: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Couldn't load your budget").font(.headline)
            Text(message).font(.footnote).foregroundStyle(.secondary)
            Button("Try again") {
                Task { await model.load() }
            }
        }
        .card()
    }
}

#Preview {
    HomeView().preferredColorScheme(.dark)
}
