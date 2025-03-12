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
    notes?: string;
    fertilized?: boolean;
    pruned?: boolean;
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
        const measurements = response.data;
        
        // Calculate health score for each measurement
        return measurements.map((m: PlantMeasurement) => ({
            ...m,
            health_score: calculateHealthScore(m)
        }));
    } catch (error) {
        console.error('Error fetching measurements:', error);
        throw error;
    }
};

// Calculate a health score based on available metrics
export const calculateHealthScore = (measurement: PlantMeasurement): number => {
    let score = 0;
    let metrics = 0;

    // Leaf color contributes up to 40 points (1-5 scale * 8)
    if (measurement.leaf_color) {
        score += measurement.leaf_color * 8;
        metrics++;
    }

    // Leaf firmness contributes up to 40 points (1-5 scale * 8)
    if (measurement.leaf_firmness) {
        score += measurement.leaf_firmness * 8;
        metrics++;
    }

    // Growth indicators contribute the remaining 20 points
    if (measurement.leaf_count && measurement.height && measurement.canopy_width) {
        // This is a simplified score - you might want to adjust based on plant type/age
        score += 20;
        metrics++;
    }

    // Return average score if we have metrics, otherwise 0
    return metrics > 0 ? Math.round(score / metrics) : 0;
}; 