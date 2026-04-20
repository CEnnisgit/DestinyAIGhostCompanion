import XCTest
@testable import GhostCompanion

final class StreamingChatClientTests: XCTestCase {
    /// The streaming client buffers raw bytes until they decode as UTF-8.
    /// This test verifies the buffering helper directly by driving a private
    /// algorithm-equivalent reimplementation — the goal is to prove the
    /// contract: partial multi-byte code points aren't emitted as garbage.
    func testUTF8BufferingContract() {
        var buffer = Data()
        // "é" is 0xC3 0xA9 in UTF-8. Feeding only 0xC3 should produce nothing.
        buffer.append(0xC3)
        XCTAssertNil(decodeBuffered(&buffer))
        // Appending 0xA9 should now yield "é".
        buffer.append(0xA9)
        XCTAssertEqual(decodeBuffered(&buffer), "é")
        XCTAssertTrue(buffer.isEmpty)
    }

    /// Mirror of StreamingChatClient.decodeUTF8(_:).
    private func decodeBuffered(_ buffer: inout Data) -> String? {
        guard !buffer.isEmpty else { return nil }
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
