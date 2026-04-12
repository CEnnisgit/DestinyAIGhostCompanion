import SwiftUI

struct RootTabView: View {
    @EnvironmentObject private var authStore: AuthStore
    @EnvironmentObject private var chatStore: ChatStore
    @EnvironmentObject private var inventoryStore: InventoryStore
    @EnvironmentObject private var settingsStore: SettingsStore

    var body: some View {
        TabView {
            ChatView()
                .tabItem {
                    Label("Chat", systemImage: "message")
                }

            InventoryView()
                .tabItem {
                    Label("Inventory", systemImage: "shippingbox")
                }

            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gearshape")
                }
        }
        .task(id: authStore.token) {
            guard authStore.isAuthenticated else { return }
            await chatStore.bootstrap(using: authStore)
            await inventoryStore.refresh(using: authStore)
            await settingsStore.refresh(using: authStore)
        }
    }
}
