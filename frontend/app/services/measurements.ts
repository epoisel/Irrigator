import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL;

// Create axios instance with default config
const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    },
    withCredentials: false // Important for CORS
});

export interface PlantPhoto {
    id: number;
    filename: string;
    timestamp: string;
}

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
    health_score?: number;
    photos?: PlantPhoto[];
}

export const addMeasurement = async (measurement: PlantMeasurement) => {
    try {
        const response = await api.post('/api/measurements', measurement);
        return response.data;
    } catch (error) {
        console.error('Error adding measurement:', error);
        throw error;
    }
};

export const getMeasurements = async (deviceId: string, days: number = 30) => {
    try {
        const response = await api.get(`/api/measurements/${deviceId}?days=${days}`);
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

export const updateMeasurement = async (id: number, measurement: Partial<PlantMeasurement>) => {
    try {
        const response = await api.put(`/api/measurements/${id}`, measurement);
        return response.data;
    } catch (error) {
        console.error('Error updating measurement:', error);
        throw error;
    }
};

export const deleteMeasurement = async (id: number) => {
    try {
        const response = await api.delete(`/api/measurements/${id}`);
        return response.data;
    } catch (error) {
        console.error('Error deleting measurement:', error);
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

export const uploadPhoto = async (measurementId: number, photo: File) => {
    try {
        const formData = new FormData();
        formData.append('photo', photo);

        const response = await api.post(
            `/api/measurements/${measurementId}/photos`,
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            }
        );
        return response.data;
    } catch (error) {
        console.error('Error uploading photo:', error);
        throw error;
    }
};

export const getPhotos = async (measurementId: number) => {
    try {
        const response = await api.get(`/api/measurements/${measurementId}/photos`);
        return response.data;
    } catch (error) {
        console.error('Error fetching photos:', error);
        throw error;
    }
};

export const getPhotoUrl = (photoId: number) => {
    return `${API_URL}/api/photos/${photoId}`;
};

export const deletePhoto = async (photoId: number) => {
    try {
        const response = await api.delete(`/api/photos/${photoId}`);
        return response.data;
    } catch (error) {
        console.error('Error deleting photo:', error);
        throw error;
    }
}; 