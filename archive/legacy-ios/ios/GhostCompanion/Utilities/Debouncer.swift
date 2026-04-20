import Foundation

@MainActor
final class Debouncer {
    private var task: Task<Void, Never>?
    private let interval: Duration

    init(seconds: Double) { self.interval = .milliseconds(Int(seconds * 1000)) }

    func call(_ action: @escaping () -> Void) {
        task?.cancel()
        task = Task {
            try? await Task.sleep(for: interval)
            if Task.isCancelled { return }
            action()
        }
    }
}
