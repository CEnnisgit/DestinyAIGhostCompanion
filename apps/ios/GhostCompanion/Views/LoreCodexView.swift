import SwiftUI

/// Browse + search the Destiny lore corpus.
struct LoreCodexView: View {
    @EnvironmentObject private var session: GhostSession
    @Environment(\.dismiss) private var dismiss

    @State private var categories: [LoreCategory] = []
    @State private var activeCategory: String?
    @State private var query: String = ""
    @State private var entries: [LoreEntry] = []
    @State private var loading = false

    private var backend: GhostBackend? { GhostBackend(baseURLString: session.backendURLString) }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                categoryBar
                Divider().overlay(GhostTheme.hairline)
                entryList
            }
            .background(GhostTheme.backgroundGradient.ignoresSafeArea())
            .navigationTitle("Lore Codex")
            .navigationBarTitleDisplayMode(.inline)
            .searchable(text: $query, prompt: "Search the Codex")
            .onChange(of: query) { _, value in runSearch(value) }
            .toolbar {
                ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } }
            }
            .tint(GhostTheme.accent)
            .preferredColorScheme(.dark)
            .task { await loadCategories() }
        }
    }

    private var categoryBar: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(categories) { category in
                    Button { selectCategory(category.category) } label: {
                        HStack(spacing: 6) {
                            Text(category.category)
                            Text("\(category.count)")
                                .font(GhostTheme.hud(10))
                                .foregroundStyle(GhostTheme.accent)
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .overlay(
                            Capsule().stroke(
                                category.category == activeCategory ? GhostTheme.accent : GhostTheme.hairline,
                                lineWidth: 1
                            )
                        )
                        .foregroundStyle(category.category == activeCategory ? GhostTheme.textPrimary : GhostTheme.textSecondary)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal)
            .padding(.vertical, 8)
        }
    }

    private var entryList: some View {
        List(entries) { entry in
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 8) {
                    Text(entry.name).font(.headline).foregroundStyle(GhostTheme.accentBright)
                    if let category = entry.category {
                        Text(category.uppercased())
                            .font(GhostTheme.hud(9))
                            .foregroundStyle(GhostTheme.textSecondary)
                    }
                }
                Text(entry.description).font(.subheadline).foregroundStyle(GhostTheme.textPrimary)
            }
            .padding(.vertical, 3)
            .listRowBackground(GhostTheme.surface)
        }
        .scrollContentBackground(.hidden)
        .overlay { if loading { ProgressView().tint(GhostTheme.accent) } }
    }

    private func loadCategories() async {
        guard let backend else { return }
        if let cats = try? await backend.loreCategories() {
            categories = cats
            if activeCategory == nil, let first = cats.first { selectCategory(first.category) }
        }
    }

    private func selectCategory(_ category: String) {
        activeCategory = category
        if !query.isEmpty { query = "" }
        Task { await browse(category) }
    }

    private func browse(_ category: String) async {
        guard let backend else { return }
        loading = true
        defer { loading = false }
        entries = (try? await backend.loreBrowse(category: category)) ?? []
    }

    private func runSearch(_ q: String) {
        let trimmed = q.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty else {
            if let active = activeCategory { Task { await browse(active) } }
            return
        }
        activeCategory = nil
        Task {
            guard let backend else { return }
            loading = true
            defer { loading = false }
            entries = (try? await backend.loreSearch(query: trimmed)) ?? []
        }
    }
}
