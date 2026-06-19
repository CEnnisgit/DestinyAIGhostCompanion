import SwiftUI

/// The conversation transcript + input bar.
struct VoiceChatView: View {
    @EnvironmentObject private var session: GhostSession
    @State private var draft: String = ""

    var body: some View {
        VStack(spacing: 0) {
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 10) {
                        if session.messages.isEmpty {
                            emptyState
                        }
                        ForEach(session.messages) { message in
                            MessageBubble(message: message).id(message.id)
                        }
                    }
                    .padding()
                }
                .onChange(of: session.messages.count) { _, _ in
                    if let last = session.messages.last {
                        withAnimation { proxy.scrollTo(last.id, anchor: .bottom) }
                    }
                }
            }
            inputBar
        }
    }

    private var emptyState: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Eyes up, Guardian.")
                .font(.headline)
                .foregroundStyle(GhostTheme.accent)
            Text("Ask me to equip gear or about Destiny lore.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.vertical, 24)
    }

    private var inputBar: some View {
        HStack(spacing: 10) {
            TextField("Speak to your Ghost…", text: $draft, axis: .vertical)
                .textFieldStyle(.roundedBorder)
                .lineLimit(1...4)
                .onSubmit(sendDraft)

            Button(action: sendDraft) {
                Image(systemName: "arrow.up.circle.fill")
                    .font(.title2)
            }
            .disabled(draft.trimmingCharacters(in: .whitespaces).isEmpty)
        }
        .padding()
        .background(.ultraThinMaterial)
    }

    private func sendDraft() {
        let text = draft
        draft = ""
        if session.connection != .connected { session.connectVoice() }
        session.send(text)
    }
}

private struct MessageBubble: View {
    let message: ChatMessage

    var body: some View {
        HStack {
            if message.role == .guardian { Spacer(minLength: 40) }
            VStack(alignment: .leading, spacing: 4) {
                Text(message.text)
                if let intent = message.intent {
                    Text(intent.uppercased())
                        .font(.caption2.weight(.semibold))
                        .foregroundStyle(GhostTheme.accent)
                }
            }
            .padding(10)
            .background(message.role == .guardian ? GhostTheme.guardianBubble : GhostTheme.ghostBubble)
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
            .foregroundStyle(message.role == .guardian ? Color.primary : Color.white)
            if message.role == .ghost { Spacer(minLength: 40) }
        }
    }
}
