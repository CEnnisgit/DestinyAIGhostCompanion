import React from 'react';

const Sidebar = ({ open, onClose, conversations, activeId, onNew, onOpen, onDelete, onRename, search, onSearch, provider, onProviderChange, ollamaModel, onOllamaModelChange, ollamaModels, persona, onPersonaChange, personas, speakEnabled, onSpeakChange, micDevices, selectedMicId, onMicChange, onRefreshMics, micDetectionError, micDiagOpen, onToggleMicDiag, onRunMicDiagnostics, micDiagLoading, micDiagResult }) => {
  return (
    <>
      {open && <div className="drawer-backdrop" onClick={onClose} />}
      <aside className={`drawer ${open ? 'drawer--open' : ''}`} aria-label="Conversations">
        <div className="drawer__header">
          <button className="drawer__new" onClick={onNew}>+ New Chat</button>
          <button className="topbar__hamburger" onClick={onClose} aria-label="Close">✕</button>
        </div>
        <div className="drawer__controls provider-select-group" style={{padding: '0 .75rem'}}>
          <label htmlFor="provider">Provider</label>
          <select id="provider" value={provider} onChange={(e)=>onProviderChange && onProviderChange(e.target.value)}>
            <option value="ollama">Ollama (local)</option>
            <option value="grok">Grok (xAI)</option>
            <option value="finetune">Fine-tuned</option>
          </select>
          {provider === 'ollama' && (
            <>
              <label htmlFor="ollama-model">Model</label>
              <select id="ollama-model" value={ollamaModel} onChange={(e)=>onOllamaModelChange && onOllamaModelChange(e.target.value)}>
                {(ollamaModels || []).length === 0 && <option value="">No local models found</option>}
                {(ollamaModels || []).map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </>
          )}
          <label htmlFor="persona">Persona</label>
          <select id="persona" value={persona} onChange={(e)=>onPersonaChange && onPersonaChange(e.target.value)}>
            {(personas || []).map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
          <label style={{display:'flex',gap:'.5rem',alignItems:'center',marginTop:'.25rem'}}>
            <input type="checkbox" checked={!!speakEnabled} onChange={(e)=>onSpeakChange && onSpeakChange(e.target.checked)} />
            Speak replies
          </label>
          <label htmlFor="mic" style={{marginTop:'.35rem'}}>Microphone</label>
          <div className="drawer__mic-row">
            <select id="mic" className="drawer__mic-select" value={selectedMicId || ''} onChange={(e)=>onMicChange && onMicChange(e.target.value)}>
              {(micDevices || []).length === 0 && <option value="">No microphones found</option>}
              {(micDevices || []).map((d, i) => {
                const name = d.label && d.label.trim() ? d.label : `Microphone ${i+1}`;
                return <option key={d.id || i} value={d.id}>{name}</option>;
              })}
            </select>
            <button type="button" className="drawer__new" onClick={onRefreshMics} title="Detect microphones">
              {((micDevices || []).some(d => d.label)) ? 'Refresh' : 'Grant Access'}
            </button>
          </div>
          {!(micDevices || []).some(d => d.label) && (
            <div style={{color:'#94a3b8', fontSize:'.85rem', marginTop:'.25rem'}}>
              Click "Grant Access" to allow microphone permission so device names appear.
            </div>
          )}
          {micDetectionError && (
            <div className="drawer__mic-error">{micDetectionError}</div>
          )}
          <div className="drawer__diag">
            <button type="button" className="drawer__diag-toggle" onClick={onToggleMicDiag}>
              {micDiagOpen ? 'Hide Audio Diagnostics' : 'Show Audio Diagnostics'}
            </button>
            {micDiagOpen && (
              <div className="drawer__diag-panel">
                <button type="button" className="drawer__diag-run" onClick={onRunMicDiagnostics} disabled={micDiagLoading}>
                  {micDiagLoading ? 'Running...' : 'Re-run diagnostics'}
                </button>
                {micDiagLoading && <div className="drawer__diag-status">Collecting microphone data...</div>}
                {micDiagResult && (
                  <div className="drawer__diag-grid">
                    <div>
                      <div className="drawer__diag-heading">Browser</div>
                      <pre>{JSON.stringify(micDiagResult.browser || { error: micDiagResult.browserError }, null, 2)}</pre>
                    </div>
                    <div>
                      <div className="drawer__diag-heading">Backend</div>
                      <pre>{JSON.stringify(micDiagResult.server || { error: micDiagResult.serverError }, null, 2)}</pre>
                    </div>
                  </div>
                )}
                {!micDiagResult && !micDiagLoading && (
                  <div className="drawer__diag-status">Diagnostics will appear here after running.</div>
                )}
              </div>
            )}
          </div>
        </div>
        <div className="drawer__search">
          <input
            type="search"
            placeholder="Search chats..."
            value={search}
            onChange={(e) => onSearch(e.target.value)}
            aria-label="Search past chats"
          />
        </div>
        <div className="drawer__list">
          {(conversations || []).length === 0 && (
            <div className="sidebar__empty">No saved chats yet.</div>
          )}
          {(conversations || []).map((c) => (
            <div key={c.id} className={`drawer__item ${activeId === c.id ? 'active' : ''}`}>
              <button className="drawer__item-btn" onClick={() => onOpen(c.id)} title={c.name}>
                <span className="sidebar__item-name">{c.name}</span>
                <span className="sidebar__item-provider">{c.provider}</span>
              </button>
              <div className="drawer__item-actions">
                <button onClick={() => onRename(c.id)} title="Rename">✏️</button>
                <button onClick={() => onDelete(c.id)} title="Delete">🗑️</button>
              </div>
            </div>
          ))}
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
