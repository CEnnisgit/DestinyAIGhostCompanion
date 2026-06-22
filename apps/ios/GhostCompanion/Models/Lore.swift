import Foundation

/// A lore entry from the backend Codex.
struct LoreEntry: Identifiable, Decodable, Equatable {
    let name: String
    let description: String
    let category: String?

    var id: String { name }
}

/// A lore category with its entry count.
struct LoreCategory: Identifiable, Decodable, Equatable {
    let category: String
    let count: Int

    var id: String { category }
}
