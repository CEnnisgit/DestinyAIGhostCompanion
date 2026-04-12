import SwiftUI

@main
struct GhostCompanionApp: App {
    @StateObject private var authStore = AuthStore()
    @StateObject private var chatStore = ChatStore()
    @StateObject private var inventoryStore = InventoryStore()
    @StateObject private var settingsStore = SettingsStore()

    var body: some Scene {
        WindowGroup {
            RootTabView()
                .environmentObject(authStore)
                .environmentObject(chatStore)
                .environmentObject(inventoryStore)
                .environmentObject(settingsStore)
                .task {
                    await authStore.refreshStatus()
                    await settingsStore.refresh(using: authStore)
                }
                .onOpenURL { url in
                    Task {
                        await authStore.handleCallback(url)
                        await settingsStore.refresh(using: authStore)
                        if authStore.isAuthenticated {
                            await chatStore.bootstrap(using: authStore)
                            await inventoryStore.refresh(using: authStore)
                        }
                    }
                }
        }
    }
}
