import Foundation

/// App-wide state: backend connectivity, the live voice socket, and the saved
/// conversation threads (persisted locally).
@MainActor
final class GhostSession: ObservableObject {
    enum Health: Equatable {
        case unknown, checking, ok
        case unreachable(String)
    }

    enum Connection: Equatable {
        case disconnected, connecting, connected
        case failed(String)
    }

    /// Dev default points at a locally-run backend. Set an HTTPS production URL
    /// before shipping (the App Store build should not talk to localhost).
    @Published var backendURLString: String {
        didSet { UserDefaults.standard.set(backendURLString, forKey: Self.urlKey) }
    }

    @Published private(set) var health: Health = .unknown
    @Published private(set) var connection: Connection = .disconnected
    @Published private(set) var isAwaiting = false

    @Published private(set) var conversations: [Conversation]
    @Published private(set) var selectedID: UUID

    /// When set (the signed-in Guardian's membership id), conversations sync
    /// server-side and follow the user across devices; when nil they're local.
    @Published private(set) var syncOwner: String?

    /// The active character the Ghost targets for quick gear changes from chat.
    @Published private(set) var activeCharacterID: String?

    private static let urlKey = "ghost.backend.url"
    private var socket: URLSessionWebSocketTask?

    init() {
        // Default backend: the build's `GhostBackendURL` (set to your production
        // HTTPS endpoint before archiving), falling back to localhost for dev. A
        // user's saved override (Settings) always takes precedence.
        let configured = Bundle.main.object(forInfoDictionaryKey: "GhostBackendURL") as? String
        let fallback = (configured?.isEmpty == false ? configured! : "http://localhost:8080")
        backendURLString = UserDefaults.standard.string(forKey: Self.urlKey) ?? fallback
        var loaded = Self.loadConversations().sorted { $0.updatedAt > $1.updatedAt }
        if loaded.isEmpty { loaded = [Conversation()] }
        conversations = loaded
        selectedID = loaded[0].id
    }

    private var backend: GhostBackend? { GhostBackend(baseURLString: backendURLString) }

    /// Messages of the currently selected conversation.
    var messages: [ChatMessage] {
        conversations.first { $0.id == selectedID }?.messages ?? []
    }

    // MARK: - Sync

    /// Links the session to the signed-in Guardian. When the owner changes we
    /// switch the conversation source between the server (synced) and local disk.
    func setSyncOwner(_ id: String?) {
        guard syncOwner != id else { return }
        syncOwner = id
        if let id {
            Task { await loadServerThreads(owner: id) }
        } else {
            var loaded = Self.loadConversations().sorted { $0.updatedAt > $1.updatedAt }
            if loaded.isEmpty { loaded = [Conversation()] }
            conversations = loaded
            selectedID = loaded[0].id
        }
    }

    /// Sets the character the Ghost targets for chat-driven gear changes.
    func setActiveCharacter(_ id: String?) {
        activeCharacterID = id
    }

    private func loadServerThreads(owner: String) async {
        guard let backend else { return }
        do {
            let threads = try await backend.listConversations(membershipID: owner)
            if threads.isEmpty {
                let created = try await backend.createConversation(membershipID: owner)
                conversations = [Self.conversation(from: created)]
                selectedID = conversations[0].id
            } else {
                conversations = threads.map(Self.conversation(from:))
                if !conversations.contains(where: { $0.id == selectedID }) {
                    selectedID = conversations[0].id
                }
            }
        } catch {
            // Backend unreachable — keep whatever is on screen.
        }
    }

    private static func conversation(from t: SyncedThreadSummary) -> Conversation {
        Conversation(
            id: UUID(uuidString: t.id) ?? UUID(),
            title: t.title,
            messages: [],
            updatedAt: isoDate(t.updated_at)
        )
    }

    private static func isoDate(_ s: String) -> Date {
        let withFraction = ISO8601DateFormatter()
        withFraction.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return withFraction.date(from: s) ?? ISO8601DateFormatter().date(from: s) ?? Date()
    }

    // MARK: - Conversations

    func newConversation() {
        if let owner = syncOwner {
            Task {
                guard let backend, let created = try? await backend.createConversation(membershipID: owner) else { return }
                conversations.insert(Self.conversation(from: created), at: 0)
                selectedID = conversations[0].id
                isAwaiting = false
            }
            return
        }
        if let current = conversations.first(where: { $0.id == selectedID }), current.isEmpty {
            return // reuse the already-empty thread
        }
        let conversation = Conversation()
        conversations.insert(conversation, at: 0)
        selectedID = conversation.id
        isAwaiting = false
        persist()
    }

    func selectConversation(_ id: UUID) {
        selectedID = id
        isAwaiting = false
        // Lazily fetch this thread's messages from the server when synced.
        if let owner = syncOwner,
           let current = conversations.first(where: { $0.id == id }), current.messages.isEmpty {
            Task { await loadMessages(owner: owner, id: id) }
        }
    }

    private func loadMessages(owner: String, id: UUID) async {
        guard let backend,
              let thread = try? await backend.getConversation(membershipID: owner, id: id.uuidString),
              let index = conversations.firstIndex(where: { $0.id == id })
        else { return }
        conversations[index].title = thread.title
        conversations[index].messages = thread.messages.map {
            ChatMessage(
                id: UUID(uuidString: $0.id) ?? UUID(),
                role: $0.role == "ghost" ? .ghost : .guardian,
                text: $0.text,
                intent: $0.intent
            )
        }
    }

