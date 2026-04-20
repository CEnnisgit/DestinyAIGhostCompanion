import Foundation
import AVFoundation

@MainActor
final class AudioRecorderService: NSObject {
    private var recorder: AVAudioRecorder?
    private(set) var currentURL: URL?

    func start() throws {
        let session = AVAudioSession.sharedInstance()
        try session.setCategory(.record, mode: .default, options: [.duckOthers])
        try session.setActive(true, options: .notifyOthersOnDeactivation)

        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("ghost-\(UUID().uuidString).caf")
        let settings: [String: Any] = [
            AVFormatIDKey: kAudioFormatLinearPCM,
            AVSampleRateKey: 16000.0,
            AVNumberOfChannelsKey: 1,
            AVLinearPCMBitDepthKey: 16,
            AVLinearPCMIsFloatKey: false,
            AVLinearPCMIsBigEndianKey: false,
        ]
        let rec = try AVAudioRecorder(url: url, settings: settings)
        rec.prepareToRecord()
        guard rec.record() else {
            throw NSError(domain: "AudioRecorder", code: 1, userInfo: [NSLocalizedDescriptionKey: "Failed to start recording"])
        }
        self.recorder = rec
        self.currentURL = url
    }

    @discardableResult
    func stop() -> URL? {
        recorder?.stop()
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
        let url = currentURL
        recorder = nil
        return url
    }

    var isRecording: Bool { recorder?.isRecording == true }
}
