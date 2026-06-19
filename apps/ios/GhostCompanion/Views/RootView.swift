import SwiftUI

struct RootView: View {
    @EnvironmentObject private var session: GhostSession
    @State private var showSettings = false

    var body: some View {
        NavigationStack {
            VoiceChatView()
                .background(GhostTheme.background.ignoresSafeArea())
                .navigationTitle("Ghost")
                .navigationBarTitleDisplayMode(.inline)
                .safeAreaInset(edge: .top) { statusBar }
                .toolbar {
                    ToolbarItem(placement: .topBarTrailing) {
                        Button { showSettings = true } label: { Image(systemName: "gearshape") }
                    }
                }
                .sheet(isPresented: $showSettings) { SettingsView() }
        }
    }

    private var statusBar: some View {
        HStack(spacing: 8) {
            Circle().fill(healthColor).frame(width: 9, height: 9)
            Text(healthLabel).font(.caption).foregroundStyle(.secondary)
            Spacer()
            Text(session.backendURLString).font(.caption2).foregroundStyle(.tertiary)
        }
        .padding(.horizontal)
        .padding(.vertical, 6)
        .background(.ultraThinMaterial)
    }

    private var healthColor: Color {
        switch session.health {
        case .ok: return .green
        case .checking, .unknown: return .yellow
        case .unreachable: return .red
        }
    }

    private var healthLabel: String {
        switch session.health {
        case .unknown: return "Not checked"
        case .checking: return "Connecting…"
        case .ok: return "Backend online"
        case .unreachable(let message): return "Offline — \(message)"
        }
    }
}
