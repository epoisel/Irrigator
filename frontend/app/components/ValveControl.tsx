'use client';

import { useState } from 'react';
import { api } from '../services/api';

interface ValveControlProps {
  deviceId: string;
  onValveChange?: (state: number) => void;
}

export default function ValveControl({ deviceId, onValveChange }: ValveControlProps) {
  const [valveState, setValveState] = useState<number>(0); // 0 = OFF, 1 = ON
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  const toggleValve = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Toggle valve state (0 -> 1, 1 -> 0)
      const newState = valveState === 0 ? 1 : 0;
      
      // Send command to API
      await api.controlValve(deviceId, newState);
      
      // Update local state
      setValveState(newState);
      
      // Notify parent component if callback provided
      if (onValveChange) {
        onValveChange(newState);
      }
    } catch (err) {
      setError('Failed to control valve. Please try again.');
      console.error('Valve control error:', err);
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4">Valve Control</h2>
      
      <div className="flex flex-col items-center">
        <div className={`w-32 h-32 rounded-full flex items-center justify-center mb-4 valve-button
          ${valveState === 1 
            ? 'bg-blue-500 text-white' 
            : 'bg-gray-200 text-gray-700'}`}
          onClick={!isLoading ? toggleValve : undefined}
          role="button"
          tabIndex={0}
          aria-label={`Turn valve ${valveState === 0 ? 'ON' : 'OFF'}`}
        >
          {isLoading ? (
            <div className="loading-spinner"></div>
          ) : (
            <div className="text-center">
              <div className="text-2xl font-bold">{valveState === 1 ? 'ON' : 'OFF'}</div>
              <div className="text-sm mt-1">{valveState === 1 ? 'Water flowing' : 'Water stopped'}</div>
            </div>
          )}
        </div>
        
        <button
          className={`px-6 py-2 rounded-md font-medium transition-colors
            ${isLoading 
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
              : valveState === 0 
                ? 'bg-blue-500 hover:bg-blue-600 text-white' 
                : 'bg-gray-500 hover:bg-gray-600 text-white'}`}
          onClick={!isLoading ? toggleValve : undefined}
          disabled={isLoading}
        >
          {isLoading 
            ? 'Processing...' 
            : valveState === 0 
              ? 'Turn Valve ON' 
              : 'Turn Valve OFF'}
        </button>
        
        {error && (
          <div className="mt-4 text-red-500 text-sm">{error}</div>
        )}
      </div>
    </div>
  );
} 