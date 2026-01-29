/**
 * App.js — Main UI composition for Ghost Companion.
 *
 * Responsibilities
 * - Holds top-level state: messages, auth token, provider/persona, voices.
 * - Starts OAuth popup and completes the token exchange.
 * - Streams chat responses from `/chat/stream` and updates the UI incrementally.
 * - Lists/saves/loads conversations via server routes when authenticated.
 * - Exposes settings via the sidebar (provider, model, persona, mic/voice).
 *
 * High-level flow
 * 1) On load, check `/auth/status`; if not authenticated, show Bungie sign-in.
 * 2) When sending a message, create a placeholder assistant message and stream
 *    chunks into it as they arrive. After completion, refresh conversation list.
 * 3) Persist lightweight preferences in localStorage via `useLocalStorage`.
 */
import React, { useCallback, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import ChatWindow from './components/ChatWindow';
import MessageInput from './components/MessageInput';
// Bungie sign-in only; email/password removed
import LoadingSpinner from './components/LoadingSpinner';
import useLocalStorage from './hooks/useLocalStorage';
import TopBar from './components/TopBar';
import Sidebar from './components/Sidebar';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || '';

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});

const createMessageId = () => {
  if (typeof window !== 'undefined' && window.crypto?.randomUUID) {
    return window.crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
};

function App() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [token, setToken] = useLocalStorage('ghost-companion-token', '');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [chatSearch, setChatSearch] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [bungieLinked, setBungieLinked] = useState(false);
  const [apiKeyOk, setApiKeyOk] = useState(true);
  const [apiKeyMasked, setApiKeyMasked] = useState('');
  const [apiKeyError, setApiKeyError] = useState('');
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [apiKeySaving, setApiKeySaving] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [authRedirected, setAuthRedirected] = useState(false);
  const [provider, setProvider] = useLocalStorage('ghost-provider', 'ollama');
  const [ollamaModel, setOllamaModel] = useLocalStorage('ollama-model', 'llama3');
  const [availableModels, setAvailableModels] = useState({ ollama: [] });
  const [speakEnabled, setSpeakEnabled] = useLocalStorage('ghost-speak', false);
  const [selectedVoice, setSelectedVoice] = useLocalStorage('ghost-voice', 'system');
  const [availableVoices, setAvailableVoices] = useState([]);
  const autoVoiceRef = useRef(null);
  const applyVoiceSelection = useCallback(
    (voiceKey, auto = false) => {
      setSelectedVoice(voiceKey);
      autoVoiceRef.current = auto ? voiceKey : null;
    },
    [setSelectedVoice]
  );
  const handleVoiceChange = useCallback(
    (voiceKey) => {
      applyVoiceSelection(voiceKey, false);
    },
    [applyVoiceSelection]
  );
  const [savedConversations, setSavedConversations] = useLocalStorage('ghost-conversations', []);
  const [serverConversations, setServerConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useLocalStorage('ghost-active-convo', '');
  const [persona, setPersona] = useLocalStorage('ghost-persona', 'destiny_ghost');
  const [availablePersonas, setAvailablePersonas] = useState([]);
  // Microphone selection for STT
  const [micDevices, setMicDevices] = useState([]);
  const [serverMicDevices, setServerMicDevices] = useState([]);
  const [selectedMicId, setSelectedMicId] = useLocalStorage('ghost-mic', '');
  const [micDetectionError, setMicDetectionError] = useState('');
  const [micDiagOpen, setMicDiagOpen] = useState(false);
  const [micDiagLoading, setMicDiagLoading] = useState(false);
  const [micDiagResult, setMicDiagResult] = useState(null);
  const combinedMicDevices = React.useMemo(() => {
    return [...(micDevices || []), ...(serverMicDevices || [])];
  }, [micDevices, serverMicDevices]);
  React.useEffect(() => {
    if (!selectedMicId) {
      const first = combinedMicDevices[0];
      if (first && first.id) {
        setSelectedMicId(first.id);
      }
    }
  }, [combinedMicDevices, selectedMicId, setSelectedMicId]);
  const emptyState = messages.length === 0;

  const headers = useMemo(() => {
    if (!token) {
      return {};
    }
    return {
      Authorization: `Bearer ${token}`,
    };
  }, [token]);

  const checkAuthStatus = useCallback(async () => {
    try {
      const response = await client.get('/auth/status', { headers });
      setIsAuthenticated(Boolean(response.data.authenticated));
      setBungieLinked(Boolean(response.data.bungie_linked));
      if (Object.prototype.hasOwnProperty.call(response.data, 'api_key_ok')) {
        setApiKeyOk(Boolean(response.data.api_key_ok));
        setApiKeyMasked(response.data.api_key_masked || '');
        setApiKeyError(response.data.api_key_error || '');
      }
    } catch (err) {
      console.error('Failed to check auth status:', err);
      setIsAuthenticated(false);
      setBungieLinked(false);
      setApiKeyOk(true);
    }
  }, [headers]);

  React.useEffect(() => {
    checkAuthStatus();
  }, [checkAuthStatus]);

  // Listen for token set in another window (OAuth popup safety net)
  React.useEffect(() => {
    const onStorage = (e) => {
      if (e.key === 'ghost-companion-token' && e.newValue) {
        try {
          const t = JSON.parse(e.newValue);
          if (t) {
            setToken(t);
            setIsAuthenticated(true);
            setAuthLoading(false);
          }
        } catch (_) {}
      }
    };
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, [setToken]);

  // On window focus, try to pick up a token stored by the popup
  React.useEffect(() => {
    const onFocus = () => {
      try {
        const raw = localStorage.getItem('ghost-companion-token');
        if (raw && !token) {
          const t = JSON.parse(raw);
          if (t) {
            setToken(t);
            setIsAuthenticated(true);
            setAuthLoading(false);
          }
        }
      } catch (_) {}
    };
    window.addEventListener('focus', onFocus);
    return () => window.removeEventListener('focus', onFocus);
  }, [token, setToken]);

  // Load available models from backend
  React.useEffect(() => {
    client.get('/models').then((res) => {
      if (res?.data) setAvailableModels(res.data);
    }).catch(() => {});
  }, []);

  // Load available personas
  React.useEffect(() => {
    client.get('/personas').then((res) => {
      if (res?.data?.personas) setAvailablePersonas(res.data.personas);
    }).catch(() => {});
  }, []);

  // Load voices
  React.useEffect(() => {
    client.get('/voices').then((res) => {
      if (res?.data?.voices) setAvailableVoices(res.data.voices);
    }).catch(() => {});
  }, []);

  React.useEffect(() => {
    if (!speakEnabled || !availableVoices.length) {
      return;
    }
    const personaVoice = availableVoices.find(
      (voice) => Array.isArray(voice.personas) && voice.personas.includes(persona)
    );
    const curatedDefault = availableVoices.find(
      (voice) => typeof voice.name === 'string' && /ghost|vergil/i.test(voice.name)
    );
    const targetVoice = personaVoice || curatedDefault;
    if (!targetVoice) {
      return;
    }
    const selectedVoiceValid = availableVoices.some((voice) => voice.key === selectedVoice);
    const allowOverride =
      !selectedVoice ||
      selectedVoice === 'system' ||
      !selectedVoiceValid ||
      (autoVoiceRef.current && autoVoiceRef.current === selectedVoice);
    if (allowOverride && targetVoice.key !== selectedVoice) {
      applyVoiceSelection(targetVoice.key, true);
    }
  }, [speakEnabled, persona, availableVoices, selectedVoice, applyVoiceSelection]);

  // Enumerate microphones (labels require permission). Users can click refresh in the drawer to grant.
  const refreshMics = React.useCallback(async (requestAccess = false) => {
    if (typeof window !== 'undefined' && window.isSecureContext === false) {
      setMicDevices([]);
      setMicDetectionError('Microphone access requires HTTPS/localhost. Use the desktop app or serve over https://.');
      return;
    }
    if (typeof navigator === 'undefined') {
      setMicDevices([]);
      setMicDetectionError('Navigator is unavailable in this environment.');
      return;
    }
    if (!navigator.mediaDevices) {
      setMicDevices([]);
      setMicDetectionError('Browser does not expose mediaDevices. Update to a modern browser or desktop build.');
      return;
    }
    if (!navigator.mediaDevices.getUserMedia) {
      setMicDevices([]);
      setMicDetectionError('getUserMedia is missing. Browser blocked microphone APIs.');
      return;
    }
    let tempStream;
    try {
      setMicDetectionError('');
      if (requestAccess && navigator.mediaDevices.getUserMedia) {
        tempStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      } else if (navigator.permissions?.query) {
        try {
          const status = await navigator.permissions.query({ name: 'microphone' });
          if (status.state === 'denied') {
            setMicDevices([]);
            setMicDetectionError('Microphone permission denied. Update your browser settings to allow access.');
            return;
          }
        } catch {
          // permissions API optional
        }
      }
      if (!navigator.mediaDevices.enumerateDevices) {
        throw new Error('enumerateDevices unavailable');
      }
      const list = await navigator.mediaDevices.enumerateDevices();
      const mics = list
        .filter((d) => d.kind === 'audioinput')
        .map((d, idx) => {
          let label = d.label || '';
          if (!label) label = `Microphone ${idx + 1}`;
          if (d.deviceId === 'default' && label) label = `Default — ${label}`;
          if (d.deviceId === 'communications' && label) label = `Comms — ${label}`;
          return { id: d.deviceId, label };
        });
      setMicDevices(mics);
      if (!mics.length) {
        setMicDetectionError('No microphones detected. Connect a device and click Grant Access.');
      } else {
        setMicDetectionError('');
        if (!selectedMicId) {
          setSelectedMicId(mics[0].id || '');
        }
      }
    } catch (e) {
      console.warn('Failed to enumerate microphones:', e);
      let message = 'Unable to access microphones. Check permissions and try again.';
      if (e?.name === 'NotAllowedError' || e?.name === 'SecurityError') {
        message = 'Microphone permission blocked. Allow access to speak with Ghost.';
      } else if (e?.name === 'NotFoundError') {
        message = 'No microphone hardware is available. Connect a microphone.';
      }
      setMicDevices([]);
      setMicDetectionError(message);
    } finally {
      if (tempStream) {
        try {
          tempStream.getTracks().forEach((track) => track.stop());
        } catch {}
      }
    }
  }, [selectedMicId, setSelectedMicId]);

  React.useEffect(() => { refreshMics(false); }, [refreshMics]);

  React.useEffect(() => {
    if (typeof navigator === 'undefined' || !navigator.mediaDevices) {
      return undefined;
    }
    const api = navigator.mediaDevices;
    const handler = () => {
      refreshMics(false);
    };
    if (api.addEventListener) {
      api.addEventListener('devicechange', handler);
      return () => {
        api.removeEventListener('devicechange', handler);
      };
    }
    const previous = api.ondevicechange;
    api.ondevicechange = handler;
    return () => {
      if (api.ondevicechange === handler) {
        api.ondevicechange = previous || null;
      }
    };
  }, [refreshMics]);

  const applyServerMicDevices = useCallback((payload) => {
    if (payload && Array.isArray(payload.devices) && payload.devices.length) {
      const mapped = payload.devices.map((dev, idx) => {
        const index = typeof dev.index === 'number' ? dev.index : idx;
        const name = (typeof dev.name === 'string' && dev.name.trim()) ? dev.name.trim() : `Device ${index + 1}`;
        return {
          id: `server:${index}`,
          label: `${name} (desktop)`,
          deviceIndex: index,
          source: 'server',
        };
      });
      setServerMicDevices(mapped);
    } else {
      setServerMicDevices([]);
    }
  }, []);

  React.useEffect(() => {
    client.get('/diagnostics/audio', { headers }).then((res) => {
      if (res?.data) {
        applyServerMicDevices(res.data);
      }
    }).catch(() => {});
  }, [headers, applyServerMicDevices]);

  const runMicDiagnostics = useCallback(async () => {
    setMicDiagLoading(true);
    const result = {
      browser: null,
      browserError: null,
      server: null,
      serverError: null,
      timestamp: new Date().toISOString(),
    };
    try {
      const browserInfo = {
        timestamp: new Date().toISOString(),
        secureContext: typeof window !== 'undefined' ? window.isSecureContext : null,
        protocol: typeof window !== 'undefined' ? window.location.protocol : null,
        host: typeof window !== 'undefined' ? window.location.host : null,
        hasNavigator: typeof navigator !== 'undefined',
        hasMediaDevices: typeof navigator !== 'undefined' && !!navigator.mediaDevices,
        permission: null,
        devices: [],
        error: null,
        userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : null,
      };
      if (typeof navigator === 'undefined') {
        browserInfo.error = 'Navigator unavailable';
      } else {
        if (navigator.permissions?.query) {
          try {
            const status = await navigator.permissions.query({ name: 'microphone' });
            browserInfo.permission = status.state;
          } catch (err) {
            browserInfo.permission = 'unknown';
            browserInfo.error = `Permissions API error: ${err?.message || err}`;
          }
        }
        if (navigator.mediaDevices?.enumerateDevices) {
          const list = await navigator.mediaDevices.enumerateDevices();
          browserInfo.devices = list
            .filter((d) => d.kind === 'audioinput')
            .map((d, idx) => ({
              id: d.deviceId,
              label: d.label || `Microphone ${idx + 1}`,
              groupId: d.groupId,
            }));
        } else if (!browserInfo.error) {
          browserInfo.error = 'enumerateDevices unavailable';
        }
      }
      result.browser = browserInfo;
    } catch (err) {
      result.browserError = err?.message || 'Browser diagnostics failed';
    }
    try {
      const resp = await client.get('/diagnostics/audio', { headers });
      result.server = resp.data;
      applyServerMicDevices(resp.data);
    } catch (err) {
      result.serverError = err?.response?.data?.detail || err?.message || 'Audio diagnostics endpoint unavailable';
    } finally {
      setMicDiagResult(result);
      setMicDiagLoading(false);
    }
  }, [headers, applyServerMicDevices]);

  const toggleMicDiag = useCallback(() => {
    setMicDiagOpen((prev) => !prev);
  }, []);

  React.useEffect(() => {
    if (micDiagOpen && !micDiagResult && !micDiagLoading) {
      runMicDiagnostics();
    }
  }, [micDiagOpen, micDiagResult, micDiagLoading, runMicDiagnostics]);

  // Do NOT auto-open OAuth popup on mount.
  // Many webviews/browsers block programmatic popups without a user gesture,
  // which can cause navigation to replace the main window and get stuck on
  // the callback page. Users should click the "Sign in with Bungie" button.
  React.useEffect(() => {
    // Intentionally left blank (no auto auth).
  }, []);

  const saveApiKey = useCallback(async () => {
    if (!apiKeyInput.trim()) return;
    setApiKeySaving(true);
    try {
      const res = await client.post('/auth/key', { api_key: apiKeyInput.trim() }, { headers });
      if (res.data && res.data.ok) {
        setApiKeyInput('');
        await checkAuthStatus();
      } else {
        setApiKeyError((res.data && res.data.error) || 'API key not accepted');
      }
    } catch (e) {
      setApiKeyError(e?.response?.data?.error || e.message || 'Failed to set API key');
    } finally {
      setApiKeySaving(false);
    }
  }, [apiKeyInput, headers, checkAuthStatus]);

  const handleAuthenticate = useCallback(async () => {
    setAuthLoading(true);
    try {
      const response = await client.get('/oauth/authorize');
      const authUrl = response.data.authorization_url;

      // Open OAuth URL in new window
      const authWindow = window.open(
        authUrl,
        'bungie-auth',
        'width=600,height=700,left=' + (window.screenX + (window.outerWidth - 600) / 2) + ',top=' + (window.screenY + (window.outerHeight - 700) / 2)
      );

      if (!authWindow) {
        throw new Error('Popup was blocked. Please allow popups for this site.');
      }

      // No need for polling - we'll handle the auth completion via postMessage
      const timeoutId = setTimeout(() => {
        if (!authWindow.closed) {
          authWindow.close();
        }
        setAuthLoading(false);
      }, 300000); // 5 minute timeout

      // Clear timeout when component unmounts
      return () => {
        clearTimeout(timeoutId);
        if (authWindow && !authWindow.closed) {
          authWindow.close();
        }
      };
    } catch (err) {
      console.error('Failed to start authentication:', err);
      setError(err.message || 'Failed to start authentication');
      setAuthLoading(false);
    }
  }, []);

  // Handle OAuth callback from postMessage (popup flow)
  React.useEffect(() => {
    const handleMessage = async (event) => {
      // Allow messages from any localhost/127.0.0.1 (any port, http/https)
      const isLocalOrigin = /^https?:\/\/(localhost|127\.0\.0\.1)(:\\d+)?$/.test(event.origin);
      if (!isLocalOrigin) return;
      
      if (event.data.type === 'oauth_callback' || event.data.type === 'bungie_oauth') {
        const code = event.data.code;
        if (code) {
          try {
            // Make sure to send the code in the correct format expected by the server
            const response = await client.post('/oauth/callback', { code: code });
            const { token } = response.data;
            if (token) {
              setToken(token);
              setIsAuthenticated(true);
              setBungieLinked(true);
              setAuthLoading(false);
              
              // Notify popup that auth is complete
              if (event.source) {
                event.source.postMessage({ type: 'oauth_complete' }, '*');
              }
            }
          } catch (err) {
            console.error('Failed to complete authentication:', err, err.response?.data);
            setError(err.response?.data?.detail || 'Authentication failed. Please try again.');
            setAuthLoading(false);
            
            // Close popup even on error after a short delay
            setTimeout(() => {
              if (event.source) {
                event.source.postMessage({ type: 'oauth_complete' }, '*');
              }
            }, 2000);
          }
        }
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  // Handle OAuth callback if we're on the callback page (fallback)
  React.useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const error = urlParams.get('error');

    if (code) {
      // Send the authorization code to the backend
      client.post('/oauth/callback', { code: code })
        .then((response) => {
          const { token } = response.data;
          if (token) {
            setToken(token);
            setIsAuthenticated(true);
            // If we're in a popup window, close it
            if (window.opener) {
              window.close();
            }
          }
          // Clear the URL parameters
          window.history.replaceState({}, document.title, window.location.pathname);
        })
        .catch((err) => {
          console.error('Failed to complete authentication:', err, err.response?.data);
          setError(err.response?.data?.detail || 'Authentication failed. Please try again.');
          // If we're in a popup window, close it on error too
          if (window.opener) {
            window.close();
          }
        });
    } else if (error) {
      console.error('OAuth error:', error);
      setError('Authentication failed. Please try again.');
      // If we're in a popup window, close it
      if (window.opener) {
        window.close();
      }
      // Clear the URL parameters
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  // Check for stored token on app load
  React.useEffect(() => {
    if (token) {
      // Verify token is still valid
      client.get('/auth/status', {
        headers: { Authorization: `Bearer ${token}` }
      })
        .then(() => {
          setIsAuthenticated(true);
        })
        .catch(() => {
          setToken('');
        });
    }
  }, [token]);

  // Check auth status on component mount
  React.useEffect(() => {
    checkAuthStatus();
  }, [checkAuthStatus]);

  const fetchConversations = useCallback(async () => {
    try {
      const res = await client.get('/conversations', { headers });
      setServerConversations(res.data.conversations || []);
    } catch (e) {
      // ignore if unauthorized
    }
  }, [headers]);

  React.useEffect(() => {
    if (!token) return;
    fetchConversations();
  }, [token, fetchConversations]);

  const filteredConversations = React.useMemo(() => {
    if (!chatSearch.trim()) return serverConversations || [];
    const q = chatSearch.toLowerCase();
    return (serverConversations || []).filter((c) => (
      (c.name || '').toLowerCase().includes(q) || (c.last_message || '').toLowerCase().includes(q)
    ));
  }, [serverConversations, chatSearch]);

  const closeSidebar = useCallback(() => {
    const active = document.activeElement;
    if (active && typeof active.blur === 'function') {
      active.blur();
    }
    setSidebarOpen(false);
  }, []);

  const saveCurrentChat = useCallback(async () => {
    const name = prompt('Save conversation as:', new Date().toLocaleString());
    if (!name) return;
    try {
      const id = activeConversationId || (await client.post('/conversations', { name, provider }, { headers })).data.id;
      await client.patch(`/conversations/${id}`, { name }, { headers });
      setActiveConversationId(id);
      setSessionId(id);
      fetchConversations();
    } catch (e) {
      setError('Failed to save chat');
    }
  }, [headers, provider, activeConversationId, setActiveConversationId, fetchConversations]);

  const loadConversation = useCallback((id) => {
    const convo = (savedConversations || []).find((c) => c.id === id);
    if (convo) {
      setMessages(convo.messages || []);
      setError('');
      setIsLoading(false);
      setSessionId('');
      setProvider(convo.provider || provider);
    }
  }, [savedConversations, provider]);

  const deleteConversation = useCallback(async (id) => {
    try {
      await client.delete(`/conversations/${id}`, { headers });
      setServerConversations((prev) => (prev || []).filter((c) => c.id !== id));
    } catch (e) {
      // Fallback to local delete if server fails
      setSavedConversations((prev) => prev.filter((c) => c.id !== id));
    }
  }, [headers, setServerConversations, setSavedConversations]);

  const handleProviderChange = useCallback((value) => {
    setProvider(value);
    if (!activeConversationId) return;
    (async () => {
      try {
        await client.patch(`/conversations/${activeConversationId}`, { provider: value }, { headers });
        if (serverConversations && serverConversations.length) {
          setServerConversations((prev) => (prev || []).map((c) => (c.id === activeConversationId ? { ...c, provider: value } : c)));
        }
      } catch (e) {
        setSavedConversations((prev) => (prev || []).map((c) => (c.id === activeConversationId ? { ...c, provider: value } : c)));
      }
    })();
  }, [activeConversationId, headers, setProvider, serverConversations, setServerConversations, setSavedConversations]);

  const renameConversation = useCallback((id) => {
    const name = prompt('Rename conversation');
    if (!name) return;
    (async () => {
      try {
        await client.patch(`/conversations/${id}`, { name }, { headers });
        if (serverConversations && serverConversations.length) {
          setServerConversations((prev) => (prev || []).map((c) => (c.id === id ? { ...c, name } : c)));
        }
      } catch (e) {
        setSavedConversations((prev) => (prev || []).map((c) => (c.id === id ? { ...c, name } : c)));
      }
    })();
  }, [headers, serverConversations, setServerConversations, setSavedConversations]);

  const handleSendMessage = useCallback(
    async (input) => {
      const trimmed = input.trim();
      if (!trimmed) {
        return;
      }

      const userMessage = {
        id: createMessageId(),
        role: 'user',
        content: trimmed,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setError('');

      try {
        // Create placeholder assistant message
        const assistantId = createMessageId();
        setMessages((prev) => [...prev, { id: assistantId, role: 'assistant', content: '', timestamp: new Date().toISOString() }]);

        const params = new URLSearchParams();
        params.set('message', trimmed);
        if (provider) params.set('provider', provider);
        if (provider === 'ollama' && ollamaModel) params.set('model', ollamaModel);
        if (persona) params.set('persona', persona);
        if (speakEnabled) params.set('speak', '1');
        if (selectedVoice) params.set('voice', selectedVoice);
        if (sessionId) params.set('session_id', sessionId);

        const resp = await fetch(`${API_BASE_URL}/chat/stream?${params.toString()}`, { headers });
        const convId = resp.headers.get('X-Conversation-Id');
        if (convId) {
          setSessionId(convId);
          setActiveConversationId(convId);
        }
        const reader = resp.body?.getReader();
        const decoder = new TextDecoder();
        while (reader) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, { stream: true });
          setMessages((prev) => prev.map((m) => (m.id === assistantId ? { ...m, content: (m.content || '') + chunk } : m)));
        }
        // Refresh list from server
        try { await client.get('/conversations', { headers }).then((res) => setServerConversations(res.data.conversations || [])); } catch {}
      } catch (err) {
        let friendly = 'Something went wrong while contacting the Ghost. Please try again.';
        if (err.response) {
          if (err.response.status === 401) {
            friendly = 'Unauthorized: please check your OAuth token.';
          } else if (err.response.data?.detail) {
            friendly = err.response.data.detail;
          } else if (err.response.status >= 500) {
            friendly = 'The Ghost is experiencing issues. Please wait a moment and try again.';
          }
        } else if (err.request) {
          friendly = 'Network error: unable to reach the Ghost. Is the backend running?';
        }
        setError(friendly);
      } finally {
        setIsLoading(false);
      }
    },
    [headers, sessionId, provider, ollamaModel, persona, speakEnabled]
  );

  const startNewChat = useCallback(async () => {
    try {
      const res = await client.post('/conversations', { name: 'New Chat', provider }, { headers });
      const id = res.data.id;
      setActiveConversationId(id);
      setSessionId(id);
      setMessages([]);
      setError('');
    } catch (e) {
      // If server unavailable, just reset local state
      setActiveConversationId('');
      setSessionId('');
      setMessages([]);
      setError('');
    }
  }, [headers, provider, setActiveConversationId]);

  const openConversation = useCallback(async (id) => {
    try {
      const res = await client.get(`/conversations/${id}`, { headers });
      const msgs = (res.data.messages || []).map((m) => ({ id: m.id, role: m.role, content: m.content, timestamp: m.ts }));
      setActiveConversationId(id);
      setMessages(msgs);
      const conv = (serverConversations || []).find((c) => c.id === id);
      if (conv?.provider) setProvider(conv.provider);
      setSessionId(id);
      setError('');
    } catch (e) {
      setError('Failed to load conversation');
    }
  }, [headers, serverConversations, setProvider]);

  return (
    <div className={`app app--with-sidebar ${emptyState ? 'is-empty' : ''}`}>
      <TopBar onHamburger={() => setSidebarOpen(true)} />
      <Sidebar
        open={sidebarOpen}
        onClose={closeSidebar}
        conversations={filteredConversations}
        activeId={activeConversationId}
        onNew={startNewChat}
        onOpen={(id) => { closeSidebar(); openConversation(id); }}
        onDelete={deleteConversation}
        onRename={renameConversation}
        search={chatSearch}
        onSearch={setChatSearch}
        provider={provider}
        onProviderChange={handleProviderChange}
        ollamaModel={ollamaModel}
        onOllamaModelChange={setOllamaModel}
        ollamaModels={(availableModels.ollama || [])}
        persona={persona}
        onPersonaChange={setPersona}
        personas={availablePersonas}
        speakEnabled={speakEnabled}
        onSpeakChange={setSpeakEnabled}
        micDevices={combinedMicDevices}
        selectedMicId={selectedMicId}
        onMicChange={setSelectedMicId}
        onRefreshMics={() => refreshMics(true)}
        micDetectionError={micDetectionError}
        micDiagOpen={micDiagOpen}
        onToggleMicDiag={toggleMicDiag}
        onRunMicDiagnostics={runMicDiagnostics}
        micDiagLoading={micDiagLoading}
        micDiagResult={micDiagResult}
      />
      {!token && (
        <div className="auth-gate">
          <div className="auth-gate__card">
            <h2>Sign in with Bungie</h2>
            <p>Sign in to your Bungie account to link your Guardian and chat.</p>
            <button className="auth-button" onClick={handleAuthenticate} disabled={authLoading}>
              {authLoading ? 'Opening Bungie...' : 'Sign in with Bungie'}
            </button>
          </div>
        </div>
      )}
      <aside className="sidebar">
        <div className="sidebar__header">
          <button className="sidebar__new" onClick={startNewChat}>+ New Chat</button>
        </div>
        <div className="sidebar__list">
          {((serverConversations || []).length === 0) && (
            <div className="sidebar__empty">No saved chats yet.</div>
          )}
          {(serverConversations || []).map((c) => (
            <div key={c.id} className={`sidebar__item ${activeConversationId === c.id ? 'active' : ''}`}>
              <button className="sidebar__item-btn" onClick={() => openConversation(c.id)} title={c.name}>
                <span className="sidebar__item-name">{c.name}</span>
                <span className="sidebar__item-provider">{c.provider}</span>
              </button>
              <div className="sidebar__item-actions">
                <button onClick={() => renameConversation(c.id)} title="Rename">✎</button>
                <button onClick={() => deleteConversation(c.id)} title="Delete">🗑</button>
              </div>
            </div>
          ))}
        </div>
      </aside>
      {/* Header removed for minimalist UI */}

      {!emptyState ? (
        <>
          <main className="app__main">
            {!bungieLinked && (
              <div className="app__error" role="alert">Your Bungie account is not linked. Authenticate to enable Ghost to manage inventory and retrieve Destiny data.</div>
            )}
            {/* Save Chat removed for minimalist UI */}
            <ChatWindow
              messages={messages}
              isLoading={isLoading}
              onRegenerate={(msg) => {
                const idx = messages.findIndex((m) => m.id === msg.id);
                for (let i = idx - 1; i >= 0; i--) {
                  if (messages[i].role === 'user') {
                    handleSendMessage(messages[i].content);
                    break;
                  }
                }
              }}
            />
            {/* Session ID control removed */}
            {error && <div className="app__error">{error}</div>}
          </main>

          <footer className="app__footer">
            <MessageInput
              onSend={handleSendMessage}
              disabled={isLoading || !isAuthenticated}
              speakEnabled={speakEnabled}
              onSpeakChange={setSpeakEnabled}
              selectedVoice={selectedVoice}
              onVoiceChange={handleVoiceChange}
              availableVoices={availableVoices}
              micDeviceId={selectedMicId}
              micDetectionError={micDetectionError}
              serverMicAvailable={serverMicDevices.length > 0}
              serverMicDefaultIndex={(serverMicDevices[0] && serverMicDevices[0].deviceIndex) ?? null}
            />
            {isLoading && <LoadingSpinner />}
          </footer>
        </>
      ) : (
        <main className="hero-empty" aria-label="Empty state">
          <h2>Hey guardian, how can i help?</h2>
          <div className="hero-composer">
            <MessageInput
              onSend={handleSendMessage}
              disabled={isLoading || !isAuthenticated}
              speakEnabled={speakEnabled}
              onSpeakChange={setSpeakEnabled}
              selectedVoice={selectedVoice}
              onVoiceChange={handleVoiceChange}
              availableVoices={availableVoices}
              micDeviceId={selectedMicId}
              micDetectionError={micDetectionError}
              serverMicAvailable={serverMicDevices.length > 0}
              serverMicDefaultIndex={(serverMicDevices[0] && serverMicDevices[0].deviceIndex) ?? null}
            />
          </div>
        </main>
      )}
    </div>
  );
}

export default App;
