import SwiftUI

struct ChatView: View {
    @Environment(AppState.self) private var appState
    @Environment(ChatViewModel.self) private var chat
    @Environment(ConversationsViewModel.self) private var conversations

    @Binding var drawerOpen: Bool
    @Binding var showSettings: Bool
    @State private var showVoiceSheet: Bool = false

    var body: some View {
        VStack(spacing: 0) {
            header
            if chat.isEmpty {
                EmptyHeroView(onSend: { chat.send($0) }, onMic: { showVoiceSheet = true })
            } else {
                messageList
                ComposerView(
                    isStreaming: chat.isStreaming,
                    onSend: { chat.send($0) },
                    onStop: { chat.stop() },
                    onMic: { showVoiceSheet = true }
                )
                .padding(.horizontal, 12)
                .padding(.bottom, 8)
            }
            if let error = chat.errorMessage {
                ErrorBanner(message: error) { chat.errorMessage = nil }
            }
        }
        .sheet(isPresented: $showVoiceSheet) {
            VoiceInputSheet { text in
                showVoiceSheet = false
                chat.send(text)
            }
            .preferredColorScheme(.dark)
        }
    }

    private var header: some View {
        HStack(spacing: 12) {
            HamburgerButton {
                withAnimation(.spring(response: 0.3)) { drawerOpen.toggle() }
            }
            Spacer()
            Button {
                showSettings = true
            } label: {
                HStack(spacing: 6) {
                    Text(Persona(id: appState.settings.persona).displayName)
                        .font(Typography.row)
                        .foregroundStyle(Theme.textPrimary)
                    Image(systemName: "chevron.down")
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundStyle(Theme.textMuted)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(Theme.backgroundElevated, in: Capsule())
            }
            Spacer()
            // Symmetry spacer matching hamburger width so the persona pill stays visually centred.
            Color.clear.frame(width: 40, height: 40)
        }
        .padding(.horizontal, 12)
        .padding(.top, 8)
        .padding(.bottom, 6)
    }

    private var messageList: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(spacing: 6) {
                    ForEach(Array(chat.messages.enumerated()), id: \.element.id) { idx, msg in
                        ChatMessageRow(
                            message: msg,
                            showSpacerAbove: idx > 0 && chat.messages[idx - 1].role != msg.role,
                            onRegenerate: { chat.regenerate(from: msg) }
                        )
                        .id(msg.id)
                    }
                }
                .padding(.horizontal, 12)
                .padding(.top, 12)
                .padding(.bottom, 12)
            }
            .scrollDismissesKeyboard(.interactively)
            .contentShape(Rectangle())
            .onTapGesture { KeyboardDismiss.resign() }
            .onChange(of: chat.messages.last?.id) { _, newValue in
                if let newValue { withAnimation { proxy.scrollTo(newValue, anchor: .bottom) } }
            }
            .onChange(of: chat.messages.last?.content) { _, _ in
                if let id = chat.messages.last?.id { proxy.scrollTo(id, anchor: .bottom) }
            }
        }
    }
}
