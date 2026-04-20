import Foundation
import Observation

@Observable
@MainActor
final class AuthViewModel {
    private let appState: AppState
    private lazy var coordinator = OAuthCoordinator(api: appState.api)

    var status: AuthStatus?
    var errorMessage: String?
    var inProgress: Bool = false

    init(appState: AppState) { self.appState = appState }

    func refreshStatus() async {
        do {
            status = try await appState.api.authStatus()
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
    }

    func signIn() async {
        inProgress = true
        defer { inProgress = false }
        do {
            _ = try await coordinator.signIn()
            await refreshStatus()
            appState.phase = .ready
        } catch OAuthError.userCancelled {
            // Quiet cancel — no banner.
        } catch {
            errorMessage = (error as? LocalizedError)?.errorDescription ?? error.localizedDescription
        }
    }
}
