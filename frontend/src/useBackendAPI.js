/**
 * React Hook for Backend API Integration
 *
 * Provides easy-to-use React hooks for connecting to the Python backend
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import apiClient from './api-client';

/**
 * Hook for managing backend connection status
 */
export function useBackendConnection(autoConnect = true) {
  const [connected, setConnected] = useState(false);
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);
  const [checking, setChecking] = useState(false);

  const checkConnection = useCallback(async () => {
    setChecking(true);
    setError(null);
    try {
      const result = await apiClient.checkHealth();
      setConnected(result.connected);
      setHealth(result.data);
      if (!result.connected && result.error) {
        setError(result.error);
      }
    } catch (err) {
      setConnected(false);
      setError(err.message);
    } finally {
      setChecking(false);
    }
  }, []);

  useEffect(() => {
    if (autoConnect) {
      checkConnection();
      // Check connection periodically
      const interval = setInterval(checkConnection, 10000); // Every 10 seconds
      return () => clearInterval(interval);
    }
  }, [autoConnect, checkConnection]);

  return {
    connected,
    health,
    error,
    checking,
    checkConnection,
  };
}

/**
 * Hook for calculating IK using backend
 */
export function useBackendIK() {
  const [calculating, setCalculating] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const calculate = useCallback(async (pose) => {
    setCalculating(true);
    setError(null);
    try {
      const data = await apiClient.calculateIK(pose);
      setResult(data);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setCalculating(false);
    }
  }, []);

  const calculateLeveling = useCallback(async (roll, pitch, yaw = 0, configuration = '6-3') => {
    setCalculating(true);
    setError(null);
    try {
      const data = await apiClient.calculateLeveling(roll, pitch, yaw, configuration);
      setResult(data);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setCalculating(false);
    }
  }, []);

  return {
    calculate,
    calculateLeveling,
    calculating,
    result,
    error,
  };
}

/**
 * Hook for WebSocket real-time communication
 */
export function useBackendWebSocket(enabled = false) {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [error, setError] = useState(null);
  const wsRef = useRef(false);

  useEffect(() => {
    if (enabled && !wsRef.current) {
      wsRef.current = true;

      apiClient.connectWebSocket(
        // onMessage
        (data) => {
          setLastMessage(data);
          setConnected(true);
        },
        // onError
        (err) => {
          setError(err.message || 'WebSocket error');
          setConnected(false);
        },
        // onClose
        () => {
          setConnected(false);
          wsRef.current = false;
        }
      );
    }

    return () => {
      if (enabled && wsRef.current) {
        apiClient.closeWebSocket();
        wsRef.current = false;
      }
    };
  }, [enabled]);

  const sendPose = useCallback((pose) => {
    apiClient.sendWebSocketPose(pose);
  }, []);

  return {
    connected,
    lastMessage,
    error,
    sendPose,
  };
}

/**
 * Hook for managing platform configuration
 */
export function usePlatformConfig() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadConfig = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.getConfig();
      setConfig(data);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateConfig = useCallback(async (newConfig) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.updateConfig(newConfig);
      setConfig(data);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  return {
    config,
    loading,
    error,
    updateConfig,
    reloadConfig: loadConfig,
  };
}

/**
 * Hook for comparing local JS calculations with backend calculations
 */
export function useCalculationComparison() {
  const [comparison, setComparison] = useState(null);
  const [comparing, setComparing] = useState(false);

  const compare = useCallback(async (pose, localResult) => {
    setComparing(true);
    try {
      const backendResult = await apiClient.calculateIK(pose);

      // Calculate differences
      const differences = localResult.leg_lengths.map((localLength, i) => {
        const backendLength = backendResult.leg_lengths[i];
        return {
          leg: i,
          local: localLength,
          backend: backendLength,
          difference: Math.abs(localLength - backendLength),
          percentDiff: Math.abs((localLength - backendLength) / backendLength) * 100,
        };
      });

      const maxDiff = Math.max(...differences.map(d => d.difference));
      const avgDiff = differences.reduce((sum, d) => sum + d.difference, 0) / differences.length;

      setComparison({
        pose,
        local: localResult,
        backend: backendResult,
        differences,
        maxDiff,
        avgDiff,
        match: maxDiff < 0.1, // Consider matching if within 0.1mm
      });

      return comparison;
    } catch (error) {
      console.error('Comparison error:', error);
      throw error;
    } finally {
      setComparing(false);
    }
  }, []);

  return {
    comparison,
    comparing,
    compare,
  };
}

// Export all hooks as default object for convenience
export default {
  useBackendConnection,
  useBackendIK,
  useBackendWebSocket,
  usePlatformConfig,
  useCalculationComparison,
};
