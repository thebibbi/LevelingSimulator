import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './stewart_6_3_browser_visualizer';
import ErrorBoundary from './ErrorBoundary';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);
