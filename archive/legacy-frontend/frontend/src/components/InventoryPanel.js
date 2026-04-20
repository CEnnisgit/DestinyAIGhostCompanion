import React from 'react';

const ACTION_LABELS = {
  equip: 'Equip',
  vault: 'Vault',
  pull_from_vault: 'Pull',
  pull_from_postmaster: 'Pull',
  move_to_character: 'Move',
};

const SECTION_LABELS = {
  equipped: 'Equipped',
  inventory: 'Inventory',
  vault: 'Vault',
  postmaster: 'Postmaster',
};

function InventoryPanel({
  inventory,
  loading,
  error,
  selectedCharacterId,
  onSelectCharacter,
  onRefresh,
  onAction,
  actionBusyId,
}) {
  const sections = inventory?.sections || {};
  const characters = inventory?.characters || [];

  return (
    <section className="inventory-panel" aria-label="Inventory management">
      <div className="inventory-panel__header">
        <div>
          <h2>Inventory</h2>
          <p>Equip, move, and vault gear with the same Bungie action flow used by chat commands.</p>
        </div>
        <button type="button" className="inventory-panel__refresh" onClick={onRefresh} disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      <div className="inventory-panel__characters">
        {characters.map((character) => (
          <button
            key={character.character_id}
            type="button"
            className={`inventory-panel__character${selectedCharacterId === character.character_id ? ' active' : ''}`}
            onClick={() => onSelectCharacter && onSelectCharacter(character.character_id)}
          >
            <span>{character.class_name}</span>
            <span>{character.light ? `Power ${character.light}` : (character.is_active ? 'Active' : 'Guardian')}</span>
          </button>
        ))}
      </div>

      {error && <div className="app__error">{error}</div>}

      <div className="inventory-panel__grid">
        {Object.entries(SECTION_LABELS).map(([key, label]) => (
          <section key={key} className="inventory-section">
            <header className="inventory-section__header">
              <h3>{label}</h3>
              <span>{(sections[key] || []).length}</span>
            </header>
            <div className="inventory-section__list">
              {(sections[key] || []).length === 0 && (
                <div className="inventory-card inventory-card--empty">No items available.</div>
              )}
              {(sections[key] || []).map((item) => {
                const busy = actionBusyId === item.instance_id;
                return (
                  <article key={item.instance_id} className="inventory-card">
                    <div className="inventory-card__meta">
                      {item.icon ? (
                        <img src={item.icon} alt="" className="inventory-card__icon" />
                      ) : (
                        <div className="inventory-card__icon inventory-card__icon--placeholder" />
                      )}
                      <div>
                        <h4>{item.name}</h4>
                        <p>
                          {[item.item_type_name, item.tier, item.class_name].filter(Boolean).join(' • ')}
                        </p>
                        <p>
                          {item.power ? `Power ${item.power}` : 'No power stat'}
                          {item.character_id ? ` • ${characters.find((c) => c.character_id === item.character_id)?.class_name || item.character_id}` : ''}
                        </p>
                      </div>
                    </div>
                    <div className="inventory-card__actions">
                      {(item.actions || []).map((action) => (
                        <button
                          key={action}
                          type="button"
                          disabled={busy}
                          onClick={() => onAction && onAction(action, item, selectedCharacterId)}
                        >
                          {busy ? 'Working…' : (ACTION_LABELS[action] || action)}
                        </button>
                      ))}
                    </div>
                  </article>
                );
              })}
            </div>
          </section>
        ))}
      </div>
    </section>
  );
}

export default InventoryPanel;
