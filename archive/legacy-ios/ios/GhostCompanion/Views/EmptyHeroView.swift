import SwiftUI

struct EmptyHeroView: View {
    let onSend: (String) -> Void
    let onMic: () -> Void

    var body: some View {
        VStack {
            Spacer()
            VStack(spacing: 12) {
                Image(systemName: "circle.grid.cross.fill")
                    .font(.system(size: 46))
                    .foregroundStyle(Theme.accent)
                Text("Hey Guardian,")
                    .font(Typography.hero)
                Text("how can I help?")
                    .font(Typography.hero)
                    .foregroundStyle(Theme.textMuted)
            }
            Spacer()
            ComposerView(
                isStreaming: false,
                onSend: onSend,
                onStop: {},
                onMic: onMic
            )
            .padding(.horizontal, 12)
            .padding(.bottom, 12)
        }
    }
}
