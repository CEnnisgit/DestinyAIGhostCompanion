import XCTest
@testable import GhostCompanion

final class KeychainStoreTests: XCTestCase {
    func testRoundTrip() {
        let store = KeychainStore(service: "com.ghostcompanion.ios.tests", account: "test-jwt")
        store.clear()
        XCTAssertNil(store.get())
        XCTAssertTrue(store.set("jwt-value"))
        XCTAssertEqual(store.get(), "jwt-value")
        XCTAssertTrue(store.clear())
        XCTAssertNil(store.get())
    }

    func testOverwrite() {
        let store = KeychainStore(service: "com.ghostcompanion.ios.tests", account: "test-jwt-2")
        store.clear()
        XCTAssertTrue(store.set("one"))
        XCTAssertTrue(store.set("two"))
        XCTAssertEqual(store.get(), "two")
        store.clear()
    }
}
