import Foundation

/// Thin client for the Ghost Companion Rust backend (apps/server).
/// Talks to `/health`, the Bungie OAuth entry point, and the `/ws/voice` socket.
struct GhostBackend {
    var baseURL: URL
    /// The signed session token (loaded from the Keychain), attached as a bearer
    /// so every request is authenticated as the signed-in Guardian.
    private let sessionToken: String?

    private static let keychainService = "com.cennis.ghostcompanion"
    private static let sessionAccount = "bungie.session_token"

    init?(baseURLString: String) {
        let trimmed = baseURLString.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let url = URL(string: trimmed) else { return nil }
        self.baseURL = url
        self.sessionToken = KeychainStore.load(service: Self.keychainService, account: Self.sessionAccount)
    }

    /// Builds a request with the session bearer attached when available.
    private func authed(_ url: URL, method: String = "GET") -> URLRequest {
        var request = URLRequest(url: url)
        request.httpMethod = method
        if let sessionToken {
            request.setValue("Bearer \(sessionToken)", forHTTPHeaderField: "Authorization")
        }
        return request
    }

    /// `GET /health` → returns the body (expected: "ok").
    func health() async throws -> String {
        let (data, response) = try await URLSession.shared.data(from: baseURL.appendingPathComponent("health"))
        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            throw GhostBackendError.badStatus
        }
        return String(decoding: data, as: UTF8.self)
    }

    /// The backend URL that begins the Bungie OAuth flow.
    var loginURL: URL { baseURL.appendingPathComponent("auth/login") }

    /// `GET /characters?membership_id=...` → the signed-in user's characters.
    func characters(membershipID: String) async throws -> [CharacterSummary] {
        var components = URLComponents(url: baseURL.appendingPathComponent("characters"), resolvingAgainstBaseURL: false)!
        components.queryItems = [URLQueryItem(name: "membership_id", value: membershipID)]
        let (data, response) = try await URLSession.shared.data(for: authed(components.url!))
        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            throw GhostBackendError.badStatus
        }
        return try JSONDecoder().decode([CharacterSummary].self, from: data)
    }

    /// `GET /lore/categories` → Codex categories with counts.
    func loreCategories() async throws -> [LoreCategory] {
        try await getJSON([LoreCategory].self, path: "lore/categories", query: [])
    }

    /// `GET /lore/browse?category=...` → entries within a category.
    func loreBrowse(category: String) async throws -> [LoreEntry] {
        try await getJSON([LoreEntry].self, path: "lore/browse", query: [URLQueryItem(name: "category", value: category)])
    }

    /// `GET /lore/search?q=...` → structured lore search.
    func loreSearch(query: String) async throws -> [LoreEntry] {
        try await getJSON([LoreEntry].self, path: "lore/search", query: [URLQueryItem(name: "q", value: query)])
    }

    /// `GET /lore/random?n=...` → random entries for discovery.
    func loreRandom(n: Int = 8) async throws -> [LoreEntry] {
        try await getJSON([LoreEntry].self, path: "lore/random", query: [URLQueryItem(name: "n", value: String(n))])
    }

    /// `GET /activity/summary?membership_id=...` → recent activity history.
    func activitySummary(membershipID: String) async throws -> ActivitySummary {
        try await getJSON(
            ActivitySummary.self,
            path: "activity/summary",
            query: [URLQueryItem(name: "membership_id", value: membershipID)]
        )
    }

    // MARK: - Cross-device chat sync

    /// `GET /conversations?membership_id=...` → the owner's synced threads.
    func listConversations(membershipID: String) async throws -> [SyncedThreadSummary] {
        struct Wrap: Decodable { let threads: [SyncedThreadSummary] }
        return try await getJSON(
            Wrap.self, path: "conversations",
            query: [URLQueryItem(name: "membership_id", value: membershipID)]
        ).threads
    }

    /// `POST /conversations` → create a new synced thread.
    func createConversation(membershipID: String, title: String? = nil) async throws -> SyncedThreadSummary {
        struct Wrap: Decodable { let thread: SyncedThreadSummary }
        var body: [String: Any] = ["membership_id": membershipID]
        if let title { body["title"] = title }
        return try await sendJSON(Wrap.self, method: "POST", path: "conversations", body: body).thread
    }

    /// `GET /conversations/{id}?membership_id=...` → a thread with its messages.
    func getConversation(membershipID: String, id: String) async throws -> SyncedThread {
        struct Wrap: Decodable { let thread: SyncedThread }
        return try await getJSON(
            Wrap.self, path: "conversations/\(id)",
            query: [URLQueryItem(name: "membership_id", value: membershipID)]
        ).thread
    }

    /// `DELETE /conversations/{id}?membership_id=...`
    func deleteConversation(membershipID: String, id: String) async throws {
        var components = URLComponents(
            url: baseURL.appendingPathComponent("conversations/\(id)"), resolvingAgainstBaseURL: false)!
        components.queryItems = [URLQueryItem(name: "membership_id", value: membershipID)]
        _ = try await URLSession.shared.data(for: authed(components.url!, method: "DELETE"))
    }

    /// `POST /chat` → a grounded reply. When `conversationID` is given the server
    /// persists the turn so it syncs across the user's devices.
    func chat(message: String, membershipID: String?, conversationID: String?) async throws -> String {
        struct Wrap: Decodable { let reply: String }
        var body: [String: Any] = ["message": message]
        if let membershipID { body["membership_id"] = membershipID }
        if let conversationID { body["conversation_id"] = conversationID }
        return try await sendJSON(Wrap.self, method: "POST", path: "chat", body: body).reply
    }

    private func sendJSON<T: Decodable>(_ type: T.Type, method: String, path: String, body: [String: Any]) async throws -> T {
        var request = authed(baseURL.appendingPathComponent(path), method: method)
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw GhostBackendError.badStatus
        }
        return try JSONDecoder().decode(T.self, from: data)
    }

    private func getJSON<T: Decodable>(_ type: T.Type, path: String, query: [URLQueryItem]) async throws -> T {
        var components = URLComponents(url: baseURL.appendingPathComponent(path), resolvingAgainstBaseURL: false)!
        if !query.isEmpty { components.queryItems = query }
        let (data, response) = try await URLSession.shared.data(for: authed(components.url!))
        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            throw GhostBackendError.badStatus
        }
        return try JSONDecoder().decode(T.self, from: data)
    }

    /// `GET /profile/summary?membership_id=...` → the Guardian career dossier.
    func profileSummary(membershipID: String) async throws -> String {
        var components = URLComponents(url: baseURL.appendingPathComponent("profile/summary"), resolvingAgainstBaseURL: false)!
        components.queryItems = [URLQueryItem(name: "membership_id", value: membershipID)]
        let (data, response) = try await URLSession.shared.data(for: authed(components.url!))
        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            throw GhostBackendError.badStatus
        }
        struct Summary: Decodable { let summary: String }
        return try JSONDecoder().decode(Summary.self, from: data).summary
    }

    /// Opens the `/ws/voice` WebSocket. `token` (+ optional equip context) is passed
    /// as a query param per the backend's current dev auth seam.
    func voiceSocket(token: String?, membershipID: String?, characterID: String?) -> URLSessionWebSocketTask {
        var components = URLComponents(url: baseURL.appendingPathComponent("ws/voice"), resolvingAgainstBaseURL: false)!
        components.scheme = (baseURL.scheme == "https") ? "wss" : "ws"
        var items: [URLQueryItem] = []
        if let token { items.append(URLQueryItem(name: "token", value: token)) }
        if let sessionToken { items.append(URLQueryItem(name: "session", value: sessionToken)) }
        if let membershipID { items.append(URLQueryItem(name: "membership_id", value: membershipID)) }
        if let characterID { items.append(URLQueryItem(name: "character_id", value: characterID)) }
        if !items.isEmpty { components.queryItems = items }
        return URLSession.shared.webSocketTask(with: components.url!)
    }
}

enum GhostBackendError: Error {
    case badStatus
    case invalidBaseURL
}
