import Foundation

/// One played activity instance from the backend `/activity/summary`.
struct ActivityRecord: Identifiable, Decodable, Equatable {
    let name: String
    let mode: String
    let period: String
    let completed: Bool
    let fireteam: [String]
    let game: String

    var id: String { period + name }

    var isDestiny1: Bool { game == "Destiny1" }

    /// "2026-06-18T20:00:00Z" → "Jun 18, 2026" (falls back to the date part).
    var displayDate: String {
        let iso = ISO8601DateFormatter()
        iso.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        let date = iso.date(from: period)
            ?? ISO8601DateFormatter().date(from: period)
        guard let date else { return String(period.prefix(10)) }
        let out = DateFormatter()
        out.dateFormat = "MMM d, yyyy"
        return out.string(from: date)
    }
}

/// The Guardian's recent activity, with a ready-to-display narrative.
struct ActivitySummary: Decodable, Equatable {
    let narrative: String
    let recent: [ActivityRecord]
}
