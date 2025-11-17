/**
 * Backend Connection Panel
 *
 * UI component for managing connection to Python backend
 * Shows connection status and allows toggling backend integration
 */

import React, { useState } from 'react';
import { useBackendConnection, useBackendIK } from './useBackendAPI';

const BackendPanel = ({ onBackendCalculation, className = '' }) => {
  const { connected, health, error, checking, checkConnection } = useBackendConnection(true);
  const { calculate, calculating, result, error: calcError } = useBackendIK();
  const [useBackend, setUseBackend] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  const handleToggleBackend = () => {
    setUseBackend(!useBackend);
    if (onBackendCalculation) {
      onBackendCalculation(!useBackend);
    }
  };

  const handleTestCalculation = async () => {
    try {
      const testPose = {
        x: 0,
        y: 0,
        z: 0,
        roll: 10,
        pitch: 5,
        yaw: 0,
        configuration: '6-3',
      };
      await calculate(testPose);
    } catch (err) {
      console.error('Test calculation failed:', err);
    }
  };

  return (
    <div className={`backend-panel ${className}`}>
      <div className="panel-header">
        <h3 className="text-lg font-semibold mb-2">Backend Connection</h3>
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="text-sm text-blue-500 hover:text-blue-700"
        >
          {showDetails ? 'Hide Details' : 'Show Details'}
        </button>
      </div>

      <div className="connection-status mb-3">
        <div className="flex items-center gap-2">
          <div
            className={`status-indicator w-3 h-3 rounded-full ${
              connected ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          <span className="text-sm">
            {checking ? 'Checking...' : connected ? 'Connected' : 'Disconnected'}
          </span>
          <button
            onClick={checkConnection}
            disabled={checking}
            className="ml-auto text-xs px-2 py-1 bg-gray-200 hover:bg-gray-300 rounded disabled:opacity-50"
          >
            Refresh
          </button>
        </div>

        {error && <div className="text-xs text-red-600 mt-1">Error: {error}</div>}
      </div>

      {showDetails && (
        <div className="details-section mb-3 p-2 bg-gray-50 rounded text-xs">
          {health ? (
            <>
              <div>
                <strong>API Status:</strong> {health.status}
              </div>
              <div>
                <strong>Version:</strong> {health.version}
              </div>
              <div>
                <strong>Message:</strong> {health.message}
              </div>
            </>
          ) : (
            <div className="text-gray-500">No health data available</div>
          )}
        </div>
      )}

      <div className="backend-toggle mb-3">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={useBackend}
            onChange={handleToggleBackend}
            disabled={!connected}
            className="w-4 h-4"
          />
          <span className="text-sm">Use Backend Calculations</span>
        </label>
        <p className="text-xs text-gray-600 mt-1">
          {useBackend
            ? 'Using Python backend for IK calculations'
            : 'Using local JavaScript calculations'}
        </p>
      </div>

      {connected && (
        <div className="test-section">
          <button
            onClick={handleTestCalculation}
            disabled={calculating}
            className="w-full text-sm px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {calculating ? 'Calculating...' : 'Test Backend'}
          </button>

          {calcError && (
            <div className="text-xs text-red-600 mt-2">Calculation Error: {calcError}</div>
          )}

          {result && showDetails && (
            <div className="result-display mt-2 p-2 bg-gray-50 rounded text-xs">
              <div>
                <strong>Configuration:</strong> {result.configuration}
              </div>
              <div>
                <strong>Valid:</strong> {result.valid ? 'Yes' : 'No'}
              </div>
              <div>
                <strong>Leg Lengths:</strong>
              </div>
              <ul className="ml-4 mt-1">
                {result.leg_lengths.map((length, i) => (
                  <li key={i}>
                    Leg {i}: {length.toFixed(2)} mm
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="info-section mt-3 p-2 bg-blue-50 rounded text-xs">
        <p>
          <strong>Backend URL:</strong> http://localhost:8000
        </p>
        <p className="mt-1 text-gray-600">
          To start backend: <code className="bg-white px-1">python backend/api.py</code>
        </p>
      </div>
    </div>
  );
};

export default BackendPanel;
