import Foundation
import Observation

@Observable
@MainActor
final class AppState {
    enum Phase { case serverSetup, auth, ready }

    var phase: Phase = .serverSetup
    var toastError: String?

    let settings: AppSettings
    let keychain: KeychainStore
    let api: APIClient
    let streaming: StreamingChatClient
    let tts: TTSService

    init() {
        let settings = AppSettings()
        let keychain = KeychainStore()
        self.settings = settings
        self.keychain = keychain
        self.api = APIClient(keychain: keychain, settings: settings)
        self.streaming = StreamingChatClient(settings: settings, keychain: keychain)
        self.tts = TTSService()
    }

    func bootstrap() async {
        if settings.baseURL == nil {
            phase = .serverSetup
            return
        }
        do {
            _ = try await api.authStatus()
            if keychain.get() != nil {
                phase = .ready
            } else {
                phase = .auth
            }
        } catch APIError.unauthorized {
            keychain.clear()
            phase = .auth
        } catch APIError.invalidURL {
            phase = .serverSetup
        } catch {
            // Server unreachable — send back to setup so user can correct the URL.
            phase = .serverSetup
        }
    }

    func signOut() {
        keychain.clear()
        settings.clearSession()
        phase = .auth
    }

    func presentError(_ message: String) {
        toastError = message
    }
}
