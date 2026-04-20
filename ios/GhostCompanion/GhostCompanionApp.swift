import SwiftUI

@main
struct GhostCompanionApp: App {
    @State private var appState = AppState()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(appState)
                .preferredColorScheme(.dark)
                .task { await appState.bootstrap() }
                .onOpenURL { url in
                    // ASWebAuthenticationSession handles the redirect itself;
                    // this hook is a safety net for Universal Links or future
                    // deep-link entry points.
                    AppLogger.auth.info("onOpenURL: \(url.absoluteString, privacy: .public)")
                }
        }
    }
}
