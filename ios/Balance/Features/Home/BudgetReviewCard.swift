import SwiftUI

/// F1-3: review the change before saving.
struct BudgetReviewCard: View {
    let model: HomeViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Review draft").font(.title3)
                Spacer()
                Badge(text: "Not saved")
            }

            Text(model.reviewSummary).font(.headline)

            if let budget = model.budget {
                Text("Spending so far stays \(budget.spentSoFar.dollars). Saving changes your limit, not your transaction history.")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }

            // Shown if saving fails, e.g. the backend isn't running.
            if let error = model.errorMessage {
                Text(error).font(.footnote).foregroundStyle(Theme.error)
            }

            Button {
                Task { await model.save() }
            } label: {
                Text("Save budget").frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)

            Button {
                model.keepEditing()
            } label: {
                Text("Keep editing").frame(maxWidth: .infinity)
            }
            .buttonStyle(.bordered)
            .controlSize(.large)

            Button("Cancel") { model.cancel() }
                .frame(maxWidth: .infinity)
        }
        .card(highlighted: true)
    }
}
