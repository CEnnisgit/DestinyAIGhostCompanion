import Foundation
import Observation

@Observable
@MainActor
final class SettingsViewModel {
    private let appState: AppState

    var ollamaModels: [String] = []
    var personas: [String] = []
    var voices: [Voice] = []
    var apiKeyInput: String = ""
    var apiKeySaving: Bool = false
    var apiKeyMessage: String?
    var loading: Bool = false
    var errorMessage: String?
    var diagnostics: AudioDiagnostics?
    var diagnosticsLoading: Bool = false

    init(appState: AppState) { self.appState = appState }

    var settings: AppSettings { appState.settings }

    func load() async {
        loading = true; defer { loading = false }
        async let m = fetchModels()
        async let p = fetchPersonas()
        async let v = fetchVoices()
        _ = await (m, p, v)
        applyPersonaVoice()
    }

    private func fetchModels() async {
        do { ollamaModels = (try await appState.api.models()).ollama ?? [] }
        catch { errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription }
    }

    private func fetchPersonas() async {
        do { personas = try await appState.api.personas() }
        catch { errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription }
    }

    private func fetchVoices() async {
        do {
            var fetched = try await appState.api.voices()
            if !fetched.contains(where: { $0.key == "system" }) {
                fetched.insert(.system, at: 0)
            }
            voices = fetched
        } catch {
            voices = [.system]
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
    }

    /// Mirror of App.js persona-voice auto-selection.
    private func applyPersonaVoice() {
        guard appState.settings.speakEnabled, !voices.isEmpty else { return }
        let persona = appState.settings.persona
        let match = voices.first(where: { ($0.personas ?? []).contains(persona) })
            ?? voices.first(where: { $0.name.range(of: "ghost|vergil", options: [.regularExpression, .caseInsensitive]) != nil })
        if let match, appState.settings.selectedVoice == "system" || appState.settings.selectedVoice.isEmpty {
            appState.settings.selectedVoice = match.key
        }
    }

    func loadDiagnostics() async {
        diagnosticsLoading = true; defer { diagnosticsLoading = false }
        do {
            diagnostics = try await appState.api.audioDiagnostics()
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
    }

    func saveApiKey() async {
        let trimmed = apiKeyInput.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        apiKeySaving = true; defer { apiKeySaving = false }
        do {
            let resp = try await appState.api.setBungieApiKey(trimmed)
            apiKeyMessage = resp.ok ? "API key accepted" : (resp.error ?? "API key not accepted")
            if resp.ok { apiKeyInput = "" }
        } catch {
            apiKeyMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
    }
}
