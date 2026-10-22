import { Capacitor } from '@capacitor/core';
import { SecureStorage } from '@aparajita/capacitor-secure-storage';
import { useEffect, useState } from 'react';

const useLocalStorage = (key, defaultValue) => {
  const nativeSecret = Capacitor.isNativePlatform() && key === 'ghost-companion-token';
  const [nativeReady, setNativeReady] = useState(!nativeSecret);
  const [storedValue, setStoredValue] = useState(() => {
    if (nativeSecret) return defaultValue;
    try {
      const item = window.localStorage.getItem(key);
      if (item === null) return defaultValue;
      try {
        return JSON.parse(item);
      } catch (parseErr) {
        // Backward-compat: accept plain strings (e.g., raw JWT tokens)
        // If it looks like a JWT (a.b.c) or any non-JSON scalar, return as-is.
        if (/^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$/.test(item) || typeof item === 'string') {
          return item;
        }
        throw parseErr;
      }
    } catch (error) {
      console.warn('Failed to read from localStorage', error);
      return defaultValue;
    }
  });

  useEffect(() => {
    if (!nativeSecret) return;
    let mounted = true;
    SecureStorage.get(key).then(async value => {
      const legacy = window.localStorage.getItem(key);
      const restored = value ?? (legacy ? JSON.parse(legacy) : defaultValue);
      if (restored) await SecureStorage.set(key, restored, false, false);
      window.localStorage.removeItem(key);
      if (mounted) { setStoredValue(restored); setNativeReady(true); }
    }).catch(error => console.error('Secure storage unavailable', error));
    return () => { mounted = false; };
  }, [key, nativeSecret]);

  useEffect(() => {
    if (nativeSecret) {
      if (nativeReady) {
        const write = storedValue ? SecureStorage.set(key, storedValue, false, false) : SecureStorage.remove(key);
        write.catch(error => console.error('Secure storage write failed', error));
      }
      return;
    }
    try {
      if (storedValue === undefined || storedValue === '') {
        window.localStorage.removeItem(key);
      } else {
        window.localStorage.setItem(key, JSON.stringify(storedValue));
      }
    } catch (error) {
      console.warn('Failed to write to localStorage', error);
    }
  }, [key, storedValue, nativeSecret, nativeReady]);

  return [storedValue, setStoredValue];
};

export default useLocalStorage;
