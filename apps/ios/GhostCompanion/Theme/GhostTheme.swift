import SwiftUI

/// Destiny-flavored design tokens: deep-space dark with an electric-blue Ghost
/// accent, elemental highlights, and a HUD monospace for labels.
enum GhostTheme {
    // Surfaces
    static let background = Color(red: 0.027, green: 0.043, blue: 0.078)
    static let surface = Color(red: 0.075, green: 0.098, blue: 0.149)
    static let surfaceElevated = Color(red: 0.110, green: 0.141, blue: 0.204)

    // Brand — electric azure (the Ghost's light)
    static let accent = Color(red: 0.275, green: 0.600, blue: 0.980)
    static let accentBright = Color(red: 0.560, green: 0.800, blue: 1.000)

    // Text
    static let textPrimary = Color(red: 0.918, green: 0.945, blue: 0.980)   // Traveler white
    static let textSecondary = Color(red: 0.541, green: 0.604, blue: 0.690)

    // Elemental accents
    static let arc = Color(red: 0.475, green: 0.886, blue: 1.000)           // Arc cyan
    static let solar = Color(red: 1.000, green: 0.478, blue: 0.235)         // Solar orange
    static let void = Color(red: 0.690, green: 0.545, blue: 1.000)          // Void purple

    static let hairline = Color.white.opacity(0.08)
    static let accentHairline = accent.opacity(0.30)

    /// Vertical space gradient for the app background.
    static var backgroundGradient: LinearGradient {
        LinearGradient(
            colors: [
                Color(red: 0.043, green: 0.075, blue: 0.133),
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
