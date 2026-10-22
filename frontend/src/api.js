import axios from 'axios';
import { API_BASE_URL } from './config';
export function settings() {
  try { return JSON.parse(localStorage.getItem('ghost-settings') || '{}'); } catch { return {}; }
}
export function credentialHeaders() {
  const s = settings();
  return Object.fromEntries(Object.entries({ 'X-AI-Provider': s.provider || 'ollama', 'X-AI-Model': s.model, 'X-AI-Key': s.key, 'X-AI-Base-URL': s.baseURL, 'X-Bungie-API-Key': s.bungieKey, 'X-Bungie-Client-ID': s.clientId }).filter(([,v]) => v));
}
export const client = axios.create({ baseURL: API_BASE_URL, timeout: 60000, withCredentials: true });
client.interceptors.request.use(config => { Object.assign(config.headers, credentialHeaders()); return config; });
export function apiFetch(url, options = {}) {
  return fetch(url, { ...options, credentials: 'include', headers: { ...credentialHeaders(), ...options.headers } });
}
