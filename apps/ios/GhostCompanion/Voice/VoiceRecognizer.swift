import AVFoundation
import Foundation
import Speech

/// On-device speech capture. Streams microphone audio into `SFSpeechRecognizer`
/// and publishes a live transcript the chat view can send to the Ghost.
@MainActor
final class VoiceRecognizer: ObservableObject {
    @Published private(set) var isRecording = false
    @Published private(set) var transcript = ""
    @Published var errorMessage: String?

    private let recognizer = SFSpeechRecognizer()
    private let audioEngine = AVAudioEngine()
    private var request: SFSpeechAudioBufferRecognitionRequest?
    private var task: SFSpeechRecognitionTask?

    var isAvailable: Bool { recognizer?.isAvailable ?? false }

    /// Requests speech-recognition + microphone permission.
    func requestPermissions() async -> Bool {
        let speechAuthorized = await withCheckedContinuation { continuation in
            SFSpeechRecognizer.requestAuthorization { status in
                continuation.resume(returning: status == .authorized)
            }
        }
        let micAuthorized = await withCheckedContinuation { continuation in
            AVAudioApplication.requestRecordPermission { granted in
                continuation.resume(returning: granted)
            }
        }
        return speechAuthorized && micAuthorized
    }

    func start() {
        guard let recognizer, recognizer.isAvailable else {
            errorMessage = "Speech recognition is unavailable on this device."
            return
        }
        task?.cancel()
        task = nil
        transcript = ""
        errorMessage = nil

        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.record, mode: .measurement, options: .duckOthers)
            try session.setActive(true, options: .notifyOthersOnDeactivation)
        } catch {
            errorMessage = "Could not start audio: \(error.localizedDescription)"
            return
        }

        let request = SFSpeechAudioBufferRecognitionRequest()
        request.shouldReportPartialResults = true
        self.request = request

        let input = audioEngine.inputNode
        input.installTap(onBus: 0, bufferSize: 1024, format: input.outputFormat(forBus: 0)) { [weak self] buffer, _ in
            self?.request?.append(buffer)
        }
        audioEngine.prepare()

        do {
            try audioEngine.start()
        } catch {
            errorMessage = "Could not start microphone: \(error.localizedDescription)"
            teardownAudio()
            return
        }

        isRecording = true
        task = recognizer.recognitionTask(with: request) { [weak self] result, error in
            Task { @MainActor in
                guard let self else { return }
                if let result {
                    self.transcript = result.bestTranscription.formattedString
                    if result.isFinal { self.stop() }
                }
                if error != nil { self.stop() }
            }
        }
    }

    func stop() {
        guard isRecording else { return }
        teardownAudio()
        request?.endAudio()
        request = nil
        task = nil
        isRecording = false
    }

    private func teardownAudio() {
        if audioEngine.isRunning { audioEngine.stop() }
        audioEngine.inputNode.removeTap(onBus: 0)
    }
}
