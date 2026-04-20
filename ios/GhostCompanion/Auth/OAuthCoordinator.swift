import Foundation
import AuthenticationServices

enum OAuthError: Error, LocalizedError {
    case invalidURL
    case userCancelled
    case missingCode
    case exchangeFailed(String)

    var errorDescription: String? {
        switch self {
        case .invalidURL: return "Invalid authorization URL."
        case .userCancelled: return "Sign-in was cancelled."
        case .missingCode: return "Bungie did not return an authorization code."
        case .exchangeFailed(let msg): return "Sign-in failed: \(msg)"
        }
    }
}

@MainActor
final class OAuthCoordinator {
    static let callbackScheme = "ghostcompanion"
    static let callbackURL = "ghostcompanion://oauth/callback"

    private let api: APIClient
    private let presenter = WebAuthPresenter()
    private var currentSession: ASWebAuthenticationSession?

    init(api: APIClient) { self.api = api }

    /// Runs the full OAuth flow; returns the JWT on success.
    func signIn() async throws -> String {
        let authorize = try await api.authorize()
        guard let remoteURL = URL(string: authorize.authorization_url) else {
            throw OAuthError.invalidURL
        }
        let startURL = rewriteRedirect(remoteURL)

        let callbackURL: URL = try await withCheckedThrowingContinuation { continuation in
            let session = ASWebAuthenticationSession(
                url: startURL,
                callbackURLScheme: Self.callbackScheme
            ) { url, error in
                if let error = error as? ASWebAuthenticationSessionError, error.code == .canceledLogin {
                    continuation.resume(throwing: OAuthError.userCancelled); return
                }
                if let error { continuation.resume(throwing: error); return }
                guard let url else { continuation.resume(throwing: OAuthError.missingCode); return }
                continuation.resume(returning: url)
            }
            session.presentationContextProvider = presenter
            session.prefersEphemeralWebBrowserSession = false
            currentSession = session
            if !session.start() {
                continuation.resume(throwing: OAuthError.invalidURL)
            }
        }

        guard let code = extractCode(from: callbackURL) else {
            throw OAuthError.missingCode
        }
        let resp = try await api.exchange(code: code)
        guard let token = resp.token, !token.isEmpty else {
            throw OAuthError.exchangeFailed("no token returned")
        }
        api.setJWT(token)
        return token
    }

    /// Rewrites the `redirect_uri` in Bungie's authorize URL to the native scheme.
    private func rewriteRedirect(_ url: URL) -> URL {
        guard var comps = URLComponents(url: url, resolvingAgainstBaseURL: false) else { return url }
        var items = comps.queryItems ?? []
        if let idx = items.firstIndex(where: { $0.name == "redirect_uri" }) {
            items[idx].value = Self.callbackURL
        } else {
            items.append(URLQueryItem(name: "redirect_uri", value: Self.callbackURL))
        }
        comps.queryItems = items
        return comps.url ?? url
    }

    private func extractCode(from url: URL) -> String? {
        let comps = URLComponents(url: url, resolvingAgainstBaseURL: false)
        return comps?.queryItems?.first(where: { $0.name == "code" })?.value
    }
}
