import SwiftUI

/// ChatGPT-style conversation with a Destiny treatment: avatar rows, suggestion
/// cards, a thinking indicator, and a pill composer.
struct VoiceChatView: View {
    @EnvironmentObject private var session: GhostSession
    @EnvironmentObject private var auth: AuthStore
    @StateObject private var voice = VoiceRecognizer()
    @State private var draft: String = ""
    @FocusState private var composerFocused: Bool

    private static let bottomAnchor = "ghost.bottom"

    private let suggestions = [
        "Tell me about the Last City",
        "Equip Sunshot on my Hunter",
        "What's in my Postmaster?",
        "Who is the Traveler?"
    ]

    var body: some View {
        VStack(spacing: 0) {
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 18) {
                        if session.messages.isEmpty && !session.isAwaiting {
                            emptyState
                        }
                        ForEach(session.messages) { message in
                            MessageRow(message: message)
                        }
                        if session.isAwaiting {
                            thinkingRow
                        }
                        Color.clear.frame(height: 1).id(Self.bottomAnchor)
                    }
                    .padding(.horizontal, 16)
                    .padding(.top, 16)
                }
                .scrollDismissesKeyboard(.interactively)
                .onChange(of: session.messages.count) { _, _ in scrollToBottom(proxy) }
                .onChange(of: session.isAwaiting) { _, _ in scrollToBottom(proxy) }
            }
            composer
        }
    }

    // MARK: - Empty state

    private var emptyState: some View {
        VStack(spacing: 18) {
            GhostMark(size: 68, glow: true)
                .padding(.top, 36)
            VStack(spacing: 6) {
                Text("Eyes up, Guardian.")
                    .font(.title3.weight(.semibold))
                    .foregroundStyle(GhostTheme.textPrimary)
                Text("Ask me to manage your gear or dig into Destiny lore.")
                    .font(.subheadline)
                    .foregroundStyle(GhostTheme.textSecondary)
                    .multilineTextAlignment(.center)
            }

            LazyVGrid(columns: [GridItem(.flexible(), spacing: 10), GridItem(.flexible(), spacing: 10)], spacing: 10) {
                ForEach(suggestions, id: \.self) { suggestion in
                    SuggestionCard(text: suggestion) { send(suggestion) }
                }
            }
            .padding(.top, 8)
        }
        .frame(maxWidth: .infinity)
        .padding(.bottom, 24)
    }

    private var thinkingRow: some View {
        HStack(alignment: .top, spacing: 12) {
            GhostMark(size: 28, glow: true)
            TypingDots()
                .padding(.top, 8)
            Spacer(minLength: 0)
        }
    }

    // MARK: - Composer

    private var composer: some View {
        VStack(spacing: 0) {
            Rectangle().fill(GhostTheme.accentHairline).frame(height: 1)
            HStack(spacing: 10) {
                Button { Task { await toggleMic() } } label: {
                    Image(systemName: voice.isRecording ? "mic.fill" : "mic")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundStyle(voice.isRecording ? GhostTheme.solar : GhostTheme.accent)
                        .frame(width: 34, height: 34)
                }
                .accessibilityLabel(voice.isRecording ? "Stop recording" : "Speak")

                TextField("Speak to your Ghost…", text: $draft, axis: .vertical)
                    .textFieldStyle(.plain)
                    .foregroundStyle(GhostTheme.textPrimary)
                    .tint(GhostTheme.accent)
                    .lineLimit(1...5)
                    .focused($composerFocused)
                    .onSubmit(sendDraft)

                Button(action: sendDraft) {
                    Image(systemName: "arrow.up")
                        .font(.system(size: 16, weight: .bold))
                        .foregroundStyle(GhostTheme.background)
                        .frame(width: 32, height: 32)
                        .background(canSend ? GhostTheme.accent : GhostTheme.surfaceElevated, in: Circle())
                }
                .disabled(!canSend)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(
                RoundedRectangle(cornerRadius: 26, style: .continuous)
                    .fill(GhostTheme.surface)
                    .overlay(
                        RoundedRectangle(cornerRadius: 26, style: .continuous)
                            .stroke(GhostTheme.accentHairline, lineWidth: 1)
                    )
            )
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
        }
        .background(GhostTheme.background)
    }

    private var canSend: Bool { !draft.trimmingCharacters(in: .whitespaces).isEmpty }

    // MARK: - Actions

    private func sendDraft() {
        let text = draft
        draft = ""
        send(text)
    }

    private func send(_ text: String) {
        let trimmed = text.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty else { return }
        if session.connection != .connected {
            session.connectVoice(membershipID: auth.membershipID, characterID: auth.selectedCharacterID)
        }
        session.send(trimmed)
    }

    private func toggleMic() async {
        if voice.isRecording {
            voice.stop()
            if !voice.transcript.isEmpty { draft = voice.transcript }
            return
        }
        guard await voice.requestPermissions() else { return }
        voice.start()
    }

    private func scrollToBottom(_ proxy: ScrollViewProxy) {
        withAnimation(.easeOut(duration: 0.25)) {
            proxy.scrollTo(Self.bottomAnchor, anchor: .bottom)
        }
    }
}

// MARK: - Rows

private struct MessageRow: View {
    let message: ChatMessage

    var body: some View {
        switch message.role {
        case .guardian:
            HStack {
                Spacer(minLength: 48)
                Text(message.text)
                    .foregroundStyle(GhostTheme.textPrimary)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(
                        RoundedRectangle(cornerRadius: 18, style: .continuous)
                            .fill(GhostTheme.surfaceElevated)
                            .overlay(
                                RoundedRectangle(cornerRadius: 18, style: .continuous)
                                    .stroke(GhostTheme.accentHairline, lineWidth: 1)
                            )
                    )
            }
        case .ghost:
            HStack(alignment: .top, spacing: 12) {
                GhostMark(size: 28)
                VStack(alignment: .leading, spacing: 4) {
                    HStack(spacing: 8) {
                        Text("GHOST")
                            .font(GhostTheme.hud(11))
                            .foregroundStyle(GhostTheme.accent)
                        if let intent = message.intent {
                            Text(intent.uppercased())
                                .font(GhostTheme.hud(9))
                                .foregroundStyle(GhostTheme.intentColor(intent))
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(
                                    Capsule().stroke(GhostTheme.intentColor(intent).opacity(0.5), lineWidth: 1)
                                )
                        }
                    }
                    Text(message.text)
                        .foregroundStyle(GhostTheme.textPrimary)
                        .fixedSize(horizontal: false, vertical: true)
                }
                Spacer(minLength: 0)
            }
        }
    }
}

private struct SuggestionCard: View {
    let text: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack {
                Text(text)
                    .font(.footnote)
                    .foregroundStyle(GhostTheme.textPrimary)
                    .multilineTextAlignment(.leading)
                Spacer(minLength: 0)
            }
            .padding(12)
            .frame(maxWidth: .infinity, minHeight: 64, alignment: .topLeading)
            .background(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .fill(GhostTheme.surface)
                    .overlay(
                        RoundedRectangle(cornerRadius: 14, style: .continuous)
                            .stroke(GhostTheme.hairline, lineWidth: 1)
                    )
            )
        }
        .buttonStyle(.plain)
    }
}
