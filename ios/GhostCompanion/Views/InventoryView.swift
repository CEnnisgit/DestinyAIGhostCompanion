import SwiftUI

struct InventoryView: View {
    @EnvironmentObject private var authStore: AuthStore
    @EnvironmentObject private var inventoryStore: InventoryStore

    var body: some View {
        NavigationStack {
            Group {
                if authStore.isAuthenticated {
                    content
                } else {
                    SignInView()
                }
            }
            .navigationTitle("Inventory")
            .task {
                guard authStore.isAuthenticated else { return }
                if inventoryStore.inventory == nil {
                    await inventoryStore.refresh(using: authStore)
                }
            }
            .refreshable {
                await inventoryStore.refresh(using: authStore)
            }
        }
    }

    private var content: some View {
        VStack(spacing: 12) {
            if let actionMessage = inventoryStore.actionMessage {
                Text(actionMessage)
                    .font(.footnote)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal)
            }

            if let errorMessage = inventoryStore.errorMessage {
                Text(errorMessage)
                    .font(.footnote)
                    .foregroundStyle(.red)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal)
            }

            if let inventory = inventoryStore.inventory {
                VStack(spacing: 12) {
                    TextField("Search gear", text: $inventoryStore.query)
                        .textFieldStyle(.roundedBorder)
                        .padding(.horizontal)

                    if !inventory.characters.isEmpty {
                        Picker("Character", selection: Binding(
                            get: { inventoryStore.selectedCharacterID ?? inventory.activeCharacterId ?? inventory.characters.first?.characterId ?? "" },
                            set: { inventoryStore.selectedCharacterID = $0 }
                        )) {
                            ForEach(inventory.characters) { character in
                                Text(character.className ?? character.characterId).tag(character.characterId)
                            }
                        }
                        .pickerStyle(.segmented)
                        .padding(.horizontal)
                    }

                    List {
                        inventorySection(title: "Equipped", items: inventory.sections.equipped)
                        inventorySection(title: "Inventory", items: inventory.sections.inventory)
                        inventorySection(title: "Vault", items: inventory.sections.vault)
                        inventorySection(title: "Postmaster", items: inventory.sections.postmaster)
                    }
                    .listStyle(.insetGrouped)
                }
            } else if inventoryStore.isLoading {
                Spacer()
                ProgressView("Loading inventory")
                Spacer()
            } else {
                Spacer()
                Text("No inventory loaded yet.")
                    .foregroundStyle(.secondary)
                Spacer()
            }
        }
    }

    private func inventorySection(title: String, items: [InventoryItem]) -> some View {
        let filtered = inventoryStore.filtered(items)
        return Section(title) {
            if filtered.isEmpty {
                Text("No items here.")
                    .foregroundStyle(.secondary)
            } else {
                ForEach(filtered) { item in
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(item.name)
                                    .font(.headline)
                                Text([item.bucket, item.tier, item.power.map { "Power \($0)" }].compactMap { $0 }.joined(separator: " • "))
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            Spacer()
                            if inventoryStore.pendingItemID == item.instanceId {
                                ProgressView()
                            }
                        }

                        if !item.actions.isEmpty {
                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack {
                                    ForEach(item.actions, id: \.self) { action in
                                        Button(label(for: action)) {
                                            Task {
                                                await inventoryStore.perform(action: action, item: item, using: authStore)
                                            }
                                        }
                                        .buttonStyle(.bordered)
                                        .disabled(inventoryStore.pendingItemID != nil)
                                    }
                                }
                            }
                        }
                    }
                    .padding(.vertical, 4)
                }
            }
        }
    }

    private func label(for action: String) -> String {
        switch action {
        case "equip":
            return "Equip"
        case "vault":
            return "Vault"
        case "pull_from_vault":
            return "Pull"
        case "pull_from_postmaster":
            return "Claim"
        case "move_to_character":
            return "Move"
        default:
            return action.replacingOccurrences(of: "_", with: " ").capitalized
        }
    }
}
