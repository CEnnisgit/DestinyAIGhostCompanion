import React from 'react';

const LoadingSpinner = () => (
  <div className="loading-spinner" role="status" aria-live="polite">
    <div className="loading-spinner__icon" />
    <span className="loading-spinner__label">Linking to your Ghost...</span>
  </div>
);

export default LoadingSpinner;
