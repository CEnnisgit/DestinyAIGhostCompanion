import Foundation
import os

enum AppLogger {
    static let auth = Logger(subsystem: "com.ghostcompanion.ios", category: "auth")
    static let network = Logger(subsystem: "com.ghostcompanion.ios", category: "network")
    static let chat = Logger(subsystem: "com.ghostcompanion.ios", category: "chat")
    static let voice = Logger(subsystem: "com.ghostcompanion.ios", category: "voice")
}
