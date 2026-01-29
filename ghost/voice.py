from __future__ import annotations

import io
import os
import queue
import tempfile
import threading
from dataclasses import dataclass
from typing import Optional

import requests


# Optional imports guarded at runtime to keep base install light
try:
    import sounddevice as sd  # type: ignore
    import numpy as np  # type: ignore
    HAVE_SD = True
except Exception:
    HAVE_SD = False
    np = None  # type: ignore
    sd = None  # type: ignore

try:  # Fallback offline TTS
    import pyttsx3  # type: ignore
    HAVE_PYTTSX3 = True
except Exception:
    HAVE_PYTTSX3 = False


# ----------------------------- Audio capture -----------------------------

@dataclass
class AudioChunk:
    data: bytes
    sample_rate: int
    channels: int


class Recorder:
    def __init__(self, sample_rate: int = 16000, channels: int = 1, device: int | str | None = None):
        if not HAVE_SD:
            raise RuntimeError("sounddevice is not installed; microphone capture unavailable")
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device
        self._q: queue.Queue[bytes] = queue.Queue()
        self._stream: sd.InputStream | None = None  # type: ignore
        self._closed = threading.Event()

    def _on_audio(self, indata, frames, time, status):  # type: ignore[no-untyped-def]
        if status:
            pass
        self._q.put(indata.copy().tobytes())

    def start(self, *, device: int | str | None = None) -> None:
        if not HAVE_SD:
            raise RuntimeError("sounddevice not available")
        use_device = self.device if device is None else device
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="int16",
            callback=self._on_audio,
            device=use_device,
        )
        self._stream.start()

    def stop(self) -> AudioChunk:
        if self._stream is None:
            raise RuntimeError("Recorder not started")
        self._stream.stop()
        self._stream.close()
        self._stream = None
        self._closed.set()
        # Collect all buffered bytes
        chunks: list[bytes] = []
        while not self._q.empty():
            chunks.append(self._q.get_nowait())
        raw = b"".join(chunks)
        return AudioChunk(data=raw, sample_rate=self.sample_rate, channels=self.channels)

    def record_blocking(self, seconds: float, *, device: int | str | None = None) -> AudioChunk:
        self.start(device=device)
        sd.sleep(int(seconds * 1000))  # type: ignore[attr-defined]
        return self.stop()


def pcm16le_to_wav_bytes(pcm: AudioChunk) -> bytes:
    import wave

    bio = io.BytesIO()
    with wave.open(bio, "wb") as wf:
        wf.setnchannels(pcm.channels)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(pcm.sample_rate)
        wf.writeframes(pcm.data)
    return bio.getvalue()


# ----------------------------- STT providers -----------------------------

class STTProvider:
    def transcribe(self, wav_bytes: bytes, *, language: Optional[str] = None) -> str:
        raise NotImplementedError


class OpenAIWhisperSTT(STTProvider):
    def __init__(self, api_key: Optional[str] = None, model: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY not set for STT")
        self.model = model or os.getenv("OPENAI_WHISPER_MODEL", "gpt-4o-transcribe")

    def transcribe(self, wav_bytes: bytes, *, language: Optional[str] = None) -> str:
        files = {
            "file": ("audio.wav", wav_bytes, "audio/wav"),
        }
        data = {
            "model": self.model,
        }
        if language:
            data["language"] = language
        resp = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            files=files,
            data=data,
            timeout=60,
        )
        resp.raise_for_status()
        j = resp.json()
        return str(j.get("text", "")).strip()


class FasterWhisperSTT(STTProvider):
    def __init__(self, model_size: str = "small") -> None:
        try:
            from faster_whisper import WhisperModel  # type: ignore
        except Exception as exc:  # pragma: no cover - optional
            raise RuntimeError("faster-whisper not installed") from exc
        self._WhisperModel = WhisperModel
        self._model_size = model_size
        self._model = None

    def _load(self):
        if self._model is None:
            self._model = self._WhisperModel(self._model_size, compute_type="int8")

    def transcribe(self, wav_bytes: bytes, *, language: Optional[str] = None) -> str:
        import soundfile as sf  # type: ignore
        self._load()
        # Write wav to temp file for simplicity
        tmp_path = None
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp_path = tmp.name
            tmp.write(wav_bytes)
            tmp.flush()
            tmp.close()
            segments, info = self._model.transcribe(tmp_path, language=language)
        finally:
            if tmp_path:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
        text_parts = [seg.text for seg in segments]
        return " ".join(t.strip() for t in text_parts).strip()


def make_stt_provider() -> STTProvider:
    provider = os.getenv("STT_PROVIDER", "auto").lower()
    if provider in ("openai", "whisper", "api"):
        return OpenAIWhisperSTT()
    if provider == "local":
        return FasterWhisperSTT(os.getenv("WHISPER_MODEL_SIZE", "small"))
    # auto: prefer OpenAI if key exists
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIWhisperSTT()
    try:
        return FasterWhisperSTT(os.getenv("WHISPER_MODEL_SIZE", "small"))
    except Exception:
        # Final fallback: raise helpful error
        raise RuntimeError("No STT available. Set OPENAI_API_KEY or install faster-whisper.")


