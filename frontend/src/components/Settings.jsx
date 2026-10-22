import React, { useState, useEffect } from 'react';
import { client, settings, loadCredentialStorage, saveCredential, waitCredentialWrites } from '../api';
export default function Settings({ onClose }) {
  const [value, setValue] = useState(settings);
  const [result, setResult] = useState('');
  const [secure, setSecure] = useState(false);
  const [ready, setReady] = useState(false);
  useEffect(() => { loadCredentialStorage().then(ok => { setSecure(ok); setValue(settings()); }).catch(() => setResult('OS keyring unavailable; browser storage is in use.')).finally(() => setReady(true)); }, []);
  const update = async (field, v) => {
    const next = {...value, [field]: v}; setValue(next);
    const stored = {...next};
    if (secure) { delete stored.key; delete stored.bungieKey; }
    localStorage.setItem('ghost-settings', JSON.stringify(stored));
    if (secure) {
      if (field === 'key' || field === 'bungieKey') {
        try {
          await saveCredential(field, v);
        } catch { setResult('Could not save to OS keyring. Please retry.'); }
      }
    }
  };
  return <div role="dialog" aria-modal="true" aria-label="Settings" style={{position:'fixed', inset:'5%', zIndex:10000, background:'#171b25', color:'white', padding:24, overflow:'auto'}}>
    <h2>Settings</h2><p><strong>{secure ? 'Credentials are saved in the OS keyring on this device.' : 'Warning: credentials stay in localStorage on this device. Anyone with access to this browser can read them. Use a trusted server over HTTPS.'}</strong></p>
    <label>AI provider <select disabled={!ready} value={value.provider || 'ollama'} onChange={e => update('provider', e.target.value)}>{['xai','openai','anthropic','openai_compatible','ollama','local'].map(p => <option key={p}>{p}</option>)}</select></label>
    {[['model','Model'],['baseURL','Base URL (http/https)'],['key','AI API key'],['bungieKey','Bungie API key'],['clientId','Bungie client ID']].map(([field,label]) => <p key={field}><label>{label} <input disabled={!ready} type={field.toLowerCase().includes('key') ? 'password' : 'text'} value={value[field] || ''} onChange={e => update(field,e.target.value)} autoComplete="off" /></label></p>)}
    <button onClick={async () => { setResult('Testing…'); try { await waitCredentialWrites(); const r = await client.post('/ai/test'); setResult(r.data.ok ? 'Connection successful' : r.data.error); } catch { setResult('Connection failed'); } }}>Test connection</button><p role="status">{result}</p><button onClick={onClose}>Close</button>
  </div>;
}
