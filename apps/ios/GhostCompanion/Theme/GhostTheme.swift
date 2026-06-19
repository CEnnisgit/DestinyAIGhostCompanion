import SwiftUI

/// Destiny-flavored design tokens: deep-space dark, Ghost gold, elemental accents,
/// and a HUD monospace for labels.
enum GhostTheme {
    // Surfaces
    static let background = Color(red: 0.039, green: 0.055, blue: 0.078)
    static let surface = Color(red: 0.086, green: 0.106, blue: 0.141)
    static let surfaceElevated = Color(red: 0.122, green: 0.149, blue: 0.196)

    // Brand
    static let accent = Color(red: 0.957, green: 0.780, blue: 0.416)        // Ghost gold
    static let accentBright = Color(red: 1.000, green: 0.860, blue: 0.560)

    // Text
    static let textPrimary = Color(red: 0.937, green: 0.953, blue: 0.976)   // Traveler white
    static let textSecondary = Color(red: 0.600, green: 0.643, blue: 0.706)

    // Elemental accents
    static let arc = Color(red: 0.475, green: 0.886, blue: 1.000)           // Arc cyan
    static let solar = Color(red: 1.000, green: 0.478, blue: 0.235)         // Solar orange
    static let void = Color(red: 0.690, green: 0.545, blue: 1.000)          // Void purple

    static let hairline = Color.white.opacity(0.08)
    static let goldHairline = accent.opacity(0.25)

    /// Vertical space gradient for the app background.
    static var backgroundGradient: LinearGradient {
        LinearGradient(
            colors: [
                Color(red: 0.055, green: 0.078, blue: 0.118),
                background,
                Color.black
            ],
            startPoint: .top,
            endPoint: .bottom
        )
    }

    /// Maps a Ghost intent label to an elemental accent.
    static func intentColor(_ intent: String) -> Color {
        switch intent {
        case "lore": return arc
        case "error": return solar
        case "equip", "transfer", "pull_postmaster", "query_inventory": return accent
        default: return textSecondary
        }
    }

    /// HUD-style monospace for labels, intents, and status.
    static func hud(_ size: CGFloat = 11) -> Font {
        .system(size: size, weight: .semibold, design: .monospaced)
    }
}
