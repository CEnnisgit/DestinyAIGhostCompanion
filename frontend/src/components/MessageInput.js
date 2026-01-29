import React, { useEffect, useState, useRef, useCallback, useMemo } from 'react';

// Enhanced composer: robust speech-to-text pipeline + voice controls
const MessageInput = ({ onSend, disabled, speakEnabled, onSpeakChange, selectedVoice, onVoiceChange, availableVoices, micDeviceId, micDetectionError, serverMicAvailable, serverMicDefaultIndex }) => {
  const [value, setValue] = useState('');
  const [listening, setListening] = useState(false);
  const [recordingMode, setRecordingMode] = useState(null); // 'speech' | 'recorder' | null
  const [transcribing, setTranscribing] = useState(false);
  const [micError, setMicError] = useState('');
  const [speechStatus, setSpeechStatus] = useState('');
  const speechStatusBootRef = useRef(true);
  const recognitionRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const recordedChunksRef = useRef([]);
  const serverDeviceIndex = useMemo(() => {
    if (!micDeviceId || typeof micDeviceId !== 'string') {
      return null;
    }
    if (!micDeviceId.startsWith('server:')) {
      return null;
    }
    const idx = Number(micDeviceId.split(':')[1]);
    if (Number.isNaN(idx)) {
      return null;
    }
    return idx;
  }, [micDeviceId]);

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!value.trim()) {
      if (transcribing) return;
      if (listening) {
        stopRecording();
      } else {
        startRecording();
      }
      return;
    }
    onSend(value);
    setValue('');
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      handleSubmit(event);
    }
  };

  const cleanupMediaStream = useCallback(() => {
    const stream = mediaStreamRef.current;
    if (stream) {
      stream.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch {}
      });
    }
    mediaStreamRef.current = null;
  }, []);

  const stopRecognitionSession = useCallback(() => {
    const recognition = recognitionRef.current;
    if (recognition) {
      try {
        recognition.onresult = null;
        recognition.onerror = null;
        recognition.onend = null;
        recognition.stop();
      } catch {}
      recognitionRef.current = null;
    }
  }, []);

  const startSpeechRecognition = useCallback(() => {
    if (typeof window === 'undefined') return false;
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return false;
    try {
      const recognition = new SpeechRecognition();
      recognition.lang = (typeof navigator !== 'undefined' && navigator.language) ? navigator.language : 'en-US';
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;
      recognitionRef.current = recognition;
      recognition.onresult = (event) => {
        const results = event?.results;
        const lastResult = results && results[results.length - 1];
        const transcript = lastResult && lastResult[0] && lastResult[0].transcript;
        const text = (transcript || '').trim();
        if (text) {
          onSend(text);
        } else {
          setMicError('No speech detected. Try again.');
        }
        setListening(false);
        setRecordingMode(null);
        recognitionRef.current = null;
      };
      recognition.onerror = (event) => {
        let message = 'Speech recognition failed.';
        if (event?.error === 'not-allowed' || event?.error === 'service-not-allowed') {
          message = 'Microphone permission denied.';
        } else if (event?.error === 'no-speech') {
          message = 'No speech detected.';
        }
        setMicError(message);
        setListening(false);
        setRecordingMode(null);
        recognitionRef.current = null;
      };
      recognition.onend = () => {
        setListening(false);
        setRecordingMode((mode) => (mode === 'speech' ? null : mode));
        recognitionRef.current = null;
      };
      recognition.start();
      setRecordingMode('speech');
      setListening(true);
      return true;
    } catch (error) {
      console.warn('SpeechRecognition start failed, falling back to recorder', error);
      stopRecognitionSession();
      return false;
    }
  }, [onSend, stopRecognitionSession]);

  const startMediaRecorder = useCallback(async () => {
    if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
      throw new Error('Browser does not support microphone access.');
    }
    let stream = null;
    const constraints = micDeviceId ? { audio: { deviceId: { exact: micDeviceId } } } : { audio: true };
    try {
      stream = await navigator.mediaDevices.getUserMedia(constraints);
    } catch (error) {
      console.warn('Preferred mic unavailable; retrying with default device.', error);
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    }
    if (!stream) {
      throw new Error('Unable to access microphone.');
    }
    if (typeof MediaRecorder === 'undefined') {
      stream.getTracks().forEach((track) => track.stop());
      throw new Error('MediaRecorder is not supported in this browser.');
    }
    recordedChunksRef.current = [];
    const options = {};
    if (MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
      options.mimeType = 'audio/webm;codecs=opus';
    }
    const recorder = new MediaRecorder(stream, options);
    mediaStreamRef.current = stream;
    mediaRecorderRef.current = recorder;
    recorder.ondataavailable = (event) => {
      if (event?.data && event.data.size > 0) {
        recordedChunksRef.current.push(event.data);
      }
    };
    recorder.onstop = handleRecorderStop;
    recorder.onerror = (event) => {
      console.error('MediaRecorder error', event?.error || event);
      setMicError('Recording error. Try again.');
      setListening(false);
      setRecordingMode(null);
      cleanupMediaStream();
    };
    recorder.start();
    setRecordingMode('recorder');
    setListening(true);
  }, [cleanupMediaStream, micDeviceId]);

  const startServerSideRecording = useCallback(
    async (deviceOverride = null) => {
      if (!serverMicAvailable && typeof deviceOverride !== 'number' && typeof serverMicDefaultIndex !== 'number') {
        setMicError('No desktop microphones available for capture.');
        return;
      }
      setMicError('');
      setSpeechStatus('Recording via desktop...');
      setListening(true);
      setRecordingMode('recorder');
      setTranscribing(true);
      try {
        const payload = {
          device_index:
            typeof deviceOverride === 'number'
              ? deviceOverride
              : (typeof serverMicDefaultIndex === 'number' ? serverMicDefaultIndex : null),
        };
        const resp = await fetch('/stt/local', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (!resp.ok) {
          const detail = await safeReadJson(resp);
          throw new Error(detail?.detail || 'Desktop recording failed.');
        }
        const data = await resp.json();
        const text = String(data?.text || '').trim();
        if (text) {
          onSend(text);
        } else {
          setMicError('No speech detected.');
        }
      } catch (error) {
        setMicError(error?.message || 'Desktop recording failed.');
        console.error('Desktop microphone capture failed', error);
      } finally {
        setTranscribing(false);
        setListening(false);
        setRecordingMode(null);
        setSpeechStatus('');
      }
    },
    [onSend, serverMicAvailable, serverMicDefaultIndex]
  );

  const startRecording = useCallback(async () => {
    if (disabled || listening || transcribing) return;
    setMicError('');

    if (serverDeviceIndex !== null) {
      await startServerSideRecording(serverDeviceIndex);
      return;
    }

    const recognitionStarted = startSpeechRecognition();
    if (recognitionStarted) {
      return;
    }

    try {
      await startMediaRecorder();
    } catch (error) {
      setMicError(error?.message || 'Microphone not available.');
      console.error('Microphone capture failed', error);
      if (serverMicAvailable) {
        await startServerSideRecording(serverDeviceIndex);
      }
    }
  }, [
    disabled,
    listening,
    transcribing,
    startSpeechRecognition,
    startMediaRecorder,
    serverDeviceIndex,
    serverMicAvailable,
    startServerSideRecording,
  ]);

  const stopRecording = useCallback(() => {
    if (!listening) return;
    if (recordingMode === 'speech') {
      stopRecognitionSession();
    } else if (recordingMode === 'recorder') {
      const recorder = mediaRecorderRef.current;
      if (recorder && recorder.state !== 'inactive') {
        recorder.stop();
      }
    }
  }, [listening, recordingMode, stopRecognitionSession]);

  const handleRecorderStop = async () => {
    mediaRecorderRef.current = null;
    cleanupMediaStream();
    setListening(false);
    setRecordingMode(null);
    const chunks = recordedChunksRef.current;
    recordedChunksRef.current = [];
    if (!chunks.length) {
      return;
    }
    setTranscribing(true);
    try {
      const wavBlob = await blobToWav(new Blob(chunks));
      await sendForTranscription(wavBlob);
    } catch (error) {
      const message = error?.message || 'Speech recognition failed. Check server STT configuration.';
      setMicError(message);
      console.error('Transcription error', error);
    } finally {
      setTranscribing(false);
    }
  };

  async function safeReadJson(response) {
    try {
      return await response.json();
    } catch {
      return null;
    }
  }

  const sendForTranscription = async (blob) => {
    const formData = new FormData();
    formData.append('file', blob, 'audio.wav');
    const response = await fetch('/stt', { method: 'POST', body: formData });
    if (!response.ok) {
      const detail = await safeReadJson(response);
      throw new Error(detail?.detail || 'Speech recognition service returned an error.');
    }
    const data = await response.json();
    if (data?.text) {
      const text = String(data.text).trim();
      if (text) {
        onSend(text);
        return;
      }
    }
    throw new Error('No transcription returned. Ensure STT provider is configured.');
  };

  const voiceOptions = (availableVoices && availableVoices.length) ? availableVoices : [{ key: 'system', name: 'System (device TTS)', provider: 'pyttsx3' }];
  const currentVoice = selectedVoice || 'system';
  useEffect(() => {
    if (speechStatusBootRef.current) {
      speechStatusBootRef.current = false;
      return undefined;
    }
    const nextStatus = speakEnabled ? 'Speech replies enabled' : 'Speech replies off';
    setSpeechStatus(nextStatus);
    const timer = window.setTimeout(() => setSpeechStatus(''), 2000);
    return () => window.clearTimeout(timer);
  }, [speakEnabled]);

  const statusMessage = listening
    ? (recordingMode === 'speech' ? 'Listening\u2026' : 'Recording\u2026')
    : (transcribing ? 'Transcribing\u2026' : speechStatus);
  const combinedMicError = micError || micDetectionError || '';

  const handleSpeakToggle = () => {
    if (disabled || transcribing || !onSpeakChange) {
      return;
    }
    onSpeakChange(!speakEnabled);
  };

  useEffect(() => () => {
    stopRecognitionSession();
    const recorder = mediaRecorderRef.current;
    try {
      if (recorder && recorder.state !== 'inactive') {
        recorder.stop();
      }
    } catch {}
    cleanupMediaStream();
  }, [cleanupMediaStream, stopRecognitionSession]);

  const autoVoiceLoopRef = useRef(false);
  useEffect(() => {
    if (!speakEnabled) {
      autoVoiceLoopRef.current = false;
      if (listening) {
        stopRecording();
      }
      return;
    }
    if (disabled || transcribing || listening) {
      return;
    }
    if (micDetectionError) {
      return;
    }
    if (value.trim()) {
      return;
    }
    if (autoVoiceLoopRef.current) {
      return;
    }
    autoVoiceLoopRef.current = true;
    startRecording()
      .catch(() => {
        // Errors surfaced through micError already
      })
      .finally(() => {
        autoVoiceLoopRef.current = false;
      });
  }, [speakEnabled, disabled, transcribing, listening, micDetectionError, value, startRecording, stopRecording]);

  return (
    <form className="message-input" onSubmit={handleSubmit}>
      <div className="message-input__left">
        <select
          className="message-input__voice"
          value={currentVoice}
          onChange={(e)=> onVoiceChange && onVoiceChange(e.target.value)}
          title="Voice for spoken replies"
        >
          {voiceOptions.map((v) => (
            <option key={v.key} value={v.key}>{v.name}</option>
          ))}
        </select>
      </div>
      <textarea
        value={value}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask your Ghost anything..."
        rows={2}
        disabled={disabled}
        aria-label="Message"
      />
      <div className="message-input__actions">
        <div className="message-input__buttons">
          <button
            type="button"
            className={`message-input__speak-toggle${speakEnabled ? ' active' : ''}`}
            onClick={handleSpeakToggle}
            disabled={disabled || transcribing}
            aria-pressed={!!speakEnabled}
            title={speakEnabled ? 'Disable speech replies' : 'Enable speech replies and text to speech'}
          >
            {speakEnabled ? 'Speech On' : 'Speech Off'}
          </button>
          <button type="submit" disabled={disabled || transcribing} title={'Send'}>
            Send
          </button>
        </div>
        {(statusMessage || combinedMicError) && (
          <div
            className={`message-input__mic-status${statusMessage ? ' message-input__mic-status--active' : ''}`}
            aria-live="polite"
          >
            {statusMessage && <span>{statusMessage}</span>}
            {combinedMicError && <span className="message-input__mic-error">{combinedMicError}</span>}
          </div>
        )}
      </div>
    </form>
  );
};

