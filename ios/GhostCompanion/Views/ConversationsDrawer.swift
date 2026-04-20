import SwiftUI

struct ConversationsDrawer: View {
    @Environment(ConversationsViewModel.self) private var vm

    let width: CGFloat
    let onClose: () -> Void
    let onOpenSettings: () -> Void
    let onOpenConversation: (String) -> Void
    let onNewChat: () -> Void

    @State private var renamingId: String?
    @State private var renameText: String = ""

    var body: some View {
        @Bindable var vm = vm
        VStack(alignment: .leading, spacing: 0) {
            header
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass").foregroundStyle(Theme.textMuted)
                TextField("Search", text: $vm.search)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .foregroundStyle(Theme.textPrimary)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
            .background(Theme.background, in: RoundedRectangle(cornerRadius: 12))
            .padding(.horizontal, 16)
            .padding(.bottom, 12)

            Divider().background(Theme.textMuted.opacity(0.2))

            if vm.filtered.isEmpty {
                ScrollView {
                    Text("No saved chats yet.")
                        .font(Typography.meta)
                        .foregroundStyle(Theme.textMuted)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 16)
                }
                .refreshable { await vm.refresh() }
            } else {
                List {
                    ForEach(vm.filtered) { c in
                        DrawerRow(
                            conversation: c,
                            isActive: vm.activeId == c.id,
                            onOpen: { onOpenConversation(c.id) },
                            onRename: {
                                renamingId = c.id
                                renameText = c.name
                            },
                            onDelete: {
                                Haptics.warning()
                                Task { await vm.delete(c.id) }
                            }
                        )
                        .listRowBackground(Color.clear)
                        .listRowInsets(EdgeInsets())
                        .listRowSeparator(.hidden)
                        .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                            Button(role: .destructive) {
                                Haptics.warning()
                                Task { await vm.delete(c.id) }
                            } label: {
                                Label("Delete", systemImage: "trash")
                            }
                            Button {
                                renamingId = c.id
                                renameText = c.name
                            } label: {
                                Label("Rename", systemImage: "pencil")
                            }
                            .tint(Theme.accent)
                        }
                    }
                }
                .listStyle(.plain)
                .scrollContentBackground(.hidden)
                .background(Theme.backgroundElevated)
                .refreshable { await vm.refresh() }
            }

            footer
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .background(Theme.backgroundElevated.ignoresSafeArea())
        .alert("Rename chat", isPresented: Binding(
            get: { renamingId != nil },
            set: { if !$0 { renamingId = nil } }
        )) {
            TextField("Name", text: $renameText)
            Button("Save") {
                if let id = renamingId {
                    Task { await vm.rename(id, to: renameText) }
                }
                renamingId = nil
            }
            Button("Cancel", role: .cancel) { renamingId = nil }
        }
    }

    private var header: some View {
        HStack {
            Button(action: onNewChat) {
                HStack(spacing: 8) {
                    Image(systemName: "plus")
                    Text("New Chat").font(Typography.row)
                }
                .foregroundStyle(Color.black)
                .padding(.horizontal, 14)
                .padding(.vertical, 10)
                .background(Theme.accent, in: Capsule())
            }
            Spacer()
            Button(action: onClose) {
                Image(systemName: "xmark")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundStyle(Theme.textPrimary)
                    .frame(width: 34, height: 34)
                    .background(Theme.background, in: Circle())
            }
        }
        .padding(.horizontal, 16)
        .padding(.top, 18)
        .padding(.bottom, 12)
    }

    private var footer: some View {
        HStack(spacing: 10) {
            Button(action: onOpenSettings) {
                HStack(spacing: 10) {
                    Image(systemName: "gearshape.fill")
                        .foregroundStyle(Theme.textPrimary)
                    Text("Settings").font(Typography.row).foregroundStyle(Theme.textPrimary)
                    Spacer()
                    Image(systemName: "chevron.right")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundStyle(Theme.textMuted)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 12)
                .background(Theme.background, in: RoundedRectangle(cornerRadius: 12))
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 16)
    }
}
