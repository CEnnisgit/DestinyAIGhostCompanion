import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var session: GhostSession
    @Environment(\.dismiss) private var dismiss
    @State private var urlDraft: String = ""

    var body: some View {
        NavigationStack {
            Form {
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
            .navigationTitle("Settings")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
            .onAppear { urlDraft = session.backendURLString }
        }
    }
}
