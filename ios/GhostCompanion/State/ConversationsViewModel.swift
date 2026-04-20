import Foundation
import Observation

@Observable
@MainActor
final class ConversationsViewModel {
    private let appState: AppState

    var conversations: [Conversation] = []
    var search: String = ""
    var activeId: String = ""
    var loading: Bool = false
    var errorMessage: String?

    init(appState: AppState) {
        self.appState = appState
        self.activeId = appState.settings.activeConversationId
    }

    var filtered: [Conversation] {
        let q = search.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !q.isEmpty else { return conversations }
        return conversations.filter {
            $0.name.lowercased().contains(q) || ($0.last_message ?? "").lowercased().contains(q)
        }
    }

    func refresh() async {
        loading = true; defer { loading = false }
        do {
            conversations = try await appState.api.listConversations()
        } catch APIError.unauthorized {
            appState.phase = .auth
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
    }

    func create(name: String, provider: String?) async -> String? {
        do {
            let id = try await appState.api.createConversation(name: name, provider: provider)
            setActive(id)
            await refresh()
            return id
        } catch APIError.unauthorized {
            appState.phase = .auth; return nil
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
            return nil
        }
    }

    func rename(_ id: String, to name: String) async {
        do {
            try await appState.api.updateConversation(id: id, name: name)
            if let idx = conversations.firstIndex(where: { $0.id == id }) {
                conversations[idx].name = name
            }
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
    }

    func changeProvider(_ id: String, to provider: String) async {
        do {
            try await appState.api.updateConversation(id: id, provider: provider)
            if let idx = conversations.firstIndex(where: { $0.id == id }) {
                conversations[idx].provider = provider
            }
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
    }

    func delete(_ id: String) async {
        do {
            try await appState.api.deleteConversation(id: id)
            conversations.removeAll { $0.id == id }
            if activeId == id { setActive("") }
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
    }

    func setActive(_ id: String) {
        activeId = id
        appState.settings.activeConversationId = id
    }
}
