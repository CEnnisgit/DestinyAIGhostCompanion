import SwiftUI

/// A symmetric, radially-centered sacred-geometry backdrop: a starfield,
/// concentric rings, evenly-spaced radial spokes, a faceted star, and a
/// Flower-of-Life seed — all centered for a divine, balanced feel.
struct SacredBackground: View {
    var body: some View {
        Canvas { ctx, size in
            let accent = GhostTheme.accent
            let c = CGPoint(x: size.width / 2, y: size.height / 2)
            let maxR = Double(max(size.width, size.height))

            // Deterministic starfield.
            var seed: UInt64 = 1337
            func rand() -> Double {
                seed = seed &* 1_103_515_245 &+ 12_345
                return Double((seed >> 16) & 0x7fff) / Double(0x7fff)
            }
            let starColor = Color(red: 0.81, green: 0.89, blue: 1.0)
            for _ in 0..<90 {
                let x = rand() * Double(size.width)
                let y = rand() * Double(size.height)
                let r = rand() * 1.1 + 0.2
                let o = rand() * 0.5 + 0.1
                ctx.fill(Path(ellipseIn: CGRect(x: x - r, y: y - r, width: r * 2, height: r * 2)),
                         with: .color(starColor.opacity(o)))
            }

            // Concentric rings centered.
            var frac = 0.08
            while frac <= 0.95 {
                let r = maxR * frac
                ctx.stroke(Path(ellipseIn: CGRect(x: c.x - r, y: c.y - r, width: r * 2, height: r * 2)),
                           with: .color(accent.opacity(0.15)), lineWidth: 0.7)
                frac += 0.13
            }

            // Evenly-spaced radial spokes from center (dotted, symmetric).
            let dashed = StrokeStyle(lineWidth: 0.6, dash: [1, 7])
            for i in 0..<48 {
                let a = Double(i) * 2 * .pi / 48
                let start = CGPoint(x: c.x + CGFloat(cos(a)) * 70, y: c.y + CGFloat(sin(a)) * 70)
                let end = CGPoint(x: c.x + CGFloat(cos(a)) * maxR, y: c.y + CGFloat(sin(a)) * maxR)
                ctx.stroke(line(start, end), with: .color(accent.opacity(0.12)), style: dashed)
            }

            // Centered faceted star.
            ctx.stroke(starPath(center: c, outer: 120, inner: 56, points: 12),
                       with: .color(accent.opacity(0.5)), lineWidth: 0.9)

            // Flower-of-Life seed: a central circle ringed by six, hexagonally.
            let seedR: CGFloat = 40
            var centers = [c]
            for i in 0..<6 {
                let a = Double(i) * .pi / 3
                centers.append(CGPoint(x: c.x + CGFloat(cos(a)) * seedR, y: c.y + CGFloat(sin(a)) * seedR))
            }
            for center in centers {
                ctx.stroke(Path(ellipseIn: CGRect(x: center.x - seedR, y: center.y - seedR, width: seedR * 2, height: seedR * 2)),
                           with: .color(accent.opacity(0.14)), lineWidth: 0.7)
            }
        }
        .allowsHitTesting(false)
        .ignoresSafeArea()
    }

    private func line(_ a: CGPoint, _ b: CGPoint) -> Path {
        Path { p in
            p.move(to: a)
            p.addLine(to: b)
        }
    }

    private func starPath(center: CGPoint, outer: CGFloat, inner: CGFloat, points: Int) -> Path {
        var path = Path()
        for i in 0..<(points * 2) {
            let r = i % 2 == 0 ? outer : inner
            let a = Double(i) * .pi / Double(points) - .pi / 2
            let pt = CGPoint(x: center.x + CGFloat(cos(a)) * r, y: center.y + CGFloat(sin(a)) * r)
            if i == 0 { path.move(to: pt) } else { path.addLine(to: pt) }
        }
        path.closeSubpath()
        return path
    }
}

/// A faceted star outline shape.
struct StarShape: Shape {
    var points: Int = 8
    var innerRatio: CGFloat = 0.5

    func path(in rect: CGRect) -> Path {
        var path = Path()
        let c = CGPoint(x: rect.midX, y: rect.midY)
        let outer = min(rect.width, rect.height) / 2
        let inner = outer * innerRatio
        for i in 0..<(points * 2) {
            let r = i % 2 == 0 ? outer : inner
            let a = Double(i) * .pi / Double(points) - .pi / 2
            let pt = CGPoint(x: c.x + CGFloat(cos(a)) * r, y: c.y + CGFloat(sin(a)) * r)
            if i == 0 { path.move(to: pt) } else { path.addLine(to: pt) }
        }
        path.closeSubpath()
        return path
    }
}

/// The Ghost framed by a rotating rosette, a counter-rotating faceted star, and
/// a soft, breathing radiant bloom of the Traveler's light.
struct GhostHalo: View {
    @State private var angle: Double = 0
    @State private var revAngle: Double = 0
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

            StarShape(points: 8, innerRatio: 0.5)
                .stroke(GhostTheme.accent.opacity(0.35), lineWidth: 0.8)
                .frame(width: 120, height: 120)
                .rotationEffect(.degrees(revAngle))

            Circle()
                .stroke(GhostTheme.accent.opacity(0.22), style: StrokeStyle(lineWidth: 1, dash: [2, 6]))
                .frame(width: 124, height: 124)
            Circle().stroke(GhostTheme.accent.opacity(0.5), lineWidth: 1).frame(width: 88, height: 88)

            GhostMark(size: 56, glow: true)
        }
        .frame(width: 200, height: 200)
        .onAppear {
            withAnimation(.linear(duration: 48).repeatForever(autoreverses: false)) { angle = 360 }
            withAnimation(.linear(duration: 60).repeatForever(autoreverses: false)) { revAngle = -360 }
            withAnimation(.easeInOut(duration: 5).repeatForever(autoreverses: true)) { pulse = true }
        }
    }
}
