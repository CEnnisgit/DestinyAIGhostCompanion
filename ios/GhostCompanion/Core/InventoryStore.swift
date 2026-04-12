import Foundation

@MainActor
final class InventoryStore: ObservableObject {
    @Published var inventory: InventoryResponse?
    @Published var isLoading = false
    @Published var pendingItemID: String?
    @Published var actionMessage: String?
    @Published var errorMessage: String?
    @Published var selectedCharacterID: String?
    @Published var query = ""

    func refresh(using auth: AuthStore) async {
        isLoading = true
        defer { isLoading = false }
        do {
            let payload = try await auth.client().fetchInventory()
            inventory = payload
            selectedCharacterID = selectedCharacterID ?? payload.activeCharacterId ?? payload.characters.first?.characterId
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func perform(action: String, item: InventoryItem, using auth: AuthStore) async {
        pendingItemID = item.instanceId
        defer { pendingItemID = nil }
        do {
            let preview = try await auth.client().previewAction(
                action: action,
                itemInstanceID: item.instanceId,
                targetCharacterID: selectedCharacterID
            )
            let executed = try await auth.client().executeAction(confirmationToken: preview.confirmationToken)
            actionMessage = executed.result.message
            errorMessage = nil
            await refresh(using: auth)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func filtered(_ items: [InventoryItem]) -> [InventoryItem] {
        let trimmed = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return items }
        return items.filter { $0.name.localizedCaseInsensitiveContains(trimmed) }
    }
}
