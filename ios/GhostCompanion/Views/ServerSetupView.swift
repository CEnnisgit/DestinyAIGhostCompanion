import SwiftUI

struct ServerSetupView: View {
    @Environment(AppState.self) private var appState
    @State private var urlText: String = ""
    @State private var testing: Bool = false
    @State private var error: String?

    var body: some View {
        VStack(spacing: 24) {
            Spacer()
            VStack(spacing: 8) {
                Text("Ghost Companion")
                    .font(Typography.hero)
                Text("Enter the address of your Ghost server.")
                    .font(Typography.body)
                    .foregroundStyle(Theme.textMuted)
            }
            VStack(alignment: .leading, spacing: 8) {
                Text("Server URL").font(Typography.meta).foregroundStyle(Theme.textMuted)
                TextField("http://192.168.1.10:8000", text: $urlText)
                    .textInputAutocapitalization(.never)
                    .keyboardType(.URL)
                    .autocorrectionDisabled()
                    .padding(.horizontal, 14)
                    .padding(.vertical, 12)
                    .background(Theme.backgroundElevated, in: RoundedRectangle(cornerRadius: 14))
            }
            .padding(.horizontal, 24)

            if let error {
                Text(error)
                    .font(Typography.meta)
                    .foregroundStyle(Theme.danger)
                    .padding(.horizontal, 24)
            }

            Button(action: connect) {
                HStack {
                    if testing { ProgressView().tint(.black) }
                    Text(testing ? "Connecting…" : "Connect")
                        .font(.headline)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 14)
                .background(Theme.accent, in: Capsule())
                .foregroundStyle(Color.black)
            }
            .disabled(testing || urlText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            .padding(.horizontal, 24)

            Spacer()
        }
        .onAppear { urlText = appState.settings.baseURLString }
    }

    private func connect() {
        let trimmed = urlText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard URL(string: trimmed) != nil else {
            error = "That doesn't look like a valid URL."; return
        }
        error = nil
        testing = true
        Task {
            defer { testing = false }
            appState.settings.baseURLString = trimmed
            do {
                try await appState.api.health()
                await appState.bootstrap()
            } catch {
                self.error = (error as? APIError)?.errorDescription ?? error.localizedDescription
            }
        }
    }
}
