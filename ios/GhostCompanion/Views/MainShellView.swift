import SwiftUI

struct MainShellView: View {
    @Environment(AppState.self) private var appState
    @State private var conversationsVM: ConversationsViewModel?
    @State private var chatVM: ChatViewModel?
    @State private var settingsVM: SettingsViewModel?
    @State private var drawerOpen: Bool = false
    @State private var showSettings: Bool = false

    private let drawerWidth: CGFloat = min(320, UIScreen.main.bounds.width * 0.86)

    var body: some View {
        let convVM = convBinding()
        let chat = chatBinding(conversations: convVM)
        let settingsVM = settingsBinding()

        GeometryReader { _ in
            ZStack(alignment: .leading) {
                ChatView(drawerOpen: $drawerOpen, showSettings: $showSettings)
                    .environment(chat)
                    .environment(convVM)
                    .disabled(drawerOpen)

                if drawerOpen {
                    Color.black.opacity(0.45)
                        .ignoresSafeArea()
                        .transition(.opacity)
                        .onTapGesture { withAnimation(.spring(response: 0.3)) { drawerOpen = false } }
                }

                ConversationsDrawer(
                    width: drawerWidth,
                    onClose: { withAnimation(.spring(response: 0.3)) { drawerOpen = false } },
                    onOpenSettings: {
                        withAnimation(.spring(response: 0.3)) { drawerOpen = false }
                        showSettings = true
                    },
                    onOpenConversation: { id in
                        withAnimation(.spring(response: 0.3)) { drawerOpen = false }
                        Task {
                            convVM.setActive(id)
                            await chat.load(conversationId: id)
                        }
                    },
                    onNewChat: {
                        withAnimation(.spring(response: 0.3)) { drawerOpen = false }
                        Task {
                            convVM.setActive("")
                            chat.reset()
                        }
                    }
                )
                .environment(convVM)
                .frame(width: drawerWidth)
                .offset(x: drawerOpen ? 0 : -drawerWidth)
                .animation(.spring(response: 0.3), value: drawerOpen)
            }
        }
        .task {
            await convVM.refresh()
            if !convVM.activeId.isEmpty {
                await chat.load(conversationId: convVM.activeId)
            }
        }
        .sheet(isPresented: $showSettings) {
            NavigationStack {
                SettingsView()
                    .environment(settingsVM)
            }
            .preferredColorScheme(.dark)
            .task { await settingsVM.load() }
        }
    }

    private func convBinding() -> ConversationsViewModel {
        if let conversationsVM { return conversationsVM }
        let vm = ConversationsViewModel(appState: appState)
        conversationsVM = vm
        return vm
    }

    private func chatBinding(conversations: ConversationsViewModel) -> ChatViewModel {
        if let chatVM { return chatVM }
        let vm = ChatViewModel(appState: appState, conversations: conversations)
        chatVM = vm
        return vm
    }

    private func settingsBinding() -> SettingsViewModel {
        if let settingsVM { return settingsVM }
        let vm = SettingsViewModel(appState: appState)
        settingsVM = vm
        return vm
    }
}
