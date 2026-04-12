import Foundation

enum APIClientError: LocalizedError {
    case invalidURL
    case invalidResponse
    case server(String)
    case unauthorized

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "The backend URL is invalid."
        case .invalidResponse:
            return "The backend returned an unexpected response."
        case .server(let detail):
            return detail
        case .unauthorized:
            return "Sign in is required."
        }
    }
}

final class APIClient {
    private let baseURL: URL
    private let token: String?
    private let session: URLSession

    init(baseURL: String, token: String? = nil, session: URLSession = .shared) throws {
        guard let url = URL(string: baseURL.trimmingCharacters(in: .whitespacesAndNewlines)),
              let scheme = url.scheme else {
            throw APIClientError.invalidURL
        }
        if scheme != "http" && scheme != "https" {
            throw APIClientError.invalidURL
        }
        self.baseURL = url
        self.token = token
        self.session = session
    }

    func mobileAuthorizeURL(callbackScheme: String = "ghostcompanion") -> URL {
        var components = URLComponents(url: baseURL.appending(path: "/oauth/mobile/authorize"), resolvingAgainstBaseURL: false)!
        components.queryItems = [URLQueryItem(name: "callback_scheme", value: callbackScheme)]
        return components.url!
    }

    func fetchAppConfig() async throws -> AppConfigResponse {
        try await send(path: "/api/v1/app-config", method: "GET", body: Optional<String>.none)
    }

    func fetchAuthStatus() async throws -> AuthStatusResponse {
        try await send(path: "/auth/status", method: "GET", body: Optional<String>.none)
    }

    func fetchConversations() async throws -> [ConversationSummary] {
        let response: ConversationListResponse = try await send(path: "/conversations", method: "GET", body: Optional<String>.none)
        return response.conversations
    }

    func createConversation(name: String, provider: String?) async throws -> ConversationCreateResponse {
        let request = ConversationCreateRequest(name: name, provider: provider)
        return try await send(path: "/conversations", method: "POST", body: request)
    }

    func fetchConversation(_ conversationID: String) async throws -> [ConversationMessage] {
        let response: ConversationDetailResponse = try await send(path: "/conversations/\(conversationID)", method: "GET", body: Optional<String>.none)
        return response.messages
    }

    func fetchInventory() async throws -> InventoryResponse {
        try await send(path: "/api/v1/inventory", method: "GET", body: Optional<String>.none)
    }

    func previewAction(action: String, itemInstanceID: String, targetCharacterID: String?) async throws -> ActionPreviewResponse {
        let request = ActionPreviewRequest(action: action, itemInstanceId: itemInstanceID, targetCharacterId: targetCharacterID)
        return try await send(path: "/api/v1/items/actions/preview", method: "POST", body: request)
    }

    func executeAction(confirmationToken: String) async throws -> ActionExecuteResponse {
        let request = ActionExecuteRequest(confirmationToken: confirmationToken)
        return try await send(path: "/api/v1/items/actions/execute", method: "POST", body: request)
    }

    func voiceTurn(text: String, sessionID: String?) async throws -> VoiceTurnResponse {
        let request = VoiceTurnRequest(text: text, sessionId: sessionID)
        return try await send(path: "/api/v1/voice/turn", method: "POST", body: request)
    }

    func streamChat(
        message: String,
        sessionID: String?,
        provider: String?,
        persona: String?,
        model: String?,
        onConversation: @escaping @MainActor (String) -> Void,
        onChunk: @escaping @MainActor (String) -> Void
    ) async throws {
        guard token != nil else {
            throw APIClientError.unauthorized
        }
        var components = URLComponents(url: baseURL.appending(path: "/chat/stream"), resolvingAgainstBaseURL: false)!
        components.queryItems = [
            URLQueryItem(name: "message", value: message),
            URLQueryItem(name: "session_id", value: sessionID),
            URLQueryItem(name: "provider", value: provider),
            URLQueryItem(name: "persona", value: persona),
            URLQueryItem(name: "model", value: model)
        ].filter { ($0.value ?? "").isEmpty == false }
        guard let url = components.url else {
            throw APIClientError.invalidURL
        }
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        if let token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let (bytes, response) = try await session.bytes(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw APIClientError.invalidResponse
        }
        guard (200 ..< 300).contains(http.statusCode) else {
            throw try await decodeServerError(from: bytes)
        }
        if let conversationID = http.value(forHTTPHeaderField: "X-Conversation-Id"), !conversationID.isEmpty {
            await onConversation(conversationID)
        }

        var buffer = Data()
        for try await byte in bytes {
            buffer.append(byte)
            if buffer.count >= 96 {
                let text = String(decoding: buffer, as: UTF8.self)
                if !text.isEmpty {
                    await onChunk(text)
                }
                buffer.removeAll(keepingCapacity: true)
            }
        }
        if !buffer.isEmpty {
            let text = String(decoding: buffer, as: UTF8.self)
            if !text.isEmpty {
                await onChunk(text)
            }
        }
    }

    private func send<Response: Decodable, Body: Encodable>(
        path: String,
        method: String,
        body: Body?
    ) async throws -> Response {
        let request = try buildRequest(path: path, method: method, body: body)
        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw APIClientError.invalidResponse
        }
        guard (200 ..< 300).contains(http.statusCode) else {
            throw try decodeServerError(from: data)
        }
        return try decoder.decode(Response.self, from: data)
    }

    private func buildRequest<Body: Encodable>(path: String, method: String, body: Body?) throws -> URLRequest {
        let url = baseURL.appending(path: path)
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        if let token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        if let body {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONEncoder().encode(body)
        }
        return request
    }

    private var decoder: JSONDecoder {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return decoder
    }

    private func decodeServerError(from data: Data) throws -> Error {
        if let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let detail = object["detail"] as? String {
            return APIClientError.server(detail)
        }
        return APIClientError.invalidResponse
    }

    private func decodeServerError(from bytes: URLSession.AsyncBytes) async throws -> Error {
        var data = Data()
        for try await byte in bytes {
            data.append(byte)
        }
        return try decodeServerError(from: data)
    }
}
