import Foundation

struct ModelsResponse: Codable {
    let ollama: [String]?
}

struct STTResponse: Codable {
    let text: String
}

struct HealthResponse: Codable {
    let ok: Bool?
}
