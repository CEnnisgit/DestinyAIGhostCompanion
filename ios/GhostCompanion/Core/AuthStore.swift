import Foundation

@MainActor
final class AuthStore: ObservableObject {
    @Published var backendBaseURL: String
    @Published var token: String?
    @Published var status = AuthStatusResponse(authenticated: false, bungieLinked: false, apiKeyOk: false, apiKeyMasked: "")
    @Published var isRefreshing = false
    @Published var errorMessage: String?

    private let defaults = UserDefaults.standard
    private let backendKey = "ghost.backend.base_url"
    private let keychainService = "GhostCompanion"
    private let keychainAccount = "backend-token"

    init() {
        self.backendBaseURL = UserDefaults.standard.string(forKey: "ghost.backend.base_url") ?? "http://127.0.0.1:8000"
        self.token = KeychainStore.load(service: "GhostCompanion", account: "backend-token")
    }

    var isAuthenticated: Bool {
        status.authenticated && (token?.isEmpty == false)
    }

    func client() throws -> APIClient {
        try APIClient(baseURL: backendBaseURL, token: token)
    }

    func saveBackendBaseURL(_ value: String) {
        backendBaseURL = value.trimmingCharacters(in: .whitespacesAndNewlines)
        defaults.set(backendBaseURL, forKey: backendKey)
    }

    func refreshStatus() async {
        isRefreshing = true
        defer { isRefreshing = false }
        do {
            let status = try await client().fetchAuthStatus()
            self.status = status
            self.errorMessage = nil
        } catch {
            self.errorMessage = error.localizedDescription
        }
    }

    func signInURL() throws -> URL {
        try client().mobileAuthorizeURL()
    }

    func handleCallback(_ url: URL) async {
        guard url.scheme?.lowercased() == "ghostcompanion" else { return }
        guard let components = URLComponents(url: url, resolvingAgainstBaseURL: false) else { return }
        let tokenValue = components.queryItems?.first(where: { $0.name == "token" })?.value
        if let tokenValue, !tokenValue.isEmpty {
            token = tokenValue
            KeychainStore.save(tokenValue, service: keychainService, account: keychainAccount)
        }
        await refreshStatus()
    }

    func signOut() {
        token = nil
        status = AuthStatusResponse(authenticated: false, bungieLinked: false, apiKeyOk: status.apiKeyOk, apiKeyMasked: status.apiKeyMasked)
        KeychainStore.delete(service: keychainService, account: keychainAccount)
    }
}
