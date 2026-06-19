import AuthenticationServices
import SwiftUI
import UIKit

/// Drives Bungie OAuth via `ASWebAuthenticationSession`. The backend completes the
/// code exchange and redirects to `ghostcompanion://auth?membership_id=...`
/// (requires `GHOST_MOBILE_CALLBACK=ghostcompanion://auth` on the server).
@MainActor
final class AuthStore: NSObject, ObservableObject, ASWebAuthenticationPresentationContextProviding {
    @Published private(set) var membershipID: String?
    @Published private(set) var isAuthenticating = false
    @Published var errorMessage: String?

    private let service = "com.cennis.ghostcompanion"
    private let account = "bungie.membership_id"
    private let callbackScheme = "ghostcompanion"
    private var session: ASWebAuthenticationSession?

    override init() {
        super.init()
        membershipID = KeychainStore.load(service: service, account: account)
    }

    var isSignedIn: Bool { membershipID != nil }

    func signIn(backendURLString: String) {
        guard let backend = GhostBackend(baseURLString: backendURLString) else {
            errorMessage = "Invalid backend URL"
            return
        }
        isAuthenticating = true
        errorMessage = nil

        let session = ASWebAuthenticationSession(
            url: backend.loginURL,
            callbackURLScheme: callbackScheme
        ) { [weak self] callbackURL, error in
            Task { @MainActor in
                guard let self else { return }
                self.isAuthenticating = false
                if let error {
                    if (error as? ASWebAuthenticationSessionError)?.code != .canceledLogin {
                        self.errorMessage = error.localizedDescription
                    }
                    return
                }
                if let callbackURL { self.handleCallback(callbackURL) }
            }
        }
        session.presentationContextProvider = self
        self.session = session
        session.start()
    }

    func handleCallback(_ url: URL) {
        let components = URLComponents(url: url, resolvingAgainstBaseURL: false)
        guard let id = components?.queryItems?.first(where: { $0.name == "membership_id" })?.value,
              !id.isEmpty
        else {
            errorMessage = "Sign-in did not return a membership id."
            return
        }
        KeychainStore.save(id, service: service, account: account)
        membershipID = id
    }

    func signOut() {
        KeychainStore.delete(service: service, account: account)
        membershipID = nil
    }

    // MARK: - ASWebAuthenticationPresentationContextProviding

    func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        let window = UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .flatMap { $0.windows }
            .first { $0.isKeyWindow }
        return window ?? ASPresentationAnchor()
    }
}
