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
    @Published private(set) var characters: [CharacterSummary] = []
    @Published private(set) var selectedCharacterID: String?
    @Published private(set) var isLoadingCharacters = false
    @Published private(set) var profileSummary: String?

    private let service = "com.cennis.ghostcompanion"
    private let account = "bungie.membership_id"
    private let sessionAccount = "bungie.session_token"
    private let characterKey = "ghost.character_id"
    private let callbackScheme = "ghostcompanion"
    private var session: ASWebAuthenticationSession?

    override init() {
        super.init()
        membershipID = KeychainStore.load(service: service, account: account)
        selectedCharacterID = UserDefaults.standard.string(forKey: characterKey)
    }

    var isSignedIn: Bool { membershipID != nil }

    /// Loads the user's characters from the backend (after sign-in).
    func loadCharacters(backendURLString: String) async {
        guard let membershipID, let backend = GhostBackend(baseURLString: backendURLString) else { return }
        isLoadingCharacters = true
        defer { isLoadingCharacters = false }
        do {
            let result = try await backend.characters(membershipID: membershipID)
            characters = result
            if selectedCharacterID == nil || !result.contains(where: { $0.characterId == selectedCharacterID }) {
                selectCharacter(result.first?.characterId)
            }
        } catch {
            errorMessage = error.localizedDescription
        }
        profileSummary = try? await backend.profileSummary(membershipID: membershipID)
    }

    func selectCharacter(_ id: String?) {
        selectedCharacterID = id
        if let id {
            UserDefaults.standard.set(id, forKey: characterKey)
        } else {
            UserDefaults.standard.removeObject(forKey: characterKey)
        }
    }

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
        // Persist the signed session token so every API call is authenticated.
        if let token = components?.queryItems?.first(where: { $0.name == "session" })?.value,
           !token.isEmpty {
            KeychainStore.save(token, service: service, account: sessionAccount)
        }
        KeychainStore.save(id, service: service, account: account)
        membershipID = id
    }

    func signOut(backendURLString: String) {
        // Revoke server-side first (the token is still in the Keychain), then
        // discard local credentials.
        if let backend = GhostBackend(baseURLString: backendURLString) {
            Task { await backend.logout() }
        }
        KeychainStore.delete(service: service, account: account)
        KeychainStore.delete(service: service, account: sessionAccount)
        membershipID = nil
        characters = []
        profileSummary = nil
        selectCharacter(nil)
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
