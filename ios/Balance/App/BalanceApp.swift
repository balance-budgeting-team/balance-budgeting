import SwiftUI

@main
struct BalanceApp: App {
    var body: some Scene {
        WindowGroup {
            HomeView()
                .preferredColorScheme(.dark)
                .tint(Theme.accent)
        }
    }
}
