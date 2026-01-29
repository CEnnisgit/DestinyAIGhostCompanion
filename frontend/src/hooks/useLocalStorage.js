import { useEffect, useState } from 'react';

const useLocalStorage = (key, defaultValue) => {
  const [storedValue, setStoredValue] = useState(() => {
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
    try {
      if (storedValue === undefined || storedValue === '') {
        window.localStorage.removeItem(key);
      } else {
        window.localStorage.setItem(key, JSON.stringify(storedValue));
      }
    } catch (error) {
      console.warn('Failed to write to localStorage', error);
    }
  }, [key, storedValue]);

  return [storedValue, setStoredValue];
};

export default useLocalStorage;
