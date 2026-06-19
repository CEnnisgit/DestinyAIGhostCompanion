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

    private static let urlKey = "ghost.backend.url"
    private var socket: URLSessionWebSocketTask?

    init() {
        backendURLString = UserDefaults.standard.string(forKey: Self.urlKey) ?? "http://localhost:8080"
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

    // MARK: - Conversations

    func newConversation() {
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
    }

    func deleteConversation(_ id: UUID) {
        conversations.removeAll { $0.id == id }
        if conversations.isEmpty { conversations = [Conversation()] }
        if !conversations.contains(where: { $0.id == selectedID }) {
            selectedID = conversations[0].id
        }
        persist()
    }

    private func updateSelected(_ block: (inout Conversation) -> Void) {
        guard let index = conversations.firstIndex(where: { $0.id == selectedID }) else { return }
        block(&conversations[index])
        conversations[index].updatedAt = Date()
        persist()
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
                }
            }
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
