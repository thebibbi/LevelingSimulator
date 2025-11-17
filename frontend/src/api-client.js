/**
 * API Client for Platform Leveling Backend
 *
 * Provides integration between React frontend and Python FastAPI backend
 * Supports both REST API and WebSocket connections
 */

const DEFAULT_API_URL = 'http://localhost:8000';

class PlatformAPIClient {
  constructor(baseURL = DEFAULT_API_URL) {
    this.baseURL = baseURL;
    this.ws = null;
    this.wsCallbacks = new Set();
    this.connected = false;
  }

  /**
   * Check if backend API is available
   */
  async checkHealth() {
    try {
      const response = await fetch(`${this.baseURL}/health`);
      const data = await response.json();
      this.connected = response.ok;
      return { connected: this.connected, data };
    } catch (error) {
      this.connected = false;
      return { connected: false, error: error.message };
    }
  }

  /**
   * Calculate inverse kinematics using backend
   *
   * @param {Object} pose - The desired pose
   * @param {number} pose.x - X translation (mm)
   * @param {number} pose.y - Y translation (mm)
   * @param {number} pose.z - Z translation (mm)
   * @param {number} pose.roll - Roll angle (degrees)
   * @param {number} pose.pitch - Pitch angle (degrees)
   * @param {number} pose.yaw - Yaw angle (degrees)
   * @param {string} pose.configuration - Platform configuration (e.g., '6-3', '8-8')
   * @param {Object} pose.geometry - Optional geometry parameters
   * @returns {Promise<Object>} Leg lengths and validity
   */
  async calculateIK(pose) {
    try {
      const response = await fetch(`${this.baseURL}/calculate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(pose),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('IK calculation error:', error);
      throw error;
    }
  }

  /**
   * Calculate leg lengths needed to level the platform
   *
   * @param {number} roll - Current roll angle (degrees)
   * @param {number} pitch - Current pitch angle (degrees)
   * @param {number} yaw - Current yaw angle (degrees)
   * @param {string} configuration - Platform configuration
   * @returns {Promise<Object>} Leg lengths to achieve level
   */
  async calculateLeveling(roll, pitch, yaw = 0, configuration = '6-3') {
    try {
      const url = new URL(`${this.baseURL}/level`);
      url.searchParams.append('roll', roll);
      url.searchParams.append('pitch', pitch);
      url.searchParams.append('yaw', yaw);
      url.searchParams.append('configuration', configuration);

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Leveling calculation error:', error);
      throw error;
    }
  }

  /**
   * Get current platform configuration from backend
   */
  async getConfig() {
    try {
      const response = await fetch(`${this.baseURL}/config`);
      return await response.json();
    } catch (error) {
      console.error('Get config error:', error);
      throw error;
    }
  }

  /**
   * Update platform configuration on backend
   *
   * @param {Object} config - Platform geometry configuration
   * @param {number} config.base_radius - Base radius (mm)
   * @param {number} config.platform_radius - Platform radius (mm)
   * @param {number} config.nominal_leg_length - Nominal leg length (mm)
   * @param {number} config.min_leg_length - Minimum leg length (mm)
   * @param {number} config.max_leg_length - Maximum leg length (mm)
   */
  async updateConfig(config) {
    try {
      const response = await fetch(`${this.baseURL}/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Update config error:', error);
      throw error;
    }
  }

  /**
   * Get list of available platform configurations
   */
  async getAvailableConfigurations() {
    try {
      const response = await fetch(`${this.baseURL}/configurations`);
      return await response.json();
    } catch (error) {
      console.error('Get configurations error:', error);
      throw error;
    }
  }

  /**
   * Connect to backend WebSocket for real-time updates
   *
   * @param {Function} onMessage - Callback for incoming messages
   * @param {Function} onError - Callback for errors
   * @param {Function} onClose - Callback for connection close
   */
  connectWebSocket(onMessage, onError, onClose) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.warn('WebSocket already connected');
      return;
    }

    const wsURL = this.baseURL.replace('http://', 'ws://').replace('https://', 'wss://');
    this.ws = new WebSocket(`${wsURL}/ws`);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.connected = true;
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (onMessage) onMessage(data);

        // Notify all registered callbacks
        this.wsCallbacks.forEach(callback => callback(data));
      } catch (error) {
        console.error('WebSocket message parse error:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.connected = false;
      if (onError) onError(error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket closed');
      this.connected = false;
      if (onClose) onClose();
    };
  }

  /**
   * Send pose data via WebSocket
   *
   * @param {Object} pose - Pose data to send
   */
  sendWebSocketPose(pose) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(pose));
    } else {
      console.warn('WebSocket not connected');
    }
  }

  /**
   * Register a callback for WebSocket messages
   *
   * @param {Function} callback - Callback function
   * @returns {Function} Unsubscribe function
   */
  onWebSocketMessage(callback) {
    this.wsCallbacks.add(callback);
    return () => this.wsCallbacks.delete(callback);
  }

  /**
   * Close WebSocket connection
   */
  closeWebSocket() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.connected = false;
    }
  }

  /**
   * Check if client is connected
   */
  isConnected() {
    return this.connected;
  }
}

// Create a singleton instance
const apiClient = new PlatformAPIClient();

export default apiClient;
export { PlatformAPIClient };
