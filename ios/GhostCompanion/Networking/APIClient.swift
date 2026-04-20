import Foundation

final class APIClient {
    private let session: URLSession
    private let keychain: KeychainStore
    private let settings: AppSettings
    private let decoder: JSONDecoder

    init(session: URLSession = .shared,
         keychain: KeychainStore = KeychainStore(),
         settings: AppSettings) {
        self.session = session
        self.keychain = keychain
        self.settings = settings
        self.decoder = JSONDecoder()
    }

    func jwt() -> String? { keychain.get() }
    func setJWT(_ token: String) { keychain.set(token) }
    func clearJWT() { keychain.clear() }

    private func baseURL() throws -> URL {
        guard let base = settings.baseURL else { throw APIError.invalidURL }
        return base
    }

    private func request(_ path: String,
                         method: String = "GET",
                         body: Data? = nil,
                         contentType: String? = nil,
                         authed: Bool = true,
                         timeout: TimeInterval = 20) throws -> URLRequest {
        let base = try baseURL()
        var req = URLRequest(url: Endpoints.path(path, base: base))
        req.httpMethod = method
        if let body { req.httpBody = body }
        if let contentType { req.setValue(contentType, forHTTPHeaderField: "Content-Type") }
        if authed, let token = keychain.get() {
            req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        req.timeoutInterval = timeout
        return req
    }

    private func send<T: Decodable>(_ req: URLRequest, as type: T.Type) async throws -> T {
        do {
            let (data, resp) = try await session.data(for: req)
            try validate(resp, data: data)
            do { return try decoder.decode(T.self, from: data) }
            catch { throw APIError.decode(error) }
        } catch let e as APIError { throw e }
        catch let e as URLError { throw APIError.network(e) }
    }

    private func sendVoid(_ req: URLRequest) async throws {
        do {
            let (data, resp) = try await session.data(for: req)
            try validate(resp, data: data)
        } catch let e as APIError { throw e }
        catch let e as URLError { throw APIError.network(e) }
    }

    private func validate(_ response: URLResponse, data: Data) throws {
        guard let http = response as? HTTPURLResponse else { return }
        if http.statusCode == 401 { throw APIError.unauthorized }
        if !(200..<300).contains(http.statusCode) {
            let body = String(data: data, encoding: .utf8)
            throw APIError.http(http.statusCode, body)
        }
    }

    // MARK: - Health / Auth

    func health() async throws {
        let req = try request("health", authed: false)
        _ = try await session.data(for: req)
    }

    func authStatus() async throws -> AuthStatus {
        try await send(request("auth/status", authed: true), as: AuthStatus.self)
    }

    func authorize() async throws -> AuthorizeResponse {
        try await send(request("oauth/authorize", authed: false), as: AuthorizeResponse.self)
    }

    func exchange(code: String) async throws -> CallbackResponse {
        let body = try JSONSerialization.data(withJSONObject: ["code": code])
        let req = try request("oauth/callback", method: "POST", body: body, contentType: "application/json", authed: false)
        return try await send(req, as: CallbackResponse.self)
    }

    func setBungieApiKey(_ key: String) async throws -> ApiKeyResponse {
        let body = try JSONSerialization.data(withJSONObject: ["api_key": key])
        let req = try request("auth/key", method: "POST", body: body, contentType: "application/json", authed: true)
        return try await send(req, as: ApiKeyResponse.self)
    }

    // MARK: - Conversations

    func listConversations() async throws -> [Conversation] {
        let req = try request("conversations")
        return try await send(req, as: ConversationsResponse.self).conversations
    }

    func createConversation(name: String, provider: String?) async throws -> String {
        var payload: [String: Any] = ["name": name]
        if let provider { payload["provider"] = provider }
        let body = try JSONSerialization.data(withJSONObject: payload)
        let req = try request("conversations", method: "POST", body: body, contentType: "application/json")
        return try await send(req, as: ConversationCreateResponse.self).id
    }

    func getConversation(id: String) async throws -> [Message] {
        let req = try request("conversations/\(id)")
        return try await send(req, as: ConversationMessagesResponse.self).messages
    }

    func updateConversation(id: String, name: String? = nil, provider: String? = nil) async throws {
        var payload: [String: Any] = [:]
        if let name { payload["name"] = name }
        if let provider { payload["provider"] = provider }
        let body = try JSONSerialization.data(withJSONObject: payload)
        let req = try request("conversations/\(id)", method: "PATCH", body: body, contentType: "application/json")
        try await sendVoid(req)
    }

    func deleteConversation(id: String) async throws {
        let req = try request("conversations/\(id)", method: "DELETE")
        try await sendVoid(req)
    }

    // MARK: - Discovery

    func models() async throws -> ModelsResponse {
        try await send(request("models", authed: false), as: ModelsResponse.self)
    }

    func personas() async throws -> [String] {
        try await send(request("personas", authed: false), as: PersonasResponse.self).personas
    }

    func voices() async throws -> [Voice] {
        try await send(request("voices", authed: false), as: VoicesResponse.self).voices
    }

    // MARK: - Diagnostics

    func audioDiagnostics() async throws -> AudioDiagnostics {
        try await send(request("diagnostics/audio", authed: false), as: AudioDiagnostics.self)
    }

    // MARK: - STT

    func transcribe(wav: Data, filename: String = "capture.wav") async throws -> String {
        let boundary = "Boundary-\(UUID().uuidString)"
        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: audio/wav\r\n\r\n".data(using: .utf8)!)
        body.append(wav)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)

        var req = try request("stt", method: "POST", authed: false, timeout: 60)
        req.httpBody = body
        req.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        return try await send(req, as: STTResponse.self).text
    }
}
