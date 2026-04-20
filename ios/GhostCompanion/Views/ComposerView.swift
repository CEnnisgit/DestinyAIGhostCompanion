import SwiftUI

struct ComposerView: View {
    @State private var text: String = ""
    @FocusState private var focused: Bool

    let isStreaming: Bool
    let onSend: (String) -> Void
    let onStop: () -> Void
    let onMic: () -> Void

    var body: some View {
        HStack(alignment: .bottom, spacing: 8) {
            Button {
                focused = false
                onMic()
            } label: {
                Image(systemName: "mic.fill")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundStyle(Theme.accent)
                    .frame(width: 40, height: 40)
                    .background(Theme.backgroundElevated, in: Circle())
            }
            .accessibilityLabel("Voice input")

            TextField("Ask the Ghost…", text: $text, axis: .vertical)
                .font(Typography.composer)
                .focused($focused)
                .lineLimit(1...5)
                .padding(.horizontal, 14)
                .padding(.vertical, 10)
                .background(Theme.backgroundElevated, in: RoundedRectangle(cornerRadius: Theme.composerCornerRadius))
                .foregroundStyle(Theme.textPrimary)
                .submitLabel(.send)

            Button(action: primaryAction) {
                Image(systemName: isStreaming ? "stop.fill" : "arrow.up")
                    .font(.system(size: 18, weight: .bold))
                    .foregroundStyle(Color.black)
                    .frame(width: 40, height: 40)
                    .background(isStreaming ? Theme.danger : Theme.accent, in: Circle())
            }
            .disabled(!isStreaming && text.trimmingCharacters(in: .whitespaces).isEmpty)
            .accessibilityLabel(isStreaming ? "Stop" : "Send")
        }
    }

    private func primaryAction() {
        if isStreaming {
            focused = false
            onStop()
            return
        }
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        onSend(trimmed)
        text = ""
        focused = false
    }
}
