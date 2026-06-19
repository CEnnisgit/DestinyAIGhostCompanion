import SwiftUI

/// A stylized Ghost shell: nested diamonds around a glowing core (a HUD reticle).
struct GhostMark: View {
    var size: CGFloat = 28
    var glow: Bool = false

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: size * 0.12, style: .continuous)
                .stroke(GhostTheme.accent, lineWidth: max(1.2, size * 0.05))
                .frame(width: size * 0.72, height: size * 0.72)
                .rotationEffect(.degrees(45))

            RoundedRectangle(cornerRadius: size * 0.1, style: .continuous)
                .stroke(GhostTheme.accent.opacity(0.45), lineWidth: max(1, size * 0.03))
                .frame(width: size * 0.42, height: size * 0.42)
                .rotationEffect(.degrees(45))

            Circle()
                .fill(GhostTheme.accentBright)
                .frame(width: size * 0.16, height: size * 0.16)
                .shadow(color: GhostTheme.accent.opacity(glow ? 0.9 : 0.5),
                        radius: glow ? size * 0.45 : size * 0.18)
        }
        .frame(width: size, height: size)
    }
}

/// Three pulsing dots shown while the Ghost is "thinking".
struct TypingDots: View {
    @State private var phase = 0.0

    var body: some View {
        HStack(spacing: 5) {
            ForEach(0..<3) { index in
                Circle()
                    .fill(GhostTheme.accent)
                    .frame(width: 6, height: 6)
                    .opacity(opacity(for: index))
            }
        }
        .onAppear {
            withAnimation(.easeInOut(duration: 0.9).repeatForever(autoreverses: true)) {
                phase = 1
            }
        }
    }

    private func opacity(for index: Int) -> Double {
        let base = 0.35 + 0.65 * abs(sin((phase * .pi) + Double(index) * 0.6))
        return min(1, base)
    }
}
