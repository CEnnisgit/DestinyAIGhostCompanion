import Foundation
import Observation

@Observable
@MainActor
final class ChatViewModel {
    private let appState: AppState
    private let conversations: ConversationsViewModel
    private var streamTask: Task<Void, Never>?

    var messages: [Message] = []
    var isStreaming: Bool = false
    var errorMessage: String?

    init(appState: AppState, conversations: ConversationsViewModel) {
        self.appState = appState
        self.conversations = conversations
    }

    var isEmpty: Bool { messages.isEmpty }

    func load(conversationId: String) async {
        guard !conversationId.isEmpty else { messages = []; return }
        do {
            messages = try await appState.api.getConversation(id: conversationId)
        } catch APIError.unauthorized {
            appState.phase = .auth
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
    }

    func reset() {
        streamTask?.cancel()
        messages = []
        isStreaming = false
    }

    func send(_ text: String) {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty, !isStreaming else { return }

        Haptics.impact(.light)
        let user = Message(role: "user", content: trimmed)
        let assistantId = UUID().uuidString
        messages.append(user)
        messages.append(Message(id: assistantId, role: "assistant", content: "", streaming: true))
        isStreaming = true
        errorMessage = nil

        let query = ChatQuery(
            message: trimmed,
            provider: appState.settings.provider,
            model: appState.settings.provider == "ollama" ? appState.settings.ollamaModel : nil,
            persona: appState.settings.persona,
            speak: appState.settings.speakEnabled,
            voice: appState.settings.selectedVoice,
            sessionId: conversations.activeId.isEmpty ? nil : conversations.activeId
        )

        streamTask = Task { [weak self] in
            guard let self else { return }
            do {
                for try await event in appState.streaming.stream(query) {
                    switch event {
                    case .conversationId(let cid):
                        conversations.setActive(cid)
                    case .chunk(let text):
                        appendToAssistant(id: assistantId, text: text)
                    case .done:
                        finalizeAssistant(id: assistantId)
                    }
                }
                finalizeAssistant(id: assistantId)
                if appState.settings.speakEnabled,
                   appState.settings.selectedVoice == "system",
                   let reply = messages.first(where: { $0.id == assistantId })?.content,
                   !reply.isEmpty {
                    appState.tts.speak(reply, voiceKey: "system")
                }
                await conversations.refresh()
            } catch APIError.unauthorized {
                appState.phase = .auth
            } catch APIError.cancelled {
                finalizeAssistant(id: assistantId)
            } catch {
                errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
                finalizeAssistant(id: assistantId)
            }
        }
    }

    func stop() {
        Haptics.impact(.medium)
        streamTask?.cancel()
        isStreaming = false
        if let last = messages.indices.last, messages[last].role == "assistant" {
            messages[last].streaming = false
        }
    }

    func regenerate(from message: Message) {
        guard message.role == "assistant" else { return }
        guard let idx = messages.firstIndex(where: { $0.id == message.id }) else { return }
        // Find the previous user message.
        for i in stride(from: idx - 1, through: 0, by: -1) where messages[i].role == "user" {
            let prompt = messages[i].content
            // Drop the previous assistant reply, then re-send.
            messages.removeSubrange(idx..<messages.count)
            send(prompt)
            return
        }
    }

    private func appendToAssistant(id: String, text: String) {
        if let idx = messages.firstIndex(where: { $0.id == id }) {
            messages[idx].content += text
        }
    }

    private func finalizeAssistant(id: String) {
        if let idx = messages.firstIndex(where: { $0.id == id }) {
            messages[idx].streaming = false
        }
        isStreaming = false
    }
}
