import Foundation

struct AuthStatus: Codable {
    let authenticated: Bool
    let bungie_linked: Bool
    let api_key_ok: Bool?
    let api_key_masked: String?
    let api_key_error: String?
}

struct AuthorizeResponse: Codable {
    let authorization_url: String
    let redirect_uri: String?
}

struct CallbackResponse: Codable {
    let ok: Bool?
    let token: String?
    let bungie_linked: Bool?
}

struct ApiKeyResponse: Codable {
    let ok: Bool
    let error: String?
}
