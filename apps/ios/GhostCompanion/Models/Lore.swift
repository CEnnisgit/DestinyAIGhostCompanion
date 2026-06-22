import Foundation

/// A lore entry from the backend Codex.
struct LoreEntry: Identifiable, Decodable, Equatable {
    let name: String
    let description: String
    let category: String?
    let source: String?

    var id: String { name }

    /// A short badge for non-curated (official/imported) entries.
    var sourceBadge: String? {
        switch source {
        case "bungie": return "OFFICIAL"
        case "import": return "IMPORT"
        default: return nil
        }
    }
}

/// A lore category with its entry count.
struct LoreCategory: Identifiable, Decodable, Equatable {
    let category: String
    let count: Int

    var id: String { category }
}
