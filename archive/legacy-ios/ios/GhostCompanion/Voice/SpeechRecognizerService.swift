import Foundation
import Speech
import AVFoundation

@MainActor
final class SpeechRecognizerService {
    enum RecognizerError: Error, LocalizedError {
        case unauthorized
        case unavailable
        case audioSession(String)

        var errorDescription: String? {
            switch self {
            case .unauthorized: return "Speech recognition permission denied."
            case .unavailable: return "Speech recognition is not available on this device."
            case .audioSession(let msg): return msg
            }
        }
    }

    private let recognizer: SFSpeechRecognizer?
    private let audioEngine = AVAudioEngine()
    private var request: SFSpeechAudioBufferRecognitionRequest?
    private var task: SFSpeechRecognitionTask?

    init(locale: Locale = .current) {
        self.recognizer = SFSpeechRecognizer(locale: locale)
    }

    static func requestAuthorization() async -> SFSpeechRecognizerAuthorizationStatus {
        await withCheckedContinuation { cont in
            SFSpeechRecognizer.requestAuthorization { status in cont.resume(returning: status) }
        }
    }

    static func requestMicrophone() async -> Bool {
        await withCheckedContinuation { cont in
            AVAudioApplication.requestRecordPermission { granted in cont.resume(returning: granted) }
        }
    }

    var isAvailable: Bool { recognizer?.isAvailable == true }

    /// Streams partial transcripts. Call `stop()` to finalize.
    func start(onUpdate: @escaping (String, Bool) -> Void, onError: @escaping (Error) -> Void) {
        guard let recognizer, recognizer.isAvailable else { onError(RecognizerError.unavailable); return }
        let status = SFSpeechRecognizer.authorizationStatus()
        guard status == .authorized else { onError(RecognizerError.unauthorized); return }

        let session = AVAudioSession.sharedInstance()
        do {
            try session.setCategory(.record, mode: .measurement, options: [.duckOthers])
            try session.setActive(true, options: .notifyOthersOnDeactivation)
        } catch {
            onError(RecognizerError.audioSession(error.localizedDescription)); return
        }

        let request = SFSpeechAudioBufferRecognitionRequest()
        request.shouldReportPartialResults = true
        self.request = request

        let input = audioEngine.inputNode
        let format = input.outputFormat(forBus: 0)
        input.removeTap(onBus: 0)
        input.installTap(onBus: 0, bufferSize: 1024, format: format) { buffer, _ in
            request.append(buffer)
        }
        audioEngine.prepare()
        do { try audioEngine.start() } catch {
            onError(RecognizerError.audioSession(error.localizedDescription)); return
        }

        task = recognizer.recognitionTask(with: request) { result, error in
            if let result {
                let isFinal = result.isFinal
                onUpdate(result.bestTranscription.formattedString, isFinal)
            }
            if let error { onError(error) }
        }
    }

    func stop() {
        audioEngine.stop()
        audioEngine.inputNode.removeTap(onBus: 0)
        request?.endAudio()
        task?.finish()
        request = nil
        task = nil
    }
}
