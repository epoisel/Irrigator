import axios from 'axios';

// API base URL - change this to match your Raspberry Pi's IP address
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

// Default device ID
const DEFAULT_DEVICE_ID = 'pico_01';

// Types
export interface MoistureData {
  id: number;
  device_id: string;
  moisture: number;
  raw_adc_value?: number;
  timestamp: string;
}

export interface ValveAction {
  id: number;
  device_id: string;
  state: number;
  timestamp: string;
}

export interface AutomationRule {
  id?: number;
  device_id: string;
  enabled: number;
  low_threshold: number;
  high_threshold: number;
}

// API functions
export const api = {
  /**
   * Get moisture data for a device
   * @param deviceId Device ID
   * @param days Number of days of data to retrieve
   * @returns Promise with moisture data
   */
  getMoistureData: async (deviceId = DEFAULT_DEVICE_ID, days = 1): Promise<MoistureData[]> => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/analytics/moisture`, {
        params: { device_id: deviceId, days }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching moisture data:', error);
      throw error;
    }
  },

  /**
   * Get valve action history for a device
   * @param deviceId Device ID
   * @param days Number of days of data to retrieve
   * @returns Promise with valve action data
   */
  getValveHistory: async (deviceId = DEFAULT_DEVICE_ID, days = 1): Promise<ValveAction[]> => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/analytics/valve`, {
        params: { device_id: deviceId, days }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching valve history:', error);
      throw error;
    }
  },

  /**
   * Control a valve
   * @param deviceId Device ID
   * @param state Valve state (0 = OFF, 1 = ON)
   * @returns Promise with success status
   */
  controlValve: async (deviceId = DEFAULT_DEVICE_ID, state: number): Promise<{ status: string }> => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/valve/control`, {
        device_id: deviceId,
        state
      });
      return response.data;
    } catch (error) {
      console.error('Error controlling valve:', error);
      throw error;
    }
  },

  /**
   * Get automation rules for a device
   * @param deviceId Device ID
   * @returns Promise with automation rule
   */
  getAutomationRules: async (deviceId = DEFAULT_DEVICE_ID): Promise<AutomationRule> => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/automation`, {
        params: { device_id: deviceId }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching automation rules:', error);
      throw error;
    }
  },

  /**
   * Set automation rules for a device
   * @param rule Automation rule
   * @returns Promise with success status
   */
  setAutomationRules: async (rule: AutomationRule): Promise<{ status: string }> => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/automation`, rule);
      return response.data;
    } catch (error) {
      console.error('Error setting automation rules:', error);
      throw error;
    }
  }
}; 