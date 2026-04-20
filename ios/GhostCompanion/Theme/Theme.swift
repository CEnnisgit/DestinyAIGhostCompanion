import SwiftUI

enum Theme {
    static let background = Color("Colors/Background")
    static let backgroundElevated = Color("Colors/BackgroundElevated")
    static let accent = Color("Colors/Accent")
    static let textPrimary = Color("Colors/TextPrimary")
    static let textMuted = Color("Colors/TextMuted")
    static let bubbleAssistant = Color("Colors/BubbleAssistant")
    static let bubbleUser = Color("Colors/BubbleUser")
    static let danger = Color("Colors/Danger")

    static let bubbleCornerRadius: CGFloat = 18
    static let composerCornerRadius: CGFloat = 22
    static let maxBubbleWidth: CGFloat = 0.78
}

struct ThemedBackground: ViewModifier {
    func body(content: Content) -> some View {
        content.background(Theme.background.ignoresSafeArea())
    }
}

extension View {
    func themedBackground() -> some View { modifier(ThemedBackground()) }
}
