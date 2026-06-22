import SwiftUI

/// The Guardian's recent in-game activity: what they played, when, completion,
/// and the fireteam — across Destiny 2 and Destiny 1. Backed by `/activity/summary`.
struct ActivityLogView: View {
    @EnvironmentObject private var session: GhostSession
    @EnvironmentObject private var auth: AuthStore
    @Environment(\.dismiss) private var dismiss

    @State private var summary: ActivitySummary?
    @State private var loading = true

    private var backend: GhostBackend? { GhostBackend(baseURLString: session.backendURLString) }

    var body: some View {
        NavigationStack {
            Group {
                if auth.membershipID == nil {
                    signedOut
                } else {
                    content
                }
            }
            .background(GhostTheme.backgroundGradient.ignoresSafeArea())
            .navigationTitle("Activity Log")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } }
            }
            .tint(GhostTheme.accent)
            .preferredColorScheme(.dark)
            .task { await load() }
        }
    }

    private var signedOut: some View {
        VStack(spacing: 10) {
            Image(systemName: "person.crop.circle.badge.questionmark")
                .font(.system(size: 36))
                .foregroundStyle(GhostTheme.accent)
            Text("Sign in with Bungie to let the Ghost read your activity history.")
                .font(.subheadline)
                .multilineTextAlignment(.center)
                .foregroundStyle(GhostTheme.textSecondary)
                .padding(.horizontal, 32)
        }
    }

    private var content: some View {
        List {
            if let narrative = summary?.narrative, !narrative.isEmpty {
                Text(narrative)
                    .font(.subheadline)
                    .italic()
                    .foregroundStyle(GhostTheme.textSecondary)
                    .listRowBackground(Color.clear)
            }

            ForEach(summary?.recent ?? []) { record in
                VStack(alignment: .leading, spacing: 6) {
                    HStack(spacing: 8) {
                        Text(record.name).font(.headline).foregroundStyle(GhostTheme.accentBright)
                        Text(record.mode.uppercased())
                            .font(GhostTheme.hud(9))
                            .foregroundStyle(GhostTheme.textSecondary)
                        if record.isDestiny1 {
                            Text("D1")
                                .font(GhostTheme.hud(8))
                                .foregroundStyle(GhostTheme.accent)
                                .padding(.horizontal, 5).padding(.vertical, 1)
                                .overlay(Capsule().stroke(GhostTheme.accentHairline, lineWidth: 1))
                        }
                        Spacer()
                        Text(record.displayDate)
                            .font(GhostTheme.hud(10))
                            .foregroundStyle(GhostTheme.textSecondary)
                    }
                    HStack(spacing: 6) {
                        Image(systemName: record.completed ? "checkmark.seal.fill" : "circle.dashed")
                            .font(.system(size: 11))
                            .foregroundStyle(record.completed ? GhostTheme.accent : GhostTheme.textSecondary)
                        Text(record.completed ? "Completed" : "Played")
                            .font(GhostTheme.hud(10))
                            .foregroundStyle(GhostTheme.textSecondary)
                    }
                    if !record.fireteam.isEmpty {
                        Text("Fireteam: \(record.fireteam.joined(separator: ", "))")
                            .font(.footnote)
                            .foregroundStyle(GhostTheme.textPrimary)
                    }
                }
                .padding(.vertical, 3)
                .listRowBackground(GhostTheme.surface)
            }

            if !loading, (summary?.recent.isEmpty ?? true) {
                Text("No recent activity found — or your Bungie session needs a refresh.")
                    .font(.subheadline)
                    .foregroundStyle(GhostTheme.textSecondary)
                    .listRowBackground(Color.clear)
            }
        }
        .scrollContentBackground(.hidden)
        .overlay { if loading { ProgressView().tint(GhostTheme.accent) } }
    }

    private func load() async {
        guard let backend, let membershipID = auth.membershipID else {
            loading = false
            return
        }
        loading = true
        defer { loading = false }
        summary = try? await backend.activitySummary(membershipID: membershipID)
    }
}
