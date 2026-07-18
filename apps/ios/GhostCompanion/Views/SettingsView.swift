import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var session: GhostSession
    @EnvironmentObject private var auth: AuthStore
    @Environment(\.dismiss) private var dismiss
    @State private var urlDraft: String = ""
    @State private var showDeleteConfirmation = false
    @State private var isDeletingAccount = false
    @State private var deleteErrorMessage: String?

    var body: some View {
        NavigationStack {
            Form {
                Section("Bungie Account") {
                    if let membershipID = auth.membershipID {
                        LabeledContent("Membership ID", value: membershipID)
                        Button("Sign Out", role: .destructive) { auth.signOut(backendURLString: session.backendURLString) }
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

                if auth.isSignedIn {
                    Section("Active Character") {
                        if auth.isLoadingCharacters {
                            HStack { ProgressView(); Text("Loading characters…") }
                        } else if auth.characters.isEmpty {
                            Button("Load Characters") {
                                Task { await auth.loadCharacters(backendURLString: session.backendURLString) }
                            }
                        } else {
                            ForEach(auth.characters) { character in
                                Button { auth.selectCharacter(character.characterId) } label: {
                                    HStack {
                                        VStack(alignment: .leading, spacing: 2) {
                                            Text(character.className)
                                                .foregroundStyle(GhostTheme.textPrimary)
                                            Text("◇ \(character.light)")
                                                .font(.caption)
                                                .foregroundStyle(GhostTheme.textSecondary)
                                        }
                                        Spacer()
                                        if character.characterId == auth.selectedCharacterID {
                                            Image(systemName: "checkmark")
                                                .foregroundStyle(GhostTheme.accent)
                                        }
                                    }
                                }
                            }
                        }
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

                // App Store guideline 5.1.1(v): an account created in the app must
                // be deletable from the app, not only by emailing support.
                if auth.isSignedIn {
                    Section {
                        Button(role: .destructive) {
                            showDeleteConfirmation = true
                        } label: {
                            if isDeletingAccount {
                                HStack { ProgressView(); Text("Deleting…") }
                            } else {
                                Text("Delete Account")
                            }
                        }
                        .disabled(isDeletingAccount)

                        if let deleteErrorMessage {
                            Text(deleteErrorMessage).font(.footnote).foregroundStyle(.red)
                        }
                    } header: {
                        Text("Delete Account")
                    } footer: {
                        Text("Permanently erases your saved conversations and your Bungie sign-in from our server, and signs you out everywhere. Your Destiny account and game data are untouched. This cannot be undone.")
                    }
                }

                Section {
                    LabeledContent("Version", value: "1.0")
                    Link("Privacy Policy", destination: URL(string: "https://cennisgit.github.io/DestinyAIGhostCompanion/privacy/")!)
                } header: {
                    Text("About")
                } footer: {
                    Text("Ghost Companion is an unofficial, fan-made app. It is not affiliated with, endorsed by, or sponsored by Bungie, Inc. Destiny is a trademark of Bungie, Inc.")
                }
            }
            .alert("Delete your account?", isPresented: $showDeleteConfirmation) {
                Button("Cancel", role: .cancel) {}
                Button("Delete", role: .destructive) { deleteAccount() }
            } message: {
                Text("This permanently deletes your saved conversations and revokes the app's access to your Bungie account. It cannot be undone.")
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
            .task {
                if auth.isSignedIn && auth.characters.isEmpty {
                    await auth.loadCharacters(backendURLString: session.backendURLString)
                }
            }
        }
    }

    /// Erases the Guardian's server-side account. Dismisses only once the server
    /// confirms; on failure the user stays signed in and sees why, rather than
    /// being told a deletion happened that didn't.
    private func deleteAccount() {
        isDeletingAccount = true
        deleteErrorMessage = nil
        Task {
            do {
                try await auth.deleteAccount(backendURLString: session.backendURLString)
                isDeletingAccount = false
                dismiss()
            } catch {
                isDeletingAccount = false
                deleteErrorMessage = "Could not delete your account. Check your connection and try again."
            }
        }
    }
}
