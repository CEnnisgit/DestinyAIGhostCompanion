import Foundation

/// A Destiny character returned by the backend `/characters` endpoint.
struct CharacterSummary: Identifiable, Decodable, Equatable {
    let characterId: String
    let classType: Int
    let className: String
    let light: Int

    var id: String { characterId }
}
