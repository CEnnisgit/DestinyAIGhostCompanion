import XCTest
@testable import GhostCompanion

final class APIClientTests: XCTestCase {
    func testEndpointChatStreamBuilder() throws {
        let base = URL(string: "http://example.com:8000")!
        let query = ChatQuery(
            message: "hi",
            provider: "ollama",
            model: "llama3",
            persona: "destiny_ghost",
            speak: true,
            voice: "system",
            sessionId: "abc"
        )
        let url = try XCTUnwrap(Endpoints.chatStream(base: base, query: query))
        let items = URLComponents(url: url, resolvingAgainstBaseURL: false)?.queryItems ?? []
        let dict = Dictionary(uniqueKeysWithValues: items.map { ($0.name, $0.value ?? "") })
        XCTAssertEqual(dict["message"], "hi")
        XCTAssertEqual(dict["provider"], "ollama")
        XCTAssertEqual(dict["model"], "llama3")
        XCTAssertEqual(dict["persona"], "destiny_ghost")
        XCTAssertEqual(dict["speak"], "1")
        XCTAssertEqual(dict["voice"], "system")
        XCTAssertEqual(dict["session_id"], "abc")
        XCTAssertEqual(url.path, "/chat/stream")
    }

    func testEndpointPathAppending() {
        let base = URL(string: "http://localhost:8000")!
        let url = Endpoints.path("conversations/xyz", base: base)
        XCTAssertEqual(url.absoluteString, "http://localhost:8000/conversations/xyz")
    }

    func testAPIErrorDescriptions() {
        XCTAssertNotNil(APIError.invalidURL.errorDescription)
        XCTAssertNotNil(APIError.unauthorized.errorDescription)
        XCTAssertNotNil(APIError.http(500, "boom").errorDescription)
    }
}
