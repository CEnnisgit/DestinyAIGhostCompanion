import SwiftUI

struct DrawerRow: View {
    let conversation: Conversation
    let isActive: Bool
    let onOpen: () -> Void
    let onRename: () -> Void
    let onDelete: () -> Void

    var body: some View {
        Button(action: onOpen) {
            HStack(spacing: 10) {
                RoundedRectangle(cornerRadius: 2)
                    .fill(isActive ? Theme.accent : Color.clear)
                    .frame(width: 3)
                VStack(alignment: .leading, spacing: 4) {
                    Text(conversation.name)
                        .font(Typography.row)
                        .foregroundStyle(Theme.textPrimary)
                        .lineLimit(1)
                    if let provider = conversation.provider {
                        Text(provider)
                            .font(Typography.meta)
                            .foregroundStyle(Theme.textMuted)
                    }
                }
                Spacer()
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
            .background(isActive ? Theme.accent.opacity(0.12) : Color.clear)
        }
        .contextMenu {
            Button { onRename() } label: { Label("Rename", systemImage: "pencil") }
            Button(role: .destructive) { onDelete() } label: { Label("Delete", systemImage: "trash") }
        }
    }
}
