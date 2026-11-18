import SwiftUI

/// F1-2 and F1-2e: the budget card opened for editing.
struct BudgetEditorCard: View {
    @Bindable var model: HomeViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Edit your recurring budget").font(.title3)
                Spacer()
                Badge(text: "Draft")
            }

            Picker("Period", selection: $model.draftPeriod) {
                ForEach(BudgetPeriod.allCases, id: \.self) { period in
                    Text(period.title)
                }
            }
            .pickerStyle(.segmented)

            Text("\(model.draftPeriod.title) amount").font(.subheadline)

            TextField("$0.00", text: $model.draftAmount)
                .keyboardType(.decimalPad)
                .padding(12)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(model.amountError == nil ? Theme.border : Theme.error)
                )

            // F1-2e: the error replaces the hint when the amount is $0 or invalid.
            if let error = model.amountError {
                Text(error).font(.caption).foregroundStyle(Theme.error)
            } else if let budget = model.budget {
                Text("Currently \(budget.amount.dollars). Enter a positive amount.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Button {
                model.review()
            } label: {
                Text("Review changes").frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
            .disabled(model.draftValue == nil)

            Button("Cancel") { model.cancel() }
                .frame(maxWidth: .infinity)
        }
        .card(highlighted: true)
    }
}
