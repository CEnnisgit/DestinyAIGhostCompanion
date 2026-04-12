import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '';
const client = axios.create({ baseURL: API_BASE_URL, timeout: 15000 });

const TokenInput = ({ token, onTokenChange }) => {
  const [localToken, setLocalToken] = useState(token ?? '');
  const [isEditing, setIsEditing] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = (event) => {
    event.preventDefault();
    onTokenChange(localToken.trim());
    setIsEditing(false);
  };

  const handleReset = () => {
    setLocalToken('');
    onTokenChange('');
  };

  const signup = async () => {
    setBusy(true);
    setError('');
    try {
      const res = await client.post('/auth/signup', { email, password });
      setLocalToken(res.data.token);
      onTokenChange(res.data.token);
    } catch (e) {
      setError(e?.response?.data?.detail || 'Sign up failed');
    } finally {
      setBusy(false);
    }
  };

  const login = async () => {
    setBusy(true);
    setError('');
    try {
      const res = await client.post('/auth/login', { email, password });
      setLocalToken(res.data.token);
      onTokenChange(res.data.token);
    } catch (e) {
      setError(e?.response?.data?.detail || 'Login failed');
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="token-input" onSubmit={handleSubmit}>
      <label className="token-input__label">Account</label>
      <div className="token-input__controls" style={{ gap: '0.5rem' }}>
        <input
          id="email"
          type="email"
          value={email}
          placeholder="Email"
          onChange={(e) => setEmail(e.target.value)}
        />
        <input
          id="password"
          type="password"
          value={password}
          placeholder="Password"
          onChange={(e) => setPassword(e.target.value)}
        />
        <div className="token-input__buttons">
          <button type="button" onClick={signup} disabled={busy || !email || !password}>Sign Up</button>
          <button type="button" onClick={login} disabled={busy || !email || !password}>Log In</button>
        </div>
      </div>

      <label htmlFor="token" className="token-input__label" style={{ marginTop: '0.5rem' }}>
        Token (JWT)
      </label>
      <div className="token-input__controls">
        <input
          id="token"
          type={isEditing ? 'text' : 'password'}
          value={localToken}
          placeholder="Paste your OAuth token"
          onChange={(event) => {
            setLocalToken(event.target.value);
            setIsEditing(true);
          }}
        />
        <div className="token-input__buttons">
          <button type="submit">Save</button>
          <button type="button" className="token-input__clear" onClick={handleReset}>
            Clear
          </button>
        </div>
      </div>
      {error && <div className="app__error" style={{ marginTop: '0.5rem' }}>{error}</div>}
    </form>
  );
};

export default TokenInput;
