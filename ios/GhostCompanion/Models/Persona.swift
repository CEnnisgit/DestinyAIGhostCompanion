import Foundation

struct Persona: Identifiable, Hashable {
    let id: String
    var displayName: String {
        id.replacingOccurrences(of: "_", with: " ")
            .split(separator: " ")
            .map { $0.prefix(1).uppercased() + $0.dropFirst() }
            .joined(separator: " ")
    }
}

struct PersonasResponse: Codable {
    let personas: [String]
}
