import SwiftUI
import Speech

struct VoiceInputSheet: View {
    let onDone: (String) -> Void

    @Environment(AppState.self) private var appState
    @Environment(\.dismiss) private var dismiss

    @State private var recognizer = SpeechRecognizerService()
    @State private var recorder = AudioRecorderService()
    @State private var transcript: String = ""
    @State private var listening: Bool = false
    @State private var error: String?
    @State private var usingFallback: Bool = false
    @State private var uploading: Bool = false

    var body: some View {
        VStack(spacing: 24) {
            Capsule().fill(Theme.textMuted.opacity(0.4))
                .frame(width: 36, height: 4)
                .padding(.top, 12)

            Text(listening ? "Listening…" : (uploading ? "Transcribing…" : "Tap to speak"))
                .font(Typography.title)
                .foregroundStyle(Theme.textPrimary)

            ZStack {
                Circle()
                    .fill(Theme.accent.opacity(listening ? 0.25 : 0.12))
                    .frame(width: 160, height: 160)
                    .scaleEffect(listening ? 1.08 : 1.0)
                    .animation(.easeInOut(duration: 0.8).repeatForever(autoreverses: true), value: listening)
                Button {
                    Task { await toggle() }
                } label: {
                    Image(systemName: listening ? "stop.fill" : "mic.fill")
                        .font(.system(size: 44, weight: .bold))
                        .foregroundStyle(Color.black)
                        .frame(width: 100, height: 100)
                        .background(Theme.accent, in: Circle())
                }
            }

            ScrollView {
                Text(transcript.isEmpty ? "Your words appear here." : transcript)
                    .font(Typography.body)
                    .foregroundStyle(transcript.isEmpty ? Theme.textMuted : Theme.textPrimary)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 12)
            }
            .frame(maxHeight: 160)

            if let error {
                Text(error)
                    .font(Typography.meta)
                    .foregroundStyle(Theme.danger)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 24)
            }

            HStack(spacing: 12) {
                Button("Cancel") { dismiss() }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                    .background(Theme.backgroundElevated, in: Capsule())
                    .foregroundStyle(Theme.textPrimary)
                Button("Send") {
                    let trimmed = transcript.trimmingCharacters(in: .whitespacesAndNewlines)
                    if !trimmed.isEmpty { onDone(trimmed) } else { dismiss() }
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 12)
                .background(Theme.accent, in: Capsule())
                .foregroundStyle(Color.black)
                .disabled(transcript.trimmingCharacters(in: .whitespaces).isEmpty)
            }
            .padding(.horizontal, 24)
            .padding(.bottom, 24)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Theme.background.ignoresSafeArea())
    }

    private func toggle() async {
        if listening {
            await stop()
        } else {
            await start()
        }
    }

    private func start() async {
        error = nil
        transcript = ""
        let micGranted = await SpeechRecognizerService.requestMicrophone()
        guard micGranted else { error = "Microphone permission denied."; return }
        let speechStatus = await SpeechRecognizerService.requestAuthorization()

        if speechStatus == .authorized, recognizer.isAvailable {
            usingFallback = false
            listening = true
            recognizer.start { text, _ in
                Task { @MainActor in self.transcript = text }
            } onError: { e in
                Task { @MainActor in
                    self.error = e.localizedDescription
                    self.listening = false
                }
            }
        } else {
            // Fallback: record and upload.
            usingFallback = true
            do {
                try recorder.start()
                listening = true
            } catch {
                self.error = error.localizedDescription
            }
        }
    }

    private func stop() async {
        listening = false
        if usingFallback {
            guard let url = recorder.stop() else { return }
            uploading = true
            defer { uploading = false }
            do {
                let wav = try WavConverter.wavData(from: url)
                let text = try await appState.api.transcribe(wav: wav)
                transcript = text
            } catch {
                self.error = (error as? LocalizedError)?.errorDescription ?? error.localizedDescription
            }
        } else {
            recognizer.stop()
        }
    }
}
