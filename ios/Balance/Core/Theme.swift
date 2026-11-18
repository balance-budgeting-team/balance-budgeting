import SwiftUI

/// Colors from the Flow 1 Figma frames.
enum Theme {
    static let background = Color(red: 0.07, green: 0.08, blue: 0.08)
    static let card = Color(red: 0.11, green: 0.12, blue: 0.13)
    static let border = Color.white.opacity(0.1)
    static let accent = Color(red: 0.58, green: 0.76, blue: 0.77)
    static let error = Color(red: 0.93, green: 0.52, blue: 0.45)
    static let badge = Color(red: 0.85, green: 0.65, blue: 0.35)
}

extension View {
    /// The rounded dark card used throughout Home. `highlighted` gives it a teal border.
    func card(highlighted: Bool = false) -> some View {
        padding(16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Theme.card, in: RoundedRectangle(cornerRadius: 12))
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(highlighted ? Theme.accent : Theme.border)
            )
    }
}

extension Double {
    /// 400 → "$400.00"
    var dollars: String { formatted(.currency(code: "USD")) }

    /// 400 → "$400"
    var wholeDollars: String { formatted(.currency(code: "USD").precision(.fractionLength(0))) }
}
