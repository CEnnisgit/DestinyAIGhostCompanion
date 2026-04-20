import Foundation

struct Message: Identifiable, Codable, Hashable {
    let id: String
    let role: String
    var content: String
    let ts: Double?
    var streaming: Bool

    init(id: String = UUID().uuidString,
         role: String,
         content: String,
         ts: Double? = nil,
         streaming: Bool = false) {
        self.id = id
        self.role = role
        self.content = content
        self.ts = ts
        self.streaming = streaming
    }

    enum CodingKeys: String, CodingKey {
        case id, role, content, ts
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        self.id = try c.decodeIfPresent(String.self, forKey: .id) ?? UUID().uuidString
        self.role = try c.decode(String.self, forKey: .role)
        self.content = try c.decode(String.self, forKey: .content)
        self.ts = try c.decodeIfPresent(Double.self, forKey: .ts)
        self.streaming = false
    }

    var isUser: Bool { role == "user" }
    var isAssistant: Bool { role == "assistant" }
}
