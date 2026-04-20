import SwiftUI

struct HamburgerButton: View {
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Image(systemName: "line.3.horizontal")
                .font(.system(size: 17, weight: .semibold))
                .foregroundStyle(Theme.textPrimary)
                .frame(width: 40, height: 40)
                .background(Theme.backgroundElevated, in: Circle())
        }
        .accessibilityLabel("Open chats")
    }
}
