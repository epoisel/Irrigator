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
  
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4">Current Moisture Level</h2>
      
      {isLoading ? (
        <div className="flex justify-center items-center h-32">
          <div className="loading-spinner"></div>
        </div>
      ) : (
        <>
          <div className="flex justify-between items-center mb-2">
            <span className="text-gray-600">Level:</span>
            <span className="text-2xl font-bold">
              {moistureLevel !== null ? `${moistureLevel.toFixed(1)}%` : 'N/A'}
            </span>
          </div>
          
          <div className="h-4 bg-gray-200 rounded-full overflow-hidden mb-2">
            <div 
              className={`h-full moisture-gauge ${status.color}`}
              style={{ width: `${moistureLevel || 0}%` }}
            ></div>
          </div>
          
          <div className="text-right text-sm font-medium text-gray-600">
            Status: <span className="font-semibold">{status.text}</span>
          </div>
          
          <div className="mt-4 text-xs text-gray-500">
            {moistureData ? (
              <p>Last updated: {new Date(moistureData.timestamp).toLocaleString()}</p>
            ) : (
              <p>No data available</p>
            )}
          </div>
        </>
      )}
    </div>
  );
} 