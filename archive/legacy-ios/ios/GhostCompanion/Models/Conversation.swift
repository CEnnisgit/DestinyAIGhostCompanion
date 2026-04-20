import Foundation

struct Conversation: Identifiable, Codable, Hashable {
    let id: String
    var name: String
    var provider: String?
    let created_at: Double?
    var updated_at: Double?
    var last_message: String?
}

struct ConversationsResponse: Codable {
    let conversations: [Conversation]
}

struct ConversationCreateResponse: Codable {
    let id: String
}

struct ConversationMessagesResponse: Codable {
    let messages: [Message]
}
