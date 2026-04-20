import SwiftUI

struct RootView: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        ZStack {
            switch appState.phase {
            case .serverSetup:
                ServerSetupView()
            case .auth:
                AuthGateView()
            case .ready:
                MainShellView()
            }
        }
        .themedBackground()
        .tint(Theme.accent)
        .foregroundStyle(Theme.textPrimary)
    }
}
