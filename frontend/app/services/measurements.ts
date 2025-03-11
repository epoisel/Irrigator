import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export interface PlantMeasurement {
    id?: number;
    device_id: string;
    plant_name?: string;
    timestamp?: string;
    height?: number;
    leaf_count?: number;
    stem_thickness?: number;
    canopy_width?: number;
    leaf_color?: number;
    leaf_firmness?: number;
    health_score?: number;
    notes?: string;
    fertilized?: boolean;
    pruned?: boolean;
    ph_reading?: number;
}

export const addMeasurement = async (measurement: PlantMeasurement) => {
    try {
        const response = await axios.post(`${API_URL}/api/measurements`, measurement);
        return response.data;
    } catch (error) {
        console.error('Error adding measurement:', error);
        throw error;
    }
};

export const getMeasurements = async (deviceId: string, days: number = 30) => {
    try {
        const response = await axios.get(`${API_URL}/api/measurements/${deviceId}?days=${days}`);
        return response.data;
    } catch (error) {
        console.error('Error fetching measurements:', error);
        throw error;
    }
}; 