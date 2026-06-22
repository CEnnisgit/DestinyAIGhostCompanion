import SwiftUI

/// A clean, symmetric, sphere-themed backdrop: concentric orbital rings with
/// planet-spheres on them, and a faint starfield. The center is kept clear so
/// the Ghost has room to breathe.
struct SacredBackground: View {
    var body: some View {
        Canvas { ctx, size in
            let accent = GhostTheme.accent
            let c = CGPoint(x: size.width / 2, y: size.height / 2)
            let base = Double(max(size.width, size.height))

            // Deterministic starfield.
            var seed: UInt64 = 1337
            func rand() -> Double {
                seed = seed &* 1_103_515_245 &+ 12_345
                return Double((seed >> 16) & 0x7fff) / Double(0x7fff)
            }
            let starColor = Color(red: 0.81, green: 0.89, blue: 1.0)
            for _ in 0..<70 {
                let x = rand() * Double(size.width)
                let y = rand() * Double(size.height)
                let r = rand() * 1.0 + 0.2
                let o = rand() * 0.45 + 0.1
                ctx.fill(Path(ellipseIn: CGRect(x: x - r, y: y - r, width: r * 2, height: r * 2)),
                         with: .color(starColor.opacity(o)))
            }

            // Concentric orbital rings centered.
            for frac in [0.18, 0.30, 0.42, 0.56, 0.72, 0.90] {
                let r = base * frac
                ctx.stroke(Path(ellipseIn: CGRect(x: c.x - r, y: c.y - r, width: r * 2, height: r * 2)),
                           with: .color(accent.opacity(0.15)), lineWidth: 0.7)
            }

            // Planet-spheres placed symmetrically on orbital rings.
            let orbits: [(frac: Double, count: Int, phase: Double, size: CGFloat)] = [
                (0.42, 6, 30, 12), (0.56, 6, 0, 9), (0.72, 6, 30, 7),
            ]
            for orbit in orbits {
                let radius = base * orbit.frac
                for i in 0..<orbit.count {
                    let a = (Double(i) * 360.0 / Double(orbit.count) + orbit.phase) * .pi / 180
                    let px = c.x + CGFloat(cos(a)) * radius
                    let py = c.y + CGFloat(sin(a)) * radius
                    let s = orbit.size
                    let rect = CGRect(x: px - s, y: py - s, width: s * 2, height: s * 2)
                    let grad = Gradient(stops: [
                        .init(color: Color(red: 0.65, green: 0.83, blue: 1.0).opacity(0.55), location: 0),
                        .init(color: Color(red: 0.13, green: 0.19, blue: 0.30).opacity(0.5), location: 0.55),
                        .init(color: Color(red: 0.03, green: 0.05, blue: 0.09).opacity(0.5), location: 1),
                    ])
                    ctx.fill(Path(ellipseIn: rect),
                             with: .radialGradient(grad,
                                                   center: CGPoint(x: px - s * 0.3, y: py - s * 0.35),
                                                   startRadius: 0, endRadius: s * 1.6))
                    ctx.stroke(Path(ellipseIn: rect), with: .color(accent.opacity(0.28)), lineWidth: 0.6)
                }
            }
        }
        .allowsHitTesting(false)
        .ignoresSafeArea()
    }
}

/// The Ghost framed by a clean rotating rosette and a soft, breathing radiant
/// bloom of the Traveler's light — circular forms, no clutter.
struct GhostHalo: View {
    @State private var angle: Double = 0
    @State private var pulse = false

    var body: some View {
        ZStack {
            Circle()
                .fill(RadialGradient(
                    colors: [GhostTheme.accentBright.opacity(0.38), GhostTheme.accent.opacity(0.14), .clear],
                    center: .center, startRadius: 0, endRadius: 115
                ))
                .frame(width: 230, height: 230)
                .scaleEffect(pulse ? 1.07 : 0.92)
                .opacity(pulse ? 0.95 : 0.5)

            ZStack {
                ForEach(0..<24, id: \.self) { i in
                    Capsule()
                        .fill(GhostTheme.accent.opacity(0.7))
                        .frame(width: 1.6, height: 12)
                        .offset(y: -80)
                        .rotationEffect(.degrees(Double(i) * 15))
                }
                Circle().stroke(GhostTheme.accent.opacity(0.5), lineWidth: 1).frame(width: 172, height: 172)
            }
            .rotationEffect(.degrees(angle))

            Circle()
                .stroke(GhostTheme.accent.opacity(0.22), style: StrokeStyle(lineWidth: 1, dash: [2, 6]))
                .frame(width: 124, height: 124)
            Circle().stroke(GhostTheme.accent.opacity(0.5), lineWidth: 1).frame(width: 88, height: 88)

            GhostMark(size: 56, glow: true)
        }
        .frame(width: 200, height: 200)
        .onAppear {
            withAnimation(.linear(duration: 48).repeatForever(autoreverses: false)) { angle = 360 }
            withAnimation(.easeInOut(duration: 5).repeatForever(autoreverses: true)) { pulse = true }
        }
    }
}
