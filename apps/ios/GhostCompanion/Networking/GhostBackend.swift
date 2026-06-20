import Foundation

/// Thin client for the Ghost Companion Rust backend (apps/server).
/// Talks to `/health`, the Bungie OAuth entry point, and the `/ws/voice` socket.
struct GhostBackend {
    var baseURL: URL

    init?(baseURLString: String) {
        let trimmed = baseURLString.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let url = URL(string: trimmed) else { return nil }
        self.baseURL = url
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
        let (data, response) = try await URLSession.shared.data(from: components.url!)
        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            throw GhostBackendError.badStatus
        }
        return try JSONDecoder().decode([CharacterSummary].self, from: data)
    }

    /// Opens the `/ws/voice` WebSocket. `token` (+ optional equip context) is passed
    /// as a query param per the backend's current dev auth seam.
    func voiceSocket(token: String?, membershipID: String?, characterID: String?) -> URLSessionWebSocketTask {
        var components = URLComponents(url: baseURL.appendingPathComponent("ws/voice"), resolvingAgainstBaseURL: false)!
        components.scheme = (baseURL.scheme == "https") ? "wss" : "ws"
        var items: [URLQueryItem] = []
        if let token { items.append(URLQueryItem(name: "token", value: token)) }
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