    func deleteConversation(_ id: UUID) {
        if let owner = syncOwner, let backend {
            Task { try? await backend.deleteConversation(membershipID: owner, id: id.uuidString) }
        }
        conversations.removeAll { $0.id == id }
        if conversations.isEmpty { conversations = [Conversation()] }
        if !conversations.contains(where: { $0.id == selectedID }) {
            selectedID = conversations[0].id
        }
        if syncOwner == nil { persist() }
    }

    private func updateSelected(_ block: (inout Conversation) -> Void) {
        guard let index = conversations.firstIndex(where: { $0.id == selectedID }) else { return }
        block(&conversations[index])
        conversations[index].updatedAt = Date()
        if syncOwner == nil { persist() }
    }

    // MARK: - Health

    func checkHealth() async {
        guard let backend else { health = .unreachable("Invalid backend URL"); return }
        health = .checking
        do {
            let body = try await backend.health()
            health = body.contains("ok") ? .ok : .unreachable("Unexpected response: \(body)")
        } catch {
            health = .unreachable(error.localizedDescription)
        }
    }

    // MARK: - Voice WebSocket

    func connectVoice(membershipID: String? = nil, characterID: String? = nil) {
        guard let backend else { connection = .failed("Invalid backend URL"); return }
        disconnect()
        connection = .connecting
        let task = backend.voiceSocket(token: nil, membershipID: membershipID, characterID: characterID)
        socket = task
        task.resume()
        connection = .connected
        receiveLoop()
    }

    func disconnect() {
        socket?.cancel(with: .goingAway, reason: nil)
        socket = nil
        connection = .disconnected
    }

    func send(_ text: String) {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }

        updateSelected { conversation in
            if conversation.isEmpty && conversation.title == "New Conversation" {
                conversation.title = Conversation.title(from: trimmed)
            }
            conversation.messages.append(ChatMessage(role: .guardian, text: trimmed))
        }

        // Signed in: send over HTTP /chat so the server persists the turn and the
        // conversation syncs across devices (and the reply is game-data grounded).
        if let owner = syncOwner {
            let threadID = selectedID.uuidString
            isAwaiting = true
            Task {
                defer { isAwaiting = false }
                guard let backend else { return }
                do {
                    let reply = try await backend.chat(message: trimmed, membershipID: owner, conversationID: threadID, characterID: activeCharacterID)
                    updateSelected { $0.messages.append(ChatMessage(role: .ghost, text: reply, intent: "conversation")) }
                } catch GhostBackendError.rateLimited {
                    // Not an outage — the Guardian is just over the chat budget.
                    updateSelected { $0.messages.append(ChatMessage(role: .ghost, text: "Easy, Guardian — even a Ghost needs a moment to recharge. Try again in a few seconds.", intent: "throttled")) }
                } catch {
                    updateSelected { $0.messages.append(ChatMessage(role: .ghost, text: "The Ghost is unreachable right now.", intent: "error")) }
                }
            }
            return
        }

        // Signed out: ephemeral local chat over the WebSocket.
        guard let socket,
              let data = try? JSONEncoder().encode(OutboundVoice(text: trimmed)),
              let json = String(data: data, encoding: .utf8)
        else { return }

        isAwaiting = true
        socket.send(.string(json)) { [weak self] error in
            guard let error else { return }
            Task { @MainActor in
                self?.isAwaiting = false
                self?.connection = .failed(error.localizedDescription)
            }
        }
    }

    private func receiveLoop() {
        socket?.receive { [weak self] result in
            Task { @MainActor in
                guard let self else { return }
                switch result {
                case .success(.string(let text)):
                    self.handleInbound(text)
                    self.receiveLoop()
                case .success:
                    self.receiveLoop()
                case .failure(let error):
                    self.isAwaiting = false
                    self.connection = .failed(error.localizedDescription)
                    self.explainSocketFailure()
                }
            }
        }
    }

    /// The production backend requires a signed session on `/ws/voice`, so a
    /// signed-out chat's socket is refused — previously the Guardian's message
    /// just hung with no reply. Answer the dead air with guidance instead, once
    /// per attempt (only when their message is still awaiting a reply).
    private func explainSocketFailure() {
        guard syncOwner == nil else { return }
        guard messages.last?.role == .guardian else { return }
        updateSelected {
            $0.messages.append(ChatMessage(
                role: .ghost,
                text: "I can't speak with you yet, Guardian. Sign in with Bungie in Settings and I'll know your name — or browse the Lore Codex, which is open to everyone.",
                intent: "error"
            ))
        }
    }

    private func handleInbound(_ text: String) {
        isAwaiting = false
        let message: ChatMessage
        if let data = text.data(using: .utf8),
           let frame = try? JSONDecoder().decode(InboundVoice.self, from: data) {
            message = ChatMessage(role: .ghost, text: frame.response, intent: frame.intent)
        } else {
            message = ChatMessage(role: .ghost, text: text)
        }
        updateSelected { $0.messages.append(message) }
    }

    // MARK: - Persistence

    private static var storeURL: URL {
        let dir = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        return dir.appendingPathComponent("conversations.json")
    }

    private static func loadConversations() -> [Conversation] {
        guard let data = try? Data(contentsOf: storeURL),
              let conversations = try? JSONDecoder().decode([Conversation].self, from: data)
        else { return [] }
        return conversations
    }

    private func persist() {
        guard let data = try? JSONEncoder().encode(conversations) else { return }
        try? data.write(to: Self.storeURL, options: .atomic)
    }
}
