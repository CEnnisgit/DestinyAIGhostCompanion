import SwiftUI

struct ChatMessageRow: View {
    let message: Message
    let showSpacerAbove: Bool
    let onRegenerate: () -> Void

    var body: some View {
        VStack(alignment: message.isUser ? .trailing : .leading, spacing: 4) {
            if showSpacerAbove {
                Color.clear.frame(height: 8)
            }
            HStack {
                if message.isUser { Spacer(minLength: 48) }
                bubble
                if !message.isUser { Spacer(minLength: 48) }
            }
        }
        .contextMenu {
            if message.isAssistant {
                Button {
                    UIPasteboard.general.string = message.content
                } label: { Label("Copy", systemImage: "doc.on.doc") }
                Button {
                    onRegenerate()
                } label: { Label("Regenerate", systemImage: "arrow.clockwise") }
            } else {
                Button {
                    UIPasteboard.general.string = message.content
                } label: { Label("Copy", systemImage: "doc.on.doc") }
            }
        }
    }

    private var bubble: some View {
        let isUser = message.isUser
        return bubbleContent
            .font(Typography.body)
            .foregroundStyle(isUser ? Color.black : Theme.textPrimary)
            .padding(.horizontal, 14)
            .padding(.vertical, 10)
            .background(
                RoundedRectangle(cornerRadius: Theme.bubbleCornerRadius, style: .continuous)
                    .fill(isUser ? Theme.bubbleUser : Theme.bubbleAssistant)
            )
            .overlay(
                RoundedRectangle(cornerRadius: Theme.bubbleCornerRadius, style: .continuous)
                    .strokeBorder(Theme.textMuted.opacity(isUser ? 0 : 0.15), lineWidth: isUser ? 0 : 1)
            )
            .frame(maxWidth: UIScreen.main.bounds.width * Theme.maxBubbleWidth,
                   alignment: isUser ? .trailing : .leading)
    }

    @ViewBuilder
    private var bubbleContent: some View {
        if message.streaming {
            TimelineView(.animation(minimumInterval: 0.5, paused: false)) { context in
                let showCursor = Int(context.date.timeIntervalSince1970 * 2) % 2 == 0
                renderText(streamingContent(showCursor: showCursor))
            }
        } else {
            renderText(message.content)
        }
    }

    /// Assistant replies are markdown-aware (bold/italic/links/inline code).
    /// User bubbles render as plain text since their input rarely contains
    /// markdown and the user shouldn't have their input reinterpreted.
    @ViewBuilder
    private func renderText(_ raw: String) -> some View {
        if message.isAssistant, let attributed = try? AttributedString(
            markdown: raw,
            options: AttributedString.MarkdownParsingOptions(
                interpretedSyntax: .inlineOnlyPreservingWhitespace
            )
        ) {
            Text(attributed)
        } else {
            Text(raw)
        }
    }

    private func streamingContent(showCursor: Bool) -> String {
        let caret = showCursor ? "\u{258D}" : " "
        if message.content.isEmpty { return caret }
        return message.content + caret
    }
}
