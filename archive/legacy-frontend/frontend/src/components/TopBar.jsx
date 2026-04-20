import React from 'react';

const TopBar = ({ onHamburger }) => {
  // Render only a floating hamburger button pinned to the top-left
  return (
    <button
      className="hamburger-fab"
      onClick={onHamburger}
      aria-label="Open chats"
      title="Open chats"
    >
      ☰
    </button>
  );
};

export default TopBar;