# ----------------------------- TTS providers -----------------------------

# Persona → suggested ElevenLabs env var to pick voice ID
PERSONA_VOICE_ENV = {
    "destiny_ghost": "ELEVEN_VOICE_ID_GHOST",
    "destiny_ghost_expressive": "ELEVEN_VOICE_ID_GHOST",
    "halo_guilty_spark": "ELEVEN_VOICE_ID_VERGIL",  # similar mission-control style
    "odst_vergil": "ELEVEN_VOICE_ID_VERGIL",
}


def voice_id_for_persona(persona: str | None) -> str | None:
    if not persona:
        return None
    env = PERSONA_VOICE_ENV.get(persona)
    if env:
        return os.getenv(env) or None
    return None


class TTSProvider:
    def speak(self, text: str, *, voice_id: Optional[str] = None) -> None:
        raise NotImplementedError


class Pyttsx3TTS(TTSProvider):
    def __init__(self) -> None:
        if not HAVE_PYTTSX3:
            raise RuntimeError("pyttsx3 not installed")
        self.engine = pyttsx3.init()

    def speak(self, text: str, *, voice_id: Optional[str] = None) -> None:
        # voice_id is ignored for pyttsx3 unless it matches available
        if voice_id:
            for v in self.engine.getProperty("voices"):
                if voice_id.lower() in (v.name or "").lower():
                    self.engine.setProperty("voice", v.id)
                    break
        self.engine.say(text)
        self.engine.runAndWait()


class ElevenLabsTTS(TTSProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVEN_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("ELEVEN_API_KEY not set for TTS")
        self.model = model or os.getenv("ELEVEN_TTS_MODEL", "eleven_multilingual_v2")

    def speak(self, text: str, *, voice_id: Optional[str] = None) -> None:
        vid = voice_id or os.getenv("ELEVEN_VOICE_ID", "")
        if not vid:
            # Users can create/select voices in ElevenLabs and set the ID here
            raise RuntimeError("Missing ElevenLabs voice_id. Set ELEVEN_VOICE_ID.")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{vid}"
        headers = {"xi-api-key": self.api_key, "accept": "audio/mpeg"}
        payload = {"text": text, "model_id": self.model, "voice_settings": {"stability": 0.5, "similarity_boost": 0.7}}
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        audio = resp.content  # mp3 bytes
        # Simple playback on Windows using playsound after writing temp file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(audio)
            tmp.flush()
            path = tmp.name
        try:
            from playsound import playsound  # type: ignore
            playsound(path)
        finally:
            try:
                os.remove(path)
            except Exception:
                pass


def make_tts_provider() -> TTSProvider:
    provider = os.getenv("TTS_PROVIDER", "auto").lower()
    if provider == "elevenlabs":
        return ElevenLabsTTS()
    if provider == "pyttsx3":
        return Pyttsx3TTS()
    # auto: prefer ElevenLabs if key set
    if os.getenv("ELEVEN_API_KEY") and os.getenv("ELEVEN_VOICE_ID"):
        return ElevenLabsTTS()
    try:
        return Pyttsx3TTS()
    except Exception:
        raise RuntimeError("No TTS available. Set ELEVEN_API_KEY/ELEVEN_VOICE_ID or install pyttsx3.")


# ----------------------------- Diagnostics ------------------------------

def diagnose_audio() -> str:
    """Return a diagnostic report for microphone (STT) and speaker (TTS).

    Helps troubleshoot common Windows issues (PortAudio, missing keys).
    """
    lines: list[str] = []
    # STT
    if HAVE_SD:
        try:
            import sounddevice as _sd  # type: ignore
            devs = _sd.query_devices()
            default_in = _sd.default.device[0] if hasattr(_sd, 'default') else None
            lines.append(f"Microphone: sounddevice available. Devices: {len(devs)}. Default input: {default_in}")
        except Exception as e:  # pragma: no cover - best-effort
            lines.append(f"Microphone: sounddevice import ok but device query failed: {e}")
    else:
        lines.append("Microphone: sounddevice not installed. pip install sounddevice (PortAudio required on Windows)")
    if os.getenv("OPENAI_API_KEY"):
        lines.append("STT: OpenAI Whisper API configured (OPENAI_API_KEY present)")
    else:
        lines.append("STT: OPENAI_API_KEY missing; will try local 'faster-whisper' if installed")
    # TTS
    if os.getenv("ELEVEN_API_KEY") and os.getenv("ELEVEN_VOICE_ID"):
        lines.append("TTS: ElevenLabs configured (ELEVEN_API_KEY/ELEVEN_VOICE_ID present)")
    elif HAVE_PYTTSX3:
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            lines.append(f"TTS: pyttsx3 available. Voices: {len(voices)}")
        except Exception as e:  # pragma: no cover - best-effort
            lines.append(f"TTS: pyttsx3 import ok but engine init failed: {e}")
    else:
        lines.append("TTS: No provider configured. Set ELEVEN_API_KEY/ELEVEN_VOICE_ID or pip install pyttsx3")
    return "\n".join(lines)
