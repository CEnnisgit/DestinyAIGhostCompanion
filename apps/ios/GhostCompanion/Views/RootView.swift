import SwiftUI

struct RootView: View {
    @EnvironmentObject private var session: GhostSession
    @State private var showSettings = false
    @State private var showConversations = false

    var body: some View {
        ZStack {
            GhostTheme.backgroundGradient.ignoresSafeArea()
            VStack(spacing: 0) {
                header
                VoiceChatView()
            }
        }
        .preferredColorScheme(.dark)
        .sheet(isPresented: $showSettings) { SettingsView() }
        .sheet(isPresented: $showConversations) { ConversationsView() }
    }

    private var header: some View {
        VStack(spacing: 0) {
            HStack(spacing: 12) {
                Button { showConversations = true } label: {
                    Image(systemName: "line.3.horizontal")
                        .font(.system(size: 18, weight: .medium))
                        .foregroundStyle(GhostTheme.accent)
                }
                .accessibilityLabel("Conversations")

                GhostMark(size: 30, glow: session.health == .ok)

                VStack(alignment: .leading, spacing: 2) {
                    Text("Ghost")
                        .font(.system(.title3, design: .default).weight(.bold))
                        .foregroundStyle(GhostTheme.textPrimary)
                    HStack(spacing: 5) {
                        Circle().fill(statusColor).frame(width: 6, height: 6)
                        Text(statusText)
                            .font(GhostTheme.hud(10))
                            .foregroundStyle(GhostTheme.textSecondary)
                    }
                }

                Spacer()

                Button { session.newConversation() } label: {
                    Image(systemName: "square.and.pencil")
                        .font(.system(size: 18, weight: .medium))
                        .foregroundStyle(GhostTheme.accent)
                }
                .accessibilityLabel("New conversation")

                Button { showSettings = true } label: {
                    Image(systemName: "gearshape")
                        .font(.system(size: 18, weight: .medium))
                        .foregroundStyle(GhostTheme.accent)
                }
                .accessibilityLabel("Settings")
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)

            Rectangle().fill(GhostTheme.accentHairline).frame(height: 1)
        }
        .background(GhostTheme.background.opacity(0.6))
    }

    private var statusColor: Color {
        switch session.health {
        case .ok: return .green
        case .checking, .unknown: return GhostTheme.accent
        case .unreachable: return GhostTheme.solar
        }
    }

    private var statusText: String {
        switch session.health {
        case .unknown: return "STANDBY"
        case .checking: return "LINKING…"
        case .ok: return "ONLINE"
        case .unreachable: return "OFFLINE"
        }
    }
}
