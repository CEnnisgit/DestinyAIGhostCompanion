import SwiftUI

/// History drawer: switch between, start, or delete saved conversations.
struct ConversationsView: View {
    @EnvironmentObject private var session: GhostSession
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            List {
                ForEach(session.conversations) { conversation in
                    Button {
                        session.selectConversation(conversation.id)
                        dismiss()
                    } label: {
                        row(conversation)
                    }
                    .listRowBackground(
                        conversation.id == session.selectedID ? GhostTheme.surfaceElevated : GhostTheme.surface
                    )
                }
                .onDelete { offsets in
                    offsets.map { session.conversations[$0].id }.forEach(session.deleteConversation)
                }
            }
            .scrollContentBackground(.hidden)
            .background(GhostTheme.backgroundGradient.ignoresSafeArea())
            .navigationTitle("Conversations")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Done") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button {
                        session.newConversation()
                        dismiss()
                    } label: {
                        Image(systemName: "square.and.pencil")
                    }
                    .accessibilityLabel("New conversation")
                }
            }
            .tint(GhostTheme.accent)
            .preferredColorScheme(.dark)
        }
    }

    private func row(_ conversation: Conversation) -> some View {
        HStack(spacing: 12) {
            GhostMark(size: 22)
            VStack(alignment: .leading, spacing: 2) {
                Text(conversation.title.isEmpty ? "New Conversation" : conversation.title)
                    .foregroundStyle(GhostTheme.textPrimary)
                    .lineLimit(1)
                Text(subtitle(conversation))
                    .font(.caption)
                    .foregroundStyle(GhostTheme.textSecondary)
                    .lineLimit(1)
            }
            Spacer(minLength: 0)
            if conversation.id == session.selectedID {
                Image(systemName: "checkmark")
                    .font(.footnote.weight(.bold))
                    .foregroundStyle(GhostTheme.accent)
            }
        }
        .padding(.vertical, 2)
    }

    private func subtitle(_ conversation: Conversation) -> String {
        if let last = conversation.messages.last { return last.text }
        return "Empty"
    }
}
