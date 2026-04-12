import SwiftUI

struct ChatView: View {
    @EnvironmentObject private var authStore: AuthStore
    @EnvironmentObject private var chatStore: ChatStore
    @State private var draft = ""

    var body: some View {
        NavigationStack {
            Group {
                if authStore.isAuthenticated {
                    VStack(spacing: 0) {
                        if let errorMessage = chatStore.errorMessage {
                            Text(errorMessage)
                                .font(.footnote)
                                .foregroundStyle(.red)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(.horizontal)
                                .padding(.top, 8)
                        }

                        ScrollViewReader { proxy in
                            List(chatStore.messages) { message in
                                VStack(alignment: .leading, spacing: 6) {
                                    Text(message.role == "assistant" ? "Ghost" : "You")
                                        .font(.caption.weight(.semibold))
                                        .foregroundStyle(.secondary)
                                    Text(message.content.isEmpty && message.role == "assistant" ? "Thinking..." : message.content)
                                }
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .listRowSeparator(.hidden)
                                .id(message.id)
                            }
                            .listStyle(.plain)
                            .onChange(of: chatStore.messages) { _, messages in
                                if let lastID = messages.last?.id {
                                    withAnimation {
                                        proxy.scrollTo(lastID, anchor: .bottom)
                                    }
                                }
                            }
                        }

                        HStack(alignment: .bottom, spacing: 12) {
                            TextField("Ask Ghost", text: $draft, axis: .vertical)
                                .textFieldStyle(.roundedBorder)
                                .lineLimit(1 ... 5)

                            Button(chatStore.isStreaming ? "..." : "Send") {
                                let outgoing = draft
                                draft = ""
                                Task {
                                    await chatStore.send(outgoing, using: authStore)
                                }
                            }
                            .disabled(chatStore.isStreaming || draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                            .buttonStyle(.borderedProminent)
                        }
                        .padding()
                    }
                } else {
                    SignInView()
                }
            }
            .navigationTitle("Chat")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Menu {
                        Button("New Chat") {
                            Task {
                                await chatStore.createConversation(using: authStore)
                            }
                        }
                        if !chatStore.conversations.isEmpty {
                            Divider()
                        }
                        ForEach(chatStore.conversations) { conversation in
                            Button(conversation.name) {
                                Task {
                                    await chatStore.openConversation(conversation.id, using: authStore)
                                }
                            }
                        }
                    } label: {
                        Label("Chats", systemImage: "sidebar.left")
                    }
                }
            }
        }
    }
}
