import SwiftUI

/// Small pieces of the Home screen.

struct SafeToSpendCard: View {
    let budget: BudgetSummary
    let justSaved: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Safe to spend today").font(.subheadline)
            Text(budget.safeToSpendToday.dollars).font(.largeTitle)
            HStack(spacing: 6) {
                Circle().fill(Theme.accent).frame(width: 6, height: 6)
                Text(status).font(.caption)
            }
        }
        .card()
    }

    private var status: String {
        if justSaved { return "Updated for your new \(budget.period.rawValue) budget" }
        if budget.progressPercent > 100 { return "You're over budget this \(budget.period.unit)" }
        return "You're on track this \(budget.period.unit)"
    }
}

/// "Weekly spending   $152 of $350" with a progress bar. Tap it to edit (F1-2).
struct SpendingCard: View {
    let budget: BudgetSummary

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("\(budget.period.title) spending")
                Spacer()
                Text("\(budget.spentSoFar.wholeDollars) of \(budget.amount.wholeDollars)").font(.footnote)
            }
            ProgressView(value: Double(min(budget.progressPercent, 100)), total: 100)
        }
        .card()
    }
}

/// F1-4: shown after saving.
struct SavedNotice: View {
    let title: String
    let message: String

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title).font(.subheadline).foregroundStyle(Theme.accent)
            Text(message).foregroundStyle(.secondary)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Theme.accent.opacity(0.15), in: RoundedRectangle(cornerRadius: 12))
    }
}

/// "Draft" / "Not saved" tag.
struct Badge: View {
    let text: String

    var body: some View {
        Text(text)
            .font(.caption)
            .foregroundStyle(Theme.badge)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(Theme.badge.opacity(0.15), in: Capsule())
    }
}

/// Recent transactions. Hardcoded for the prototype: the backend doesn't send transactions yet.
struct RecentTransactions: View {
    private struct Transaction: Identifiable {
        let name: String
        let detail: String
        let amount: Double
        let icon: String
        var id: String { name }
    }

    private let transactions = [
        Transaction(name: "Blue Bottle Coffee", detail: "Today · Dining", amount: -5.75, icon: "cup.and.saucer"),
        Transaction(name: "Whole Foods", detail: "Yesterday · Groceries", amount: -32.14, icon: "cart"),
        Transaction(name: "Netflix", detail: "Oct 30 · Subscription", amount: -15.99, icon: "tv"),
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Recent transactions").font(.subheadline)
            ForEach(transactions) { transaction in
                HStack(spacing: 12) {
                    Image(systemName: transaction.icon).frame(width: 32)
                    VStack(alignment: .leading) {
                        Text(transaction.name)
                        Text(transaction.detail).font(.caption).foregroundStyle(.secondary)
                    }
                    Spacer()
                    Text(transaction.amount.dollars)
                }
            }
        }
        .padding(.top, 12)
    }
}
