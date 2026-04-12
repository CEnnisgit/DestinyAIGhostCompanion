import Foundation

@MainActor
final class ChatStore: ObservableObject {
    @Published var conversations: [ConversationSummary] = []
    @Published var messages: [ConversationMessage] = []
    @Published var selectedConversationID: String?
    @Published var isStreaming = false
    @Published var errorMessage: String?
    @Published var provider: String?
    @Published var persona: String?
    @Published var model: String?

    private func shouldUseVoiceTurn(for text: String) -> Bool {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !trimmed.isEmpty else { return false }
        let patterns = [
            #"^(yes|yeah|confirm|do it|go ahead|cancel|no|stop)$"#,
            #"\b(equip|vault|move|transfer|pull|get|postmaster|where is|find|show equipped|list equipped|show vault|show inventory)\b"#
        ]
        return patterns.contains { pattern in
            trimmed.range(of: pattern, options: [.regularExpression, .caseInsensitive]) != nil
        }
    }

    func bootstrap(using auth: AuthStore) async {
        await loadConversations(using: auth)
        if selectedConversationID == nil, let first = conversations.first?.id {
            await openConversation(first, using: auth)
        }
    }

    func loadConversations(using auth: AuthStore) async {
        do {
            conversations = try await auth.client().fetchConversations()
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func createConversation(using auth: AuthStore) async {
        do {
            let created = try await auth.client().createConversation(name: "New Chat", provider: provider)
            selectedConversationID = created.id
            messages = []
            await loadConversations(using: auth)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func openConversation(_ conversationID: String, using auth: AuthStore) async {
        do {
            messages = try await auth.client().fetchConversation(conversationID)
            selectedConversationID = conversationID
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func send(_ text: String, using auth: AuthStore) async {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        if selectedConversationID == nil {
            await createConversation(using: auth)
        }

        let userMessage = ConversationMessage(id: UUID().uuidString, role: "user", content: trimmed)
        let assistantID = UUID().uuidString
        messages.append(userMessage)
        messages.append(ConversationMessage(id: assistantID, role: "assistant", content: ""))
        isStreaming = true
        errorMessage = nil

        do {
            if shouldUseVoiceTurn(for: trimmed) {
                let reply = try await auth.client().voiceTurn(text: trimmed, sessionID: selectedConversationID)
                if let conversationID = reply.sessionId, !conversationID.isEmpty {
                    selectedConversationID = conversationID
                }
                if let index = messages.firstIndex(where: { $0.id == assistantID }) {
                    messages[index] = ConversationMessage(
                        id: assistantID,
                        role: "assistant",
                        content: reply.replyText,
                        createdAt: messages[index].createdAt
                    )
                }
            } else {
                try await auth.client().streamChat(
                    message: trimmed,
                    sessionID: selectedConversationID,
                    provider: provider,
                    persona: persona,
                    model: model,
                    onConversation: { [weak self] conversationID in
                        self?.selectedConversationID = conversationID
                    },
                    onChunk: { [weak self] chunk in
                        guard let self else { return }
                        guard let index = self.messages.firstIndex(where: { $0.id == assistantID }) else { return }
                        let current = self.messages[index]
                        self.messages[index] = ConversationMessage(
                            id: current.id,
                            role: current.role,
                            content: current.content + chunk,
                            createdAt: current.createdAt
                        )
                    }
                )
            }
            await loadConversations(using: auth)
        } catch {
            if let index = messages.firstIndex(where: { $0.id == assistantID }) {
                messages[index] = ConversationMessage(id: assistantID, role: "assistant", content: "I hit an error: \(error.localizedDescription)")
            }
            errorMessage = error.localizedDescription
        }

        isStreaming = false
    }
}
