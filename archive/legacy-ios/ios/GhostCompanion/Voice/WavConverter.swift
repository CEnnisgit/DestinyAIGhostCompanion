import Foundation
import AVFoundation

enum WavConverter {
    /// Wraps raw PCM-encoded audio at the given URL into a WAV file in memory.
    /// AudioRecorderService already records at 16 kHz / 16-bit / mono PCM in a `.caf`
    /// container; we reinterpret the samples and prepend a WAV header.
    static func wavData(from url: URL) throws -> Data {
        let file = try AVAudioFile(forReading: url)
        let inFormat = file.processingFormat
        let frameCount = AVAudioFrameCount(file.length)
        guard let buffer = AVAudioPCMBuffer(pcmFormat: inFormat, frameCapacity: frameCount) else {
            throw NSError(domain: "WavConverter", code: 1, userInfo: [NSLocalizedDescriptionKey: "Failed to allocate PCM buffer"])
        }
        try file.read(into: buffer)

        let targetFormat = AVAudioFormat(commonFormat: .pcmFormatInt16,
                                         sampleRate: 16000,
                                         channels: 1,
                                         interleaved: true)!
        guard let converter = AVAudioConverter(from: inFormat, to: targetFormat) else {
            throw NSError(domain: "WavConverter", code: 2, userInfo: [NSLocalizedDescriptionKey: "Unsupported format conversion"])
        }
        let ratio = targetFormat.sampleRate / inFormat.sampleRate
        let capacity = AVAudioFrameCount(Double(frameCount) * ratio) + 1024
        guard let out = AVAudioPCMBuffer(pcmFormat: targetFormat, frameCapacity: capacity) else {
            throw NSError(domain: "WavConverter", code: 3, userInfo: [NSLocalizedDescriptionKey: "Failed to allocate output buffer"])
        }
        var error: NSError?
        var supplied = false
        converter.convert(to: out, error: &error) { _, status in
            if supplied { status.pointee = .noDataNow; return nil }
            supplied = true
            status.pointee = .haveData
            return buffer
        }
        if let error { throw error }

        let sampleCount = Int(out.frameLength)
        let byteCount = sampleCount * 2
        var data = Data(capacity: 44 + byteCount)
        appendWavHeader(to: &data, sampleRate: 16000, channels: 1, bitsPerSample: 16, dataSize: UInt32(byteCount))
        if let int16 = out.int16ChannelData?[0] {
            data.append(UnsafeBufferPointer(start: int16, count: sampleCount))
        }
        return data
    }

    private static func appendWavHeader(to data: inout Data,
                                        sampleRate: UInt32,
                                        channels: UInt16,
                                        bitsPerSample: UInt16,
                                        dataSize: UInt32) {
        let byteRate = sampleRate * UInt32(channels) * UInt32(bitsPerSample) / 8
        let blockAlign = channels * bitsPerSample / 8
        let chunkSize = 36 + dataSize

        data.append("RIFF".data(using: .ascii)!)
        data.append(uint32LE(chunkSize))
        data.append("WAVE".data(using: .ascii)!)
        data.append("fmt ".data(using: .ascii)!)
        data.append(uint32LE(16))
        data.append(uint16LE(1))
        data.append(uint16LE(channels))
        data.append(uint32LE(sampleRate))
        data.append(uint32LE(byteRate))
        data.append(uint16LE(blockAlign))
        data.append(uint16LE(bitsPerSample))
        data.append("data".data(using: .ascii)!)
        data.append(uint32LE(dataSize))
    }

    private static func uint32LE(_ value: UInt32) -> Data {
        withUnsafeBytes(of: value.littleEndian) { Data($0) }
    }

    private static func uint16LE(_ value: UInt16) -> Data {
        withUnsafeBytes(of: value.littleEndian) { Data($0) }
    }
}

private extension Data {
    mutating func append(_ buffer: UnsafeBufferPointer<Int16>) {
        buffer.withMemoryRebound(to: UInt8.self) { bytes in
            append(bytes.baseAddress!, count: bytes.count)
        }
    }
}
