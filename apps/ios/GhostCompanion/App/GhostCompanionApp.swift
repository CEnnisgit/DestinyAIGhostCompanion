import SwiftUI

@main
struct GhostCompanionApp: App {
    @StateObject private var session = GhostSession()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(session)
                .tint(GhostTheme.accent)
                .task { await session.checkHealth() }
        }
    }
}
