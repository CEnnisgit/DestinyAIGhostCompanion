import Foundation

@MainActor
final class SettingsStore: ObservableObject {
    @Published var appConfig: AppConfigResponse?
    @Published var errorMessage: String?

    func refresh(using auth: AuthStore) async {
        do {
            appConfig = try await auth.client().fetchAppConfig()
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
