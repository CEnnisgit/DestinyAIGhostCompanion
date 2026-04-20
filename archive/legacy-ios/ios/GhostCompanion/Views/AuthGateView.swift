import SwiftUI

struct AuthGateView: View {
    @Environment(AppState.self) private var appState
    @State private var vm: AuthViewModel?

    var body: some View {
        let vm = binding()
        VStack(spacing: 28) {
            Spacer()
            VStack(spacing: 8) {
                Image(systemName: "shield.lefthalf.filled")
                    .font(.system(size: 42))
                    .foregroundStyle(Theme.accent)
                Text("Sign in with Bungie")
                    .font(Typography.title)
                Text("Link your Guardian to chat with the Ghost.")
                    .font(Typography.body)
                    .foregroundStyle(Theme.textMuted)
                    .multilineTextAlignment(.center)
            }
            .padding(.horizontal, 24)

            if let error = vm.errorMessage {
                ErrorBanner(message: error) { vm.errorMessage = nil }
            }

            Button {
                Task { await vm.signIn() }
            } label: {
                HStack {
                    if vm.inProgress { ProgressView().tint(.black) }
                    Text(vm.inProgress ? "Opening Bungie…" : "Sign in with Bungie")
                        .font(.headline)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 14)
                .background(Theme.accent, in: Capsule())
                .foregroundStyle(Color.black)
            }
            .disabled(vm.inProgress)
            .padding(.horizontal, 24)

            Button("Change server") {
                appState.phase = .serverSetup
            }
            .font(Typography.meta)
            .foregroundStyle(Theme.textMuted)

            Spacer()
        }
        .task { await vm.refreshStatus() }
    }

    private func binding() -> AuthViewModel {
        if let vm { return vm }
        let created = AuthViewModel(appState: appState)
        vm = created
        return created
    }
}
