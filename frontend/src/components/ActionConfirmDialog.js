import React from 'react';

function ActionConfirmDialog({ open, preview, itemName, onCancel, onConfirm, busy }) {
  if (!open || !preview) {
    return null;
  }

  return (
    <>
      <div className="dialog-backdrop" onClick={busy ? undefined : onCancel} />
      <section className="dialog" role="dialog" aria-modal="true" aria-label="Confirm inventory action">
        <h3>Confirm Action</h3>
        <p className="dialog__lead">{preview.preview || `Run this action for ${itemName || 'this item'}?`}</p>
        {preview.candidate && (
          <div className="dialog__details">
            <div><strong>Item:</strong> {preview.candidate.name}</div>
            <div><strong>Source:</strong> {preview.candidate.source}</div>
            {preview.target_character_id && <div><strong>Target:</strong> {preview.target_character_name || preview.target_character_id}</div>}
          </div>
        )}
        <div className="dialog__actions">
          <button type="button" onClick={onCancel} disabled={busy}>Cancel</button>
          <button type="button" className="dialog__confirm" onClick={onConfirm} disabled={busy}>
            {busy ? 'Applying...' : 'Confirm'}
          </button>
        </div>
      </section>
    </>
  );
}

export default ActionConfirmDialog;
