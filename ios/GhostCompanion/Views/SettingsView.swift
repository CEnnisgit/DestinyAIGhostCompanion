import SwiftUI

struct SettingsView: View {
    @Environment(AppState.self) private var appState
    @Environment(SettingsViewModel.self) private var vm
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        @Bindable var settings = appState.settings
        @Bindable var vm = vm

        Form {
            if let error = vm.errorMessage {
                Section {
                    ErrorBanner(message: error) { vm.errorMessage = nil }
                        .listRowBackground(Color.clear)
                        .listRowInsets(EdgeInsets())
                }
            }
            Section("Model") {
                Picker("Provider", selection: $settings.provider) {
                    Text("Ollama (local)").tag("ollama")
                    Text("Grok").tag("grok")
                    Text("Fine-tune").tag("finetune")
                }
                if settings.provider == "ollama" && !vm.ollamaModels.isEmpty {
                    Picker("Ollama model", selection: $settings.ollamaModel) {
                        ForEach(vm.ollamaModels, id: \.self) { Text($0).tag($0) }
                    }
                }
            }

            Section("Persona") {
                Picker("Persona", selection: $settings.persona) {
                    if vm.personas.isEmpty {
                        Text("Destiny Ghost").tag("destiny_ghost")
                    } else {
                        ForEach(vm.personas, id: \.self) { id in
                            Text(Persona(id: id).displayName).tag(id)
                        }
                    }
                }
            }

            Section("Voice") {
                Toggle("Speak replies", isOn: $settings.speakEnabled)
                Picker("Voice", selection: $settings.selectedVoice) {
                    if vm.voices.isEmpty {
                        Text("System (on-device)").tag("system")
                    } else {
                        ForEach(vm.voices) { v in
                            Text(v.name + (v.isOnDevice ? "" : " — server-only"))
                                .tag(v.key)
                        }
                    }
                }
                Text("Non-system voices play on the server host and aren't audible on iOS yet.")
                    .font(Typography.meta)
                    .foregroundStyle(Theme.textMuted)
            }

            Section {
                diagnosticsSection(vm: vm)
            } header: {
                Text("Audio diagnostics")
            } footer: {
                Text("Server-side audio status — iOS playback uses AVSpeechSynthesizer regardless.")
                    .font(Typography.meta)
                    .foregroundStyle(Theme.textMuted)
            }

            Section("Bungie API Key") {
                SecureField("Set or update key", text: $vm.apiKeyInput)
                Button {
                    Task { await vm.saveApiKey() }
                } label: {
                    HStack {
                        if vm.apiKeySaving { ProgressView() }
                        Text("Save API Key")
                    }
                }
                .disabled(vm.apiKeySaving || vm.apiKeyInput.trimmingCharacters(in: .whitespaces).isEmpty)
                if let msg = vm.apiKeyMessage {
                    Text(msg).font(Typography.meta).foregroundStyle(Theme.textMuted)
                }
            }

            Section("Server") {
                TextField("Base URL", text: $settings.baseURLString)
                    .textInputAutocapitalization(.never)
                    .keyboardType(.URL)
                    .autocorrectionDisabled()
                Button("Change server") {
                    appState.phase = .serverSetup
                    dismiss()
                }
            }

            Section {
                Button(role: .destructive) {
                    appState.signOut()
                    dismiss()
                } label: {
                    Text("Sign out")
                }
            }
        }
        .scrollContentBackground(.hidden)
        .background(Theme.background)
        .navigationTitle("Settings")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .cancellationAction) {
                Button("Done") { dismiss() }
            }
        }
        .task { await vm.loadDiagnostics() }
    }

    @ViewBuilder
    private func diagnosticsSection(vm: SettingsViewModel) -> some View {
        if vm.diagnosticsLoading && vm.diagnostics == nil {
            HStack { ProgressView(); Text("Loading diagnostics…") }
        } else if let d = vm.diagnostics {
            diagnosticsRow(label: "OpenAI key configured", value: d.openaiKey)
            diagnosticsRow(label: "Secure context (HTTPS)", value: d.secureContextHint)
            if let provider = d.sttProvider, !provider.isEmpty {
                HStack {
                    Text("STT provider")
                    Spacer()
                    Text(provider).foregroundStyle(Theme.textMuted)
                }
            }
            if let count = d.deviceCount {
                HStack {
                    Text("Input devices")
                    Spacer()
                    Text("\(count)").foregroundStyle(Theme.textMuted)
                }
            }
            if let idx = d.defaultInputDevice {
                HStack {
                    Text("Default input")
                    Spacer()
                    Text("#\(idx)").foregroundStyle(Theme.textMuted)
                }
            }
            if let err = d.devicesError {
                HStack(alignment: .top) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundStyle(Theme.danger)
                    Text(err).font(Typography.meta).foregroundStyle(Theme.textMuted)
                }
            }
            Button {
                Task { await vm.loadDiagnostics() }
            } label: {
                HStack {
                    if vm.diagnosticsLoading { ProgressView() }
                    Text("Refresh")
                }
            }
            .disabled(vm.diagnosticsLoading)
        } else {
            Button("Load diagnostics") {
                Task { await vm.loadDiagnostics() }
            }
        }
    }

    @ViewBuilder
    private func diagnosticsRow(label: String, value: Bool?) -> some View {
        HStack {
            Text(label)
            Spacer()
            if let value {
                Image(systemName: value ? "checkmark.circle.fill" : "xmark.circle.fill")
                    .foregroundStyle(value ? Theme.accent : Theme.danger)
            } else {
                Text("—").foregroundStyle(Theme.textMuted)
            }
        }
    }
}
