import { useCallback, useRef, useState } from "react";

// Thin wrapper over the browser SpeechRecognition API (Chrome/Safari).
export function useSpeech() {
  const Recognition =
    (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  const supported = Boolean(Recognition);

  const [recording, setRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const recRef = useRef<any>(null);

  const start = useCallback(() => {
    if (!Recognition) return;
    const rec = new Recognition();
    rec.lang = "en-US";
    rec.interimResults = true;
    rec.continuous = false;
    rec.onresult = (event: any) => {
      let text = "";
      for (let i = 0; i < event.results.length; i += 1) {
        text += event.results[i][0].transcript;
      }
      setTranscript(text);
    };
    rec.onend = () => setRecording(false);
    rec.onerror = () => setRecording(false);
    recRef.current = rec;
    setTranscript("");
    setRecording(true);
    rec.start();
  }, [Recognition]);

  const stop = useCallback(() => {
    recRef.current?.stop();
    setRecording(false);
  }, []);

  return { supported, recording, transcript, start, stop };
}
