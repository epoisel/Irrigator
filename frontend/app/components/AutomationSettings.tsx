'use client';

import { useState, useEffect } from 'react';
import { api, AutomationRule } from '../services/api';

interface AutomationSettingsProps {
  deviceId: string;
}

export default function AutomationSettings({ deviceId }: AutomationSettingsProps) {
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  const [enabled, setEnabled] = useState<boolean>(true);
  const [lowThreshold, setLowThreshold] = useState<number>(30);
  const [highThreshold, setHighThreshold] = useState<number>(70);
  
  // Load automation rules
  useEffect(() => {
    const loadAutomationRules = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        const rules = await api.getAutomationRules(deviceId);
        
        setEnabled(rules.enabled === 1);
        setLowThreshold(rules.low_threshold);
        setHighThreshold(rules.high_threshold);
      } catch (err) {
        setError('Failed to load automation settings');
        console.error('Error loading automation settings:', err);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadAutomationRules();
  }, [deviceId]);
  
  // Save automation rules
  const saveSettings = async () => {
    try {
      setIsSaving(true);
      setError(null);
      setSuccess(null);
      
      // Validate thresholds
      if (lowThreshold >= highThreshold) {
        setError('Low threshold must be less than high threshold');
        return;
      }
      
      const rule: AutomationRule = {
        device_id: deviceId,
        enabled: enabled ? 1 : 0,
        low_threshold: lowThreshold,
        high_threshold: highThreshold
      };
      
      await api.setAutomationRules(rule);
      setSuccess('Automation settings saved successfully');
    } catch (err) {
      setError('Failed to save automation settings');
      console.error('Error saving automation settings:', err);
    } finally {
      setIsSaving(false);
    }
  };
  
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4">Automation Settings</h2>
      
      {isLoading ? (
        <div className="flex justify-center items-center h-48">
          <div className="loading-spinner"></div>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <label htmlFor="automation-toggle" className="text-gray-700 font-medium">
              Automatic Irrigation
            </label>
            <div className="relative inline-block w-12 align-middle select-none">
              <input
                type="checkbox"
                id="automation-toggle"
                className="sr-only"
                checked={enabled}
                onChange={() => setEnabled(!enabled)}
                disabled={isSaving}
              />
              <div className={`block h-6 rounded-full transition-colors ${enabled ? 'bg-primary-500' : 'bg-gray-300'}`}></div>
              <div className={`absolute left-0.5 top-0.5 bg-white border border-gray-300 rounded-full h-5 w-5 transition-transform transform ${enabled ? 'translate-x-6' : ''}`}></div>
            </div>
          </div>
          
          <div>
            <label htmlFor="low-threshold" className="block text-sm font-medium text-gray-700 mb-1">
              Low Moisture Threshold (Turn ON valve)
            </label>
            <div className="flex items-center">
              <input
                type="range"
                id="low-threshold"
                min="0"
                max="100"
                step="1"
                value={lowThreshold}
                onChange={(e) => setLowThreshold(Number(e.target.value))}
                disabled={isSaving || !enabled}
                className={`w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer ${!enabled && 'opacity-50'}`}
              />
              <span className="ml-3 w-12 text-gray-700">{lowThreshold}%</span>
            </div>
            <p className="mt-1 text-sm text-gray-500">
              When moisture falls below this level, the valve will turn ON
            </p>
          </div>
          
          <div>
            <label htmlFor="high-threshold" className="block text-sm font-medium text-gray-700 mb-1">
              High Moisture Threshold (Turn OFF valve)
            </label>
            <div className="flex items-center">
              <input
                type="range"
                id="high-threshold"
                min="0"
                max="100"
                step="1"
                value={highThreshold}
                onChange={(e) => setHighThreshold(Number(e.target.value))}
                disabled={isSaving || !enabled}
                className={`w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer ${!enabled && 'opacity-50'}`}
              />
              <span className="ml-3 w-12 text-gray-700">{highThreshold}%</span>
            </div>
            <p className="mt-1 text-sm text-gray-500">
              When moisture rises above this level, the valve will turn OFF
            </p>
          </div>
          
          <div className="pt-2">
            <button
              onClick={saveSettings}
              disabled={isSaving || isLoading}
              className={`w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white 
                ${isSaving 
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500'}`}
            >
              {isSaving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
          
          {error && (
            <div className="mt-2 text-sm text-red-600">
              {error}
            </div>
          )}
          
          {success && (
            <div className="mt-2 text-sm text-green-600">
              {success}
            </div>
          )}
        </div>
      )}
    </div>
  );
} 