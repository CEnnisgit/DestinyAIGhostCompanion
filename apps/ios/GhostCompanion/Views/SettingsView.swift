import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var session: GhostSession
    @EnvironmentObject private var auth: AuthStore
    @Environment(\.dismiss) private var dismiss
    @State private var urlDraft: String = ""

    var body: some View {
        NavigationStack {
            Form {
                Section("Bungie Account") {
                    if let membershipID = auth.membershipID {
                        LabeledContent("Membership ID", value: membershipID)
                        Button("Sign Out", role: .destructive) { auth.signOut() }
                    } else if auth.isAuthenticating {
                        HStack { ProgressView(); Text("Signing in…") }
                    } else {
                        Button {
                            auth.signIn(backendURLString: session.backendURLString)
                        } label: {
                            Label("Sign in with Bungie", systemImage: "person.badge.key")
                        }
                    }
                    if let error = auth.errorMessage {
                        Text(error).font(.footnote).foregroundStyle(.red)
                    }
                }

                Section("Backend") {
                    TextField("Base URL", text: $urlDraft)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .keyboardType(.URL)
                    Button("Save & Check Connection") {
                        session.backendURLString = urlDraft.trimmingCharacters(in: .whitespacesAndNewlines)
                        Task { await session.checkHealth() }
                    }
                }

                Section {
                    Text("Use an HTTPS URL in production. The localhost default is for talking to a backend running on your Mac during development.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }

                Section("About") {
                    LabeledContent("Version", value: "1.0")
                    LabeledContent("Not affiliated with Bungie, Inc.", value: "")
                }
            }
            .scrollContentBackground(.hidden)
            .background(GhostTheme.backgroundGradient.ignoresSafeArea())
            .navigationTitle("Settings")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
            .tint(GhostTheme.accent)
            .preferredColorScheme(.dark)
            .onAppear { urlDraft = session.backendURLString }
        }
    }
}
