import { Capacitor } from '@capacitor/core';

if (Capacitor.isNativePlatform() && !/^https:\/\//.test(import.meta.env.VITE_API_URL || '')) {
  throw new Error('Native builds require VITE_API_URL pointing to an HTTPS hosted server');
}

export const API_BASE_URL = (import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000').replace(/\/+$/, '');
