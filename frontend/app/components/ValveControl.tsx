'use client';

import { useState, useEffect } from 'react';
import { api } from '../services/api';

interface ValveControlProps {
  deviceId: string;
  onValveChange?: (state: number) => void;
}

export default function ValveControl({ deviceId, onValveChange }: ValveControlProps) {
  const [valveState, setValveState] = useState<number>(0); // 0 = OFF, 1 = ON
  const [automationEnabled, setAutomationEnabled] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  // Poll valve state and automation state every 5 seconds
  useEffect(() => {
    const fetchStates = async () => {
      try {
        // Get the most recent valve action
        const history = await api.getValveHistory(deviceId, 1);
        if (history && history.length > 0) {
          const lastAction = history[0];
          setValveState(lastAction.state);
        }

        // Get automation state
        const rules = await api.getAutomationRules(deviceId);
        setAutomationEnabled(rules.enabled === 1);
      } catch (err) {
        console.error('Error fetching states:', err);
      }
    };

    // Initial fetch
    fetchStates();

    // Set up polling
    const interval = setInterval(fetchStates, 5000);

    // Cleanup on unmount
    return () => clearInterval(interval);
  }, [deviceId]);
  
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

  const toggleAutomation = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Toggle automation state
      const newState = !automationEnabled;
      
      // Send command to API
      await api.controlAutomation(deviceId, newState ? 1 : 0);
      
      // Update local state
      setAutomationEnabled(newState);
    } catch (err) {
      setError('Failed to toggle automation. Please try again.');
      console.error('Automation control error:', err);
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
        
        <div className="flex flex-col gap-2 w-full max-w-xs">
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

          <button
            className={`px-6 py-2 rounded-md font-medium transition-colors
              ${isLoading 
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                : automationEnabled
                  ? 'bg-green-500 hover:bg-green-600 text-white' 
                  : 'bg-yellow-500 hover:bg-yellow-600 text-white'}`}
            onClick={!isLoading ? toggleAutomation : undefined}
            disabled={isLoading}
          >
            {isLoading 
              ? 'Processing...' 
              : automationEnabled 
                ? 'Disable Automation' 
                : 'Enable Automation'}
          </button>
        </div>
        
        {error && (
          <div className="mt-4 text-red-500 text-sm">{error}</div>
        )}

        <div className="mt-4 text-sm text-gray-600">
          {automationEnabled ? (
            <span className="text-green-600">✓ Automation is enabled</span>
          ) : (
            <span className="text-yellow-600">⚠ Automation is disabled</span>
          )}
        </div>
      </div>
    </div>
  );
} 