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

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    total: number;
    page: number;
    limit: number;
    pages: number;
  };
}

export interface AutomationRule {
  id?: number;
  device_id: string;
  enabled: number;
  low_threshold: number;
  high_threshold: number;
}

// Zone Types
export interface Zone {
  id: number;
  name: string;
  description: string | null;
  device_id: string | null;
  width: number;
  length: number;
  created_at: string;
  updated_at: string;
  plants?: Plant[];
}

export interface Plant {
  id: number;
  name: string;
  species: string;
  planting_date: string;
  position_x: number;
  position_y: number;
  notes: string | null;
  water_requirements: string | null;
}

export interface CreateZoneData {
  name: string;
  description?: string;
  device_id?: string;
  width: number;
  length: number;
}

export interface CreatePlantData {
  name: string;
  species: string;
  planting_date: string;
  position_x: number;
  position_y: number;
  notes?: string;
  water_requirements?: string;
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
   * @param page Page number for pagination
   * @param limit Number of items per page
   * @returns Promise with valve action data and pagination info
   */
  getValveHistory: async (
    deviceId = DEFAULT_DEVICE_ID, 
    days = 1,
    page = 1,
    limit = 100
  ): Promise<PaginatedResponse<ValveAction>> => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/analytics/valve`, {
        params: { device_id: deviceId, days, page, limit }
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
  },

  async controlAutomation(deviceId: string | undefined, enabled: number): Promise<{ status: string }> {
    if (!deviceId) throw new Error('Device ID is required');
    
    try {
      const response = await axios.post(`${API_BASE_URL}/api/automation/control`, {
        device_id: deviceId,
        enabled
      });
      console.log('Automation control response:', response.data);  // Debug log
      return response.data;
    } catch (error) {
      console.error('Error controlling automation:', error);
      throw error;
    }
  },
};

// Zone API Functions
export const fetchZones = async (): Promise<Zone[]> => {
  const response = await fetch(`${API_BASE_URL}/api/zones`);
  if (!response.ok) {
    throw new Error('Failed to fetch zones');
  }
  return response.json();
};

export const createZone = async (data: CreateZoneData): Promise<Zone> => {
  const response = await fetch(`${API_BASE_URL}/api/zones`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to create zone');
  }
  return response.json();
};

export const updateZone = async (zoneId: number, data: CreateZoneData): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}/api/zones/${zoneId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to update zone');
  }
};

export const deleteZone = async (zoneId: number): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}/api/zones/${zoneId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete zone');
  }
};

export const fetchZoneDetails = async (zoneId: number): Promise<Zone> => {
  const response = await fetch(`${API_BASE_URL}/api/zones/${zoneId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch zone details');
  }
  return response.json();
};

export const createPlant = async (zoneId: number, data: CreatePlantData): Promise<Plant> => {
  const response = await fetch(`${API_BASE_URL}/api/zones/${zoneId}/plants`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to create plant');
  }
  return response.json();
};

export const updatePlant = async (zoneId: number, plantId: number, data: CreatePlantData): Promise<Plant> => {
  const response = await fetch(`${API_BASE_URL}/api/zones/${zoneId}/plants/${plantId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to update plant');
  }
  return response.json();
};

export const deletePlant = async (zoneId: number, plantId: number): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}/api/zones/${zoneId}/plants/${plantId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete plant');
  }
};

export const fetchZoneHistory = async (zoneId: number): Promise<any[]> => {
  const response = await fetch(`${API_BASE_URL}/api/zones/${zoneId}/history`);
  if (!response.ok) {
    throw new Error('Failed to fetch zone history');
  }
  return response.json();
};

export const addZoneEvent = async (zoneId: number, data: { event_type: string; event_description: string; plant_id?: number }): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}/api/zones/${zoneId}/history`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to add zone event');
  }
}; 