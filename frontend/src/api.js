import { Capacitor } from '@capacitor/core';
import { SecureStorage } from '@aparajita/capacitor-secure-storage';
import axios from 'axios';
import { API_BASE_URL } from './config';
let secureSecrets = {};
let credentialLoad;
let credentialWrites = Promise.resolve();
export function setSecureSecrets(values) { secureSecrets = values; }
export function settings() {
  try { return {...JSON.parse(localStorage.getItem('ghost-settings') || '{}'), ...secureSecrets}; } catch { return {}; }
}
export function credentialHeaders() {
  const s = settings();
  return Object.fromEntries(Object.entries({ 'X-AI-Provider': s.provider || 'ollama', 'X-AI-Model': s.model, 'X-AI-Key': s.key, 'X-AI-Base-URL': s.baseURL, 'X-Bungie-API-Key': s.bungieKey, 'X-Bungie-Client-ID': s.clientId }).filter(([,v]) => v));
}
export const client = axios.create({ baseURL: API_BASE_URL, timeout: 60000, withCredentials: true });
client.interceptors.request.use(async config => {
  if (!['/config', '/local/secrets'].includes(config.url)) {
    if (credentialLoad) await credentialLoad.catch(error => {
      if (Capacitor.isNativePlatform()) throw error;
    });
    Object.assign(config.headers, credentialHeaders());
  }
  return config;
});
export function apiFetch(url, options = {}) {
  return fetch(url, { ...options, credentials: 'include', headers: { ...credentialHeaders(), ...options.headers } });
}

export function loadCredentialStorage() {
  if (!credentialLoad) credentialLoad = initializeCredentialStorage();
  return credentialLoad;
}
async function initializeCredentialStorage() {
  if (Capacitor.isNativePlatform()) {
    const old = settings();
    const migrated = {};
    for (const field of ['key', 'bungieKey']) {
      migrated[field] = (await SecureStorage.get(field)) ?? old[field] ?? '';
      await SecureStorage.set(field, migrated[field], false, false);
    }
    setSecureSecrets(migrated);
    delete old.key; delete old.bungieKey;
    localStorage.setItem('ghost-settings', JSON.stringify(old));
    return true;
  }
  const {data} = await client.get('/config');
  if (data.mode === 'desktop' && data.keyring_available) {
    const {data: stored} = await client.get('/local/secrets');
    const old = settings();
    const migrated = {key: stored.key || old.key || '', bungieKey: stored.bungieKey || old.bungieKey || ''};
    await client.put('/local/secrets', migrated);
    setSecureSecrets(migrated);
    delete old.key; delete old.bungieKey;
    localStorage.setItem('ghost-settings', JSON.stringify(old));
    return true;
  }
  return false;
}

export function saveCredential(field, value) {
  credentialWrites = credentialWrites.catch(() => {}).then(async () => {
    if (Capacitor.isNativePlatform()) await SecureStorage.set(field, value, false, false);
    else await client.put('/local/secrets', {[field]: value});
    secureSecrets = {...secureSecrets, [field]: value};
  });
  return credentialWrites;
}
export function waitCredentialWrites() { return credentialWrites; }
