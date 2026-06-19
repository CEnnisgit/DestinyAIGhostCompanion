import SwiftUI

@main
struct GhostCompanionApp: App {
    @StateObject private var session = GhostSession()
    @StateObject private var auth = AuthStore()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(session)
                .environmentObject(auth)
                .tint(GhostTheme.accent)
                .task { await session.checkHealth() }
                // Fallback if the OAuth redirect reaches the app via the URL scheme
                // rather than ASWebAuthenticationSession's completion handler.
                .onOpenURL { url in auth.handleCallback(url) }
        }
    }
}
