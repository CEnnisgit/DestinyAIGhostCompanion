import Foundation

struct AuthStatusResponse: Codable {
    let authenticated: Bool
    let bungieLinked: Bool
    let apiKeyOk: Bool
    let apiKeyMasked: String
}

struct AppConfigResponse: Codable {
    let auth: AuthStatusResponse
    let models: ModelCatalogResponse
    let personas: [PersonaOption]
    let voices: [VoiceOption]
    let voiceCapabilities: VoiceCapabilities
    let voiceCatalog: VoiceCatalog?
    let apiBase: String
    let mobileOauthPath: String?
}

struct ModelCatalogResponse: Codable {
    let ollama: [String]
    let providers: [String]
    let defaultProvider: String?
}

struct PersonaOption: Codable, Identifiable {
    let id: String
    let label: String
    let description: String?

    init(id: String, label: String, description: String? = nil) {
        self.id = id
        self.label = label
        self.description = description
    }

    init(from decoder: Decoder) throws {
        if let container = try? decoder.singleValueContainer(),
           let value = try? container.decode(String.self) {
            self.init(id: value, label: value)
            return
        }

        let container = try decoder.container(keyedBy: CodingKeys.self)
        let id = try container.decodeIfPresent(String.self, forKey: .id) ?? ""
        let label = try container.decodeIfPresent(String.self, forKey: .label) ?? id
        let description = try container.decodeIfPresent(String.self, forKey: .description)
        self.init(id: id, label: label, description: description)
    }

    private enum CodingKeys: String, CodingKey {
        case id
        case label
        case description
    }
}

struct VoiceOption: Codable, Identifiable {
    let id: String
    let label: String
    let provider: String?
    let mode: String?
    let personas: [String]

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.id = try container.decodeIfPresent(String.self, forKey: .key) ?? ""
        self.label = try container.decodeIfPresent(String.self, forKey: .name) ?? id
        self.provider = try container.decodeIfPresent(String.self, forKey: .provider)
        self.mode = try container.decodeIfPresent(String.self, forKey: .mode)
        self.personas = try container.decodeIfPresent([String].self, forKey: .personas) ?? []
    }

    private enum CodingKeys: String, CodingKey {
        case key
        case name
        case provider
        case mode
        case personas
    }
}

struct VoiceCapabilities: Codable {
    let mode: String?
    let continuous: Bool?
    let interruptible: Bool?
    let fallback: String?
    let stt: VoiceTransportCapabilities?
    let tts: VoiceTransportCapabilities?
}

struct VoiceTransportCapabilities: Codable {
    let browser: Bool?
    let serverUpload: Bool?
    let serverLive: Bool?
    let serverAudio: Bool?
}

struct VoiceCatalog: Codable {
    let examples: [String]
    let readIntents: [String]
    let actionIntents: [String]
    let confirmationRequiredFor: [String]
}

struct ConversationListResponse: Codable {
    let conversations: [ConversationSummary]
}

struct ConversationSummary: Codable, Identifiable {
    let id: String
    let name: String
    let provider: String?
    let createdAt: String?
    let updatedAt: String?
}

struct ConversationCreateRequest: Codable {
    let name: String
    let provider: String?
}

struct ConversationCreateResponse: Codable {
    let id: String
}

struct ConversationDetailResponse: Codable {
    let messages: [ConversationMessage]
}

struct ConversationMessage: Codable, Identifiable, Hashable {
    let id: String
    let role: String
    let content: String
    let createdAt: String?

    init(id: String, role: String, content: String, createdAt: String? = nil) {
        self.id = id
        self.role = role
        self.content = content
        self.createdAt = createdAt
    }
}

struct InventoryResponse: Codable {
    let membershipId: String?
    let membershipType: Int?
    let activeCharacterId: String?
    let characters: [InventoryCharacter]
    let items: [InventoryItem]
    let sections: InventorySections
}

struct InventorySections: Codable {
    let equipped: [InventoryItem]
    let inventory: [InventoryItem]
    let vault: [InventoryItem]
    let postmaster: [InventoryItem]
}

struct InventoryCharacter: Codable, Identifiable, Hashable {
    let characterId: String
    let classType: Int?
    let className: String?
    let light: Int?
    let emblemPath: String?

    var id: String { characterId }
}

struct InventoryItem: Codable, Identifiable, Hashable {
    let instanceId: String
    let itemHash: Int?
    let name: String
    let icon: String?
    let bucket: String?
    let bucketHash: Int?
    let tier: String?
    let power: Int?
    let classType: Int?
    let source: String
    let characterId: String?
    let equipped: Bool?
    let transferable: Bool?
    let actions: [String]

    var id: String { instanceId }
}

struct ActionPreviewRequest: Codable {
    let action: String
    let itemInstanceId: String
    let targetCharacterId: String?
}

struct ActionPreviewResponse: Codable {
    let action: String
    let intent: String
    let candidate: InventoryItem
    let targetCharacterId: String?
    let targetCharacterName: String?
    let preview: String
    let confirmationToken: String
    let confirmationExpiresIn: Int?
}

struct ActionExecuteRequest: Codable {
    let confirmationToken: String
}

struct ActionExecuteResponse: Codable {
    let status: String
    let actionId: String
    let result: ActionExecutionResult
}

struct ActionExecutionResult: Codable {
    let ok: Bool?
    let message: String
}

struct VoiceTurnRequest: Codable {
    let text: String
    let sessionId: String?
}

struct VoiceTurnCandidate: Codable, Identifiable {
    let instanceId: String
    let name: String
    let source: String?
    let characterId: String?
    let characterName: String?
    let power: Int?
    let tier: String?
    let className: String?

    var id: String { instanceId }
}

struct VoiceTurnResponse: Codable {
    let sessionId: String?
    let transcriptText: String?
    let intent: String?
    let replyText: String
    let resolutionState: String?
    let confirmationRequired: Bool?
    let confirmationToken: String?
    let plannedSteps: [String]?
    let candidates: [VoiceTurnCandidate]?
}

struct VoiceSessionResponse: Codable {
    let sessionId: String?
    let requestedMode: String?
    let capabilities: VoiceCapabilities?
    let recommendedVoice: String?
    let status: String?
    let userId: Int?
}
