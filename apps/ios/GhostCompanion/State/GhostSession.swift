import Foundation

/// App-wide state: backend connectivity and the live voice conversation.
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
    @Published private(set) var messages: [ChatMessage] = []
    /// True while a sent message is awaiting the Ghost's reply (drives the typing indicator).
    @Published private(set) var isAwaiting = false

    private static let urlKey = "ghost.backend.url"
    private var socket: URLSessionWebSocketTask?

    init() {
        backendURLString = UserDefaults.standard.string(forKey: Self.urlKey) ?? "http://localhost:8080"
    }

    private var backend: GhostBackend? { GhostBackend(baseURLString: backendURLString) }

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

    func clearConversation() {
        messages = []
        isAwaiting = false
    }

    func send(_ text: String) {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        messages.append(ChatMessage(role: .guardian, text: trimmed))

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
                    self.connection = .failed(error.localizedDescription)
                }
            }
        }
    }

    private func handleInbound(_ text: String) {
        isAwaiting = false
        guard let data = text.data(using: .utf8),
              let frame = try? JSONDecoder().decode(InboundVoice.self, from: data)
        else {
            messages.append(ChatMessage(role: .ghost, text: text))
            return
        }
        messages.append(ChatMessage(role: .ghost, text: frame.response, intent: frame.intent))
    }
}