async function blobToWav(blob) {
  if (typeof window === 'undefined') {
    throw new Error('Audio decoding is not supported in this environment.');
  }
  const arrayBuffer = await blob.arrayBuffer();
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  if (!AudioContext) {
    throw new Error('AudioContext is not supported in this browser.');
  }
  const audioContext = new AudioContext();
  try {
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    const monoChannel = mixToMono(audioBuffer);
    return encodeWav([monoChannel], audioBuffer.sampleRate || 16000);
  } finally {
    try {
      await audioContext.close();
    } catch {}
  }
}

function mixToMono(audioBuffer) {
  if (audioBuffer.numberOfChannels === 1) {
    return new Float32Array(audioBuffer.getChannelData(0));
  }
  const length = audioBuffer.length;
  const tmp = new Float32Array(length);
  for (let channel = 0; channel < audioBuffer.numberOfChannels; channel += 1) {
    const data = audioBuffer.getChannelData(channel);
    for (let i = 0; i < length; i += 1) {
      tmp[i] += data[i] / audioBuffer.numberOfChannels;
    }
  }
  return tmp;
}

function encodeWav(chunks, sampleRate) {
  if (!chunks || !chunks.length) {
    return new Blob([], { type: 'audio/wav' });
  }
  const length = chunks.reduce((acc, chunk) => acc + chunk.length, 0);
  const pcm = new Float32Array(length);
  let offset = 0;
  for (const chunk of chunks) {
    pcm.set(chunk, offset);
    offset += chunk.length;
  }
  const buffer = new ArrayBuffer(44 + pcm.length * 2);
  const view = new DataView(buffer);
  writeString(view, 0, 'RIFF');
  view.setUint32(4, 36 + pcm.length * 2, true);
  writeString(view, 8, 'WAVE');
  writeString(view, 12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(view, 36, 'data');
  view.setUint32(40, pcm.length * 2, true);
  let idx = 44;
  for (let i = 0; i < pcm.length; i += 1) {
    let s = Math.max(-1, Math.min(1, pcm[i]));
    view.setInt16(idx, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    idx += 2;
  }
  return new Blob([view], { type: 'audio/wav' });
}

function writeString(view, offset, str) {
  for (let i = 0; i < str.length; i += 1) {
    view.setUint8(offset + i, str.charCodeAt(i));
  }
}

export default MessageInput;
