import Foundation

/// Outbound frame to `/ws/voice`.
struct OutboundVoice: Encodable {
    let text: String
}

/// Inbound frame from `/ws/voice`.
struct InboundVoice: Decodable {
    let response: String
    let intent: String
}

/// A single line in the conversation transcript.
struct ChatMessage: Identifiable, Equatable, Codable {
    enum Role: String, Codable { case guardian, ghost }

    var id = UUID()
    let role: Role
    let text: String
    var intent: String?
}
