import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var authStore: AuthStore
    @EnvironmentObject private var chatStore: ChatStore
    @EnvironmentObject private var settingsStore: SettingsStore
    @State private var backendURL = ""

    var body: some View {
        NavigationStack {
            Form {
                Section("Backend") {
                    TextField("Base URL", text: $backendURL)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                    Button("Save Backend URL") {
                        authStore.saveBackendBaseURL(backendURL)
                        Task {
                            await authStore.refreshStatus()
                            await settingsStore.refresh(using: authStore)
                        }
                    }
                }

                Section("Account") {
                    LabeledContent("Authenticated", value: authStore.status.authenticated ? "Yes" : "No")
                    LabeledContent("Bungie Linked", value: authStore.status.bungieLinked ? "Yes" : "No")
                    LabeledContent("API Key", value: authStore.status.apiKeyOk ? authStore.status.apiKeyMasked : "Missing")
                    if authStore.isAuthenticated {
                        Button("Sign Out", role: .destructive) {
                            authStore.signOut()
                        }
                    }
                }

                if let config = settingsStore.appConfig {
                    Section("Provider") {
                        Picker("Provider", selection: Binding(
                            get: { chatStore.provider ?? config.models.defaultProvider ?? "" },
                            set: { chatStore.provider = $0 }
                        )) {
                            ForEach(config.models.providers, id: \.self) { provider in
                                Text(provider.capitalized).tag(provider)
                            }
                        }

                        Picker("Persona", selection: Binding(
                            get: { chatStore.persona ?? config.personas.first?.id ?? "" },
                            set: { chatStore.persona = $0 }
                        )) {
                            ForEach(config.personas) { persona in
                                Text(persona.label).tag(persona.id)
                            }
                        }
                    }

                    Section("Voice") {
                        LabeledContent("Mode", value: config.voiceCapabilities.mode ?? "Unknown")
                        LabeledContent("Fallback", value: config.voiceCapabilities.fallback ?? "Unknown")
                        LabeledContent("Browser STT", value: config.voiceCapabilities.stt?.browser == true ? "Available" : "Unavailable")
                        LabeledContent("Browser TTS", value: config.voiceCapabilities.tts?.browser == true ? "Available" : "Unavailable")
                    }
                }

                if let errorMessage = settingsStore.errorMessage {
                    Section("Errors") {
                        Text(errorMessage)
                            .foregroundStyle(.red)
                    }
                }
            }
            .navigationTitle("Settings")
            .onAppear {
                backendURL = authStore.backendBaseURL
            }
        }
    }
}
