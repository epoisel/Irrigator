'use client';

import { useState, useEffect } from 'react';
import { api, MoistureData, ValveAction } from './services/api';
import MoistureCard from './components/MoistureCard';
import ValveControl from './components/ValveControl';
import MoistureChart from './components/MoistureChart';
import ValveHistory from './components/ValveHistory';
import AutomationSettings from './components/AutomationSettings';
import TimeRangeSelector from './components/TimeRangeSelector';
import PlantMeasurements from './components/PlantMeasurements';

// Default device ID - this would typically come from user selection or configuration
const DEFAULT_DEVICE_ID = process.env.NEXT_PUBLIC_DEFAULT_DEVICE_ID || 'pico_01';

export default function Home() {
  // State for data
  const [moistureData, setMoistureData] = useState<MoistureData[]>([]);
  const [currentMoisture, setCurrentMoisture] = useState<MoistureData | null>(null);
  const [valveHistory, setValveHistory] = useState<ValveAction[]>([]);
  
  // State for UI
  const [selectedDays, setSelectedDays] = useState<number>(1);
  const [isLoadingMoisture, setIsLoadingMoisture] = useState<boolean>(true);
  const [isLoadingValveHistory, setIsLoadingValveHistory] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Load moisture data
  useEffect(() => {
    const fetchMoistureData = async () => {
      try {
        setIsLoadingMoisture(true);
        setError(null);
        
        const data = await api.getMoistureData(DEFAULT_DEVICE_ID, selectedDays);
        setMoistureData(data);
        
        // Set current moisture to the most recent reading
        if (data.length > 0) {
          setCurrentMoisture(data[data.length - 1]);
        }
      } catch (err) {
        setError('Failed to load moisture data');
        console.error('Error fetching moisture data:', err);
      } finally {
        setIsLoadingMoisture(false);
      }
    };
    
    fetchMoistureData();
    
    // Set up polling for real-time updates (every 30 seconds)
    const intervalId = setInterval(fetchMoistureData, 30000);
    
    // Clean up interval on component unmount
    return () => clearInterval(intervalId);
  }, [selectedDays]);
  
  // Load valve history
  useEffect(() => {
    const fetchValveHistory = async () => {
      try {
        setIsLoadingValveHistory(true);
        
        const data = await api.getValveHistory(DEFAULT_DEVICE_ID, selectedDays);
        setValveHistory(data);
      } catch (err) {
        console.error('Error fetching valve history:', err);
      } finally {
        setIsLoadingValveHistory(false);
      }
    };
    
    fetchValveHistory();
  }, [selectedDays]);
  
  // Handle valve state change
  const handleValveChange = () => {
    // Refresh valve history when valve state changes
    const fetchValveHistory = async () => {
      try {
        const data = await api.getValveHistory(DEFAULT_DEVICE_ID, selectedDays);
        setValveHistory(data);
      } catch (err) {
        console.error('Error fetching valve history:', err);
      }
    };
    
    fetchValveHistory();
  };
  
  return (
    <div className="space-y-8">
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          <p>{error}</p>
        </div>
      )}
      
      <TimeRangeSelector 
        selectedDays={selectedDays} 
        onSelectDays={setSelectedDays} 
      />
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <MoistureCard 
          moistureData={currentMoisture} 
          isLoading={isLoadingMoisture} 
        />
        <ValveControl 
          deviceId={DEFAULT_DEVICE_ID} 
          onValveChange={handleValveChange} 
        />
      </div>
      
      <div className="mb-6">
        <MoistureChart 
          moistureData={moistureData} 
          isLoading={isLoadingMoisture} 
        />
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ValveHistory 
          valveHistory={valveHistory} 
          isLoading={isLoadingValveHistory} 
        />
        <AutomationSettings 
          deviceId={DEFAULT_DEVICE_ID} 
        />
      </div>
      
      <div className="mt-8">
        <PlantMeasurements deviceId={DEFAULT_DEVICE_ID} />
      </div>
    </div>
  );
} 