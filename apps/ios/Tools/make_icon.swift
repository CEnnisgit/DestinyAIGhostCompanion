// Generates the 1024×1024 app icon (Ghost-shell reticle on a deep-space gradient)
// to match GhostMark.swift. Run: swift make_icon.swift <output.png>
import CoreGraphics
import Foundation
import ImageIO
import UniformTypeIdentifiers

let side = 1024
let cs = CGColorSpaceCreateDeviceRGB()
guard let ctx = CGContext(
    data: nil, width: side, height: side, bitsPerComponent: 8, bytesPerRow: 0,
    space: cs, bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue
) else { fatalError("context") }

func color(_ r: Double, _ g: Double, _ b: Double, _ a: Double = 1) -> CGColor {
    CGColor(srgbRed: r, green: g, blue: b, alpha: a)
}

let center = CGPoint(x: Double(side) / 2, y: Double(side) / 2)

// Deep-space background gradient.
let bg = CGGradient(colorsSpace: cs,
                    colors: [color(0.06, 0.09, 0.14), color(0.015, 0.025, 0.045)] as CFArray,
                    locations: [0, 1])!
ctx.drawLinearGradient(bg, start: CGPoint(x: 0, y: Double(side)), end: .zero, options: [])

// Soft gold aura behind the mark.
let aura = CGGradient(colorsSpace: cs,
                      colors: [color(0.96, 0.78, 0.42, 0.50), color(0.96, 0.78, 0.42, 0)] as CFArray,
                      locations: [0, 1])!
ctx.drawRadialGradient(aura, startCenter: center, startRadius: 0, endCenter: center, endRadius: 380, options: [])

func diamond(scale: Double, corner: Double, line: Double, stroke: CGColor) {
    ctx.saveGState()
    ctx.translateBy(x: center.x, y: center.y)
    ctx.rotate(by: .pi / 4)
    let s = Double(side) * scale
    let rect = CGRect(x: -s / 2, y: -s / 2, width: s, height: s)
    ctx.addPath(CGPath(roundedRect: rect, cornerWidth: corner, cornerHeight: corner, transform: nil))
    ctx.setStrokeColor(stroke)
    ctx.setLineWidth(line)
    ctx.strokePath()
    ctx.restoreGState()
}

diamond(scale: 0.50, corner: 64, line: 32, stroke: color(0.96, 0.78, 0.42))
diamond(scale: 0.30, corner: 40, line: 20, stroke: color(0.96, 0.78, 0.42, 0.55))

// Glowing core.
let core = CGGradient(colorsSpace: cs,
                      colors: [color(1, 0.87, 0.55, 0.95), color(1, 0.87, 0.55, 0)] as CFArray,
                      locations: [0, 1])!
ctx.drawRadialGradient(core, startCenter: center, startRadius: 0, endCenter: center, endRadius: 160, options: [])
ctx.setFillColor(color(1, 0.91, 0.66))
ctx.fillEllipse(in: CGRect(x: center.x - 72, y: center.y - 72, width: 144, height: 144))

guard let image = ctx.makeImage() else { fatalError("image") }
let outPath = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "AppIcon-1024.png"
let url = URL(fileURLWithPath: outPath)
guard let dest = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil) else {
    fatalError("destination")
}
CGImageDestinationAddImage(dest, image, nil)
CGImageDestinationFinalize(dest)
print("wrote \(url.path)")
