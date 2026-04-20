import Foundation
import Observation

@Observable
final class AppSettings {
    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        self.baseURLString = defaults.string(forKey: Keys.baseURL) ?? "http://localhost:8000"
        self.provider = defaults.string(forKey: Keys.provider) ?? "ollama"
        self.ollamaModel = defaults.string(forKey: Keys.ollamaModel) ?? "llama3"
        self.persona = defaults.string(forKey: Keys.persona) ?? "destiny_ghost"
        self.speakEnabled = defaults.bool(forKey: Keys.speakEnabled)
        self.selectedVoice = defaults.string(forKey: Keys.selectedVoice) ?? "system"
        self.activeConversationId = defaults.string(forKey: Keys.activeConversation) ?? ""
    }

    var baseURLString: String { didSet { defaults.set(baseURLString, forKey: Keys.baseURL) } }
    var provider: String { didSet { defaults.set(provider, forKey: Keys.provider) } }
    var ollamaModel: String { didSet { defaults.set(ollamaModel, forKey: Keys.ollamaModel) } }
    var persona: String { didSet { defaults.set(persona, forKey: Keys.persona) } }
    var speakEnabled: Bool { didSet { defaults.set(speakEnabled, forKey: Keys.speakEnabled) } }
    var selectedVoice: String { didSet { defaults.set(selectedVoice, forKey: Keys.selectedVoice) } }
    var activeConversationId: String { didSet { defaults.set(activeConversationId, forKey: Keys.activeConversation) } }

    var baseURL: URL? {
        let trimmed = baseURLString.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return nil }
        return URL(string: trimmed)
    }

    func clearSession() {
        activeConversationId = ""
    }

    private enum Keys {
        static let baseURL = "ghost.baseURL"
        static let provider = "ghost.provider"
        static let ollamaModel = "ghost.ollamaModel"
        static let persona = "ghost.persona"
        static let speakEnabled = "ghost.speakEnabled"
        static let selectedVoice = "ghost.selectedVoice"
        static let activeConversation = "ghost.activeConversation"
    }
}
