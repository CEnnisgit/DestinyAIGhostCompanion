import Foundation

struct ChatQuery {
    var message: String
    var provider: String?
    var model: String?
    var persona: String?
    var speak: Bool
    var voice: String?
    var sessionId: String?
}

enum Endpoints {
    static func path(_ p: String, base: URL) -> URL {
        base.appendingPathComponent(p.hasPrefix("/") ? String(p.dropFirst()) : p)
    }

    static func chatStream(base: URL, query: ChatQuery) -> URL? {
        var comps = URLComponents(url: path("chat/stream", base: base), resolvingAgainstBaseURL: false)
        var items: [URLQueryItem] = [URLQueryItem(name: "message", value: query.message)]
        if let p = query.provider, !p.isEmpty { items.append(.init(name: "provider", value: p)) }
        if let m = query.model, !m.isEmpty { items.append(.init(name: "model", value: m)) }
        if let per = query.persona, !per.isEmpty { items.append(.init(name: "persona", value: per)) }
        if query.speak { items.append(.init(name: "speak", value: "1")) }
        if let v = query.voice, !v.isEmpty { items.append(.init(name: "voice", value: v)) }
        if let s = query.sessionId, !s.isEmpty { items.append(.init(name: "session_id", value: s)) }
        comps?.queryItems = items
        return comps?.url
    }
}
