import Foundation

/// Mirror of `GET /diagnostics/audio` in `server.py`. Device list is returned
/// as an opaque count — the server encodes per-device dicts with keys that
/// vary by host (sounddevice), so we only surface what's useful on iOS.
struct AudioDiagnostics: Codable {
    let report: [String]?
    let openaiKey: Bool?
    let sttProvider: String?
    let secureContextHint: Bool?
    let defaultInputDevice: Int?
    let devicesError: String?
    let deviceCount: Int?

    enum CodingKeys: String, CodingKey {
        case report
        case openaiKey = "openai_key"
        case sttProvider = "stt_provider"
        case secureContextHint = "secure_context_hint"
        case defaultInputDevice = "default_input_device"
        case devicesError = "devices_error"
        case devices
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        report = try c.decodeIfPresent([String].self, forKey: .report)
        openaiKey = try c.decodeIfPresent(Bool.self, forKey: .openaiKey)
        sttProvider = try c.decodeIfPresent(String.self, forKey: .sttProvider)
        secureContextHint = try c.decodeIfPresent(Bool.self, forKey: .secureContextHint)
        defaultInputDevice = try c.decodeIfPresent(Int.self, forKey: .defaultInputDevice)
        devicesError = try c.decodeIfPresent(String.self, forKey: .devicesError)
        if let devices = try? c.decodeIfPresent([AnyCodableValue].self, forKey: .devices) {
            deviceCount = devices.count
        } else {
            deviceCount = nil
        }
    }

    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encodeIfPresent(report, forKey: .report)
        try c.encodeIfPresent(openaiKey, forKey: .openaiKey)
        try c.encodeIfPresent(sttProvider, forKey: .sttProvider)
        try c.encodeIfPresent(secureContextHint, forKey: .secureContextHint)
        try c.encodeIfPresent(defaultInputDevice, forKey: .defaultInputDevice)
        try c.encodeIfPresent(devicesError, forKey: .devicesError)
    }
}

/// Minimal heterogeneous-dictionary decoder used only to count device entries.
struct AnyCodableValue: Codable {
    init(from decoder: Decoder) throws {
        let c = try decoder.singleValueContainer()
        if c.decodeNil() { return }
        if (try? c.decode(Bool.self)) != nil { return }
        if (try? c.decode(Double.self)) != nil { return }
        if (try? c.decode(String.self)) != nil { return }
        if (try? c.decode([String: AnyCodableValue].self)) != nil { return }
        if (try? c.decode([AnyCodableValue].self)) != nil { return }
    }
    func encode(to encoder: Encoder) throws {}
}
