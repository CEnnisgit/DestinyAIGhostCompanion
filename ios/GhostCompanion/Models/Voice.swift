import Foundation

struct Voice: Identifiable, Codable, Hashable {
    var id: String { key }
    let key: String
    let name: String
    let provider: String?
    let personas: [String]?
}

struct VoicesResponse: Codable {
    let voices: [Voice]
}

extension Voice {
    static let system = Voice(key: "system", name: "System (on-device)", provider: "system", personas: nil)

    var isOnDevice: Bool { key == "system" || provider == "system" }
}
