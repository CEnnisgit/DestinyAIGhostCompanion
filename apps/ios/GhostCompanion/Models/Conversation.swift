import Foundation

/// Server-synced thread summary (from GET /conversations).
struct SyncedThreadSummary: Decodable {
    let id: String
    let title: String
    let updated_at: String
}

/// Server-synced message (from GET /conversations/:id).
struct SyncedMessage: Decodable {
    let id: String
    let role: String
    let text: String
    let intent: String?
    let created_at: String
}

/// A full server-synced thread with its messages.
struct SyncedThread: Decodable {
    let id: String
    let title: String
    let updated_at: String
    let messages: [SyncedMessage]
}

/// A saved chat thread with the Ghost.
struct Conversation: Identifiable, Codable, Equatable {
    let id: UUID
    var title: String
    var messages: [ChatMessage]
    let createdAt: Date
    var updatedAt: Date

    init(
        id: UUID = UUID(),
        title: String = "New Conversation",
        messages: [ChatMessage] = [],
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) {
        self.id = id
        self.title = title
        self.messages = messages
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }

    var isEmpty: Bool { messages.isEmpty }

    /// Derives a short title from the first Guardian message.
    static func title(from text: String) -> String {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        return String(trimmed.prefix(40))
    }
}
