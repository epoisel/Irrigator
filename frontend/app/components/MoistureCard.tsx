'use client';

import { useState, useEffect } from 'react';
import { MoistureData } from '../services/api';

interface MoistureCardProps {
  moistureData: MoistureData | null;
  isLoading: boolean;
}

export default function MoistureCard({ moistureData, isLoading }: MoistureCardProps) {
  const [moistureLevel, setMoistureLevel] = useState<number | null>(null);
  
  useEffect(() => {
    if (moistureData) {
      setMoistureLevel(moistureData.moisture);
    }
  }, [moistureData]);
  
  // Determine moisture status and color
  const getMoistureStatus = (level: number | null) => {
    if (level === null) return { text: 'Unknown', color: 'bg-gray-200' };
    if (level < 20) return { text: 'Very Dry', color: 'bg-red-500' };
    if (level < 40) return { text: 'Dry', color: 'bg-orange-400' };
    if (level < 60) return { text: 'Moderate', color: 'bg-yellow-300' };
    if (level < 80) return { text: 'Moist', color: 'bg-green-400' };
    return { text: 'Very Moist', color: 'bg-blue-500' };
  };
  
  const status = getMoistureStatus(moistureLevel);
  
  if (isLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow animate-pulse">
        <div className="h-24 bg-gray-200 rounded"></div>
      </div>
    );
  }

  if (!moistureData) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <p className="text-gray-500">No moisture data available</p>
      </div>
    );
  }

  // Determine moisture level class
  const getMoistureClass = (moisture: number) => {
    if (moisture < 20) return "text-red-600";
    if (moisture < 40) return "text-orange-600";
    if (moisture < 60) return "text-yellow-600";
    if (moisture < 80) return "text-green-600";
    return "text-blue-600";
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4">Current Moisture Level</h2>
      
      <div className="text-center">
        <div className={`text-4xl font-bold ${getMoistureClass(moistureData.moisture)}`}>
          {moistureData.moisture.toFixed(1)}%
        </div>
        {moistureData.raw_adc_value && (
          <div className="mt-2 text-sm text-gray-500">
            Raw ADC Value: {moistureData.raw_adc_value}
          </div>
        )}
        <div className="mt-2 text-sm text-gray-500">
          Last updated: {new Date(moistureData.timestamp).toLocaleString()}
        </div>
      </div>
    </div>
  );
} 