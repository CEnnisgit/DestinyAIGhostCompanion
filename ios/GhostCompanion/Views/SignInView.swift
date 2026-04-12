import AuthenticationServices
import SwiftUI
import UIKit

struct SignInView: View {
    @EnvironmentObject private var authStore: AuthStore
    @State private var session: ASWebAuthenticationSession?

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Ghost Companion")
                .font(.largeTitle.bold())

            Text("Sign in through the backend Bungie OAuth flow. Inventory and chat stay server-backed so web and iPhone stay in sync.")
                .foregroundStyle(.secondary)

            TextField("Backend URL", text: Binding(
                get: { authStore.backendBaseURL },
                set: { authStore.saveBackendBaseURL($0) }
            ))
            .textInputAutocapitalization(.never)
            .autocorrectionDisabled()
            .textFieldStyle(.roundedBorder)

            Button("Continue with Bungie") {
                startSignIn()
            }
            .buttonStyle(.borderedProminent)

            if let errorMessage = authStore.errorMessage, !errorMessage.isEmpty {
                Text(errorMessage)
                    .font(.footnote)
                    .foregroundStyle(.red)
            }
        }
        .padding()
    }

    private func startSignIn() {
        do {
            let url = try authStore.signInURL()
            let session = ASWebAuthenticationSession(url: url, callbackURLScheme: "ghostcompanion") { callbackURL, error in
                Task { @MainActor in
                    if let callbackURL {
                        await authStore.handleCallback(callbackURL)
                    } else if let error {
                        authStore.errorMessage = error.localizedDescription
                    }
                }
            }
            session.prefersEphemeralWebBrowserSession = true
            session.presentationContextProvider = SignInPresentationAnchor.shared
            self.session = session
            session.start()
        } catch {
            authStore.errorMessage = error.localizedDescription
        }
    }
}

final class SignInPresentationAnchor: NSObject, ASWebAuthenticationPresentationContextProviding {
    static let shared = SignInPresentationAnchor()

    func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        let scenes = UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }
        let windows = scenes.flatMap(\.windows)
        return windows.first(where: \.isKeyWindow) ?? ASPresentationAnchor()
    }
}
