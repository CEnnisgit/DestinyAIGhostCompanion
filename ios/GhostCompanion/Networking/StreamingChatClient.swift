import Foundation

enum ChatEvent {
    case conversationId(String)
    case chunk(String)
    case done
}

final class StreamingChatClient {
    private let session: URLSession
    private let settings: AppSettings
    private let keychain: KeychainStore

    init(session: URLSession = .shared,
         settings: AppSettings,
         keychain: KeychainStore = KeychainStore()) {
        self.session = session
        self.settings = settings
        self.keychain = keychain
    }

    func stream(_ query: ChatQuery) -> AsyncThrowingStream<ChatEvent, Error> {
        AsyncThrowingStream { continuation in
            let task = Task {
                do {
                    guard let base = settings.baseURL,
                          let url = Endpoints.chatStream(base: base, query: query) else {
                        throw APIError.invalidURL
                    }
                    var req = URLRequest(url: url)
                    req.timeoutInterval = 600
                    if let token = keychain.get() {
                        req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
                    }
                    let (bytes, resp) = try await session.bytes(for: req)
                    if let http = resp as? HTTPURLResponse {
                        if http.statusCode == 401 {
                            continuation.finish(throwing: APIError.unauthorized)
                            return
                        }
                        if !(200..<300).contains(http.statusCode) {
                            continuation.finish(throwing: APIError.http(http.statusCode, nil))
                            return
                        }
                        if let cid = http.value(forHTTPHeaderField: "X-Conversation-Id") {
                            continuation.yield(.conversationId(cid))
                        }
                    }
                    var buffer = Data()
                    for try await byte in bytes {
                        if Task.isCancelled { throw APIError.cancelled }
                        buffer.append(byte)
                        if let decoded = decodeUTF8(&buffer) {
                            continuation.yield(.chunk(decoded))
                        }
                    }
                    if !buffer.isEmpty, let tail = String(data: buffer, encoding: .utf8) {
                        continuation.yield(.chunk(tail))
                    }
                    continuation.yield(.done)
                    continuation.finish()
                } catch let e as APIError {
                    continuation.finish(throwing: e)
                } catch let e as URLError {
                    continuation.finish(throwing: APIError.network(e))
                } catch {
                    continuation.finish(throwing: error)
                }
            }
            continuation.onTermination = { _ in task.cancel() }
        }
    }

    /// Drains `buffer` into a UTF-8 string, keeping any trailing partial code point bytes.
    private func decodeUTF8(_ buffer: inout Data) -> String? {
        guard !buffer.isEmpty else { return nil }
        // Try to decode the whole buffer; if it fails, back off from the tail until it succeeds.
        for trim in 0..<min(4, buffer.count) {
            let candidate = buffer.prefix(buffer.count - trim)
            if let s = String(data: candidate, encoding: .utf8), !s.isEmpty {
                buffer.removeFirst(candidate.count)
                return s
            }
        }
        return nil
    }
}
