'use client';

import { useState, useEffect } from 'react';
// Comment out missing UI components
// import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
// import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { api, ValveAction } from '../services/api';
import ValveControl from '../components/ValveControl';
import AutomationSettings from '../components/AutomationSettings';
import ValveHistory from '../components/ValveHistory';
import WateringProfiles from '../components/WateringProfiles';
import TimeRangeSelector from '../components/TimeRangeSelector';
import { Settings, Droplet, History, ListFilter } from 'lucide-react';

// Default device ID - this would typically come from user selection or configuration
const DEFAULT_DEVICE_ID = process.env.NEXT_PUBLIC_DEFAULT_DEVICE_ID || 'pico_01';

export default function ControlPage() {
  const [valveHistory, setValveHistory] = useState<ValveAction[]>([]);
  const [valveHistoryPagination, setValveHistoryPagination] = useState({
    total: 0,
    page: 1,
    limit: 5,
    pages: 1
  });
  const [selectedDays, setSelectedDays] = useState<number>(1);
  const [isLoadingValveHistory, setIsLoadingValveHistory] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState('manual');
  
  // Load valve history
  useEffect(() => {
    const fetchValveHistory = async () => {
      try {
        setIsLoadingValveHistory(true);
        
        const response = await api.getValveHistory(
          DEFAULT_DEVICE_ID, 
          selectedDays,
          valveHistoryPagination?.page || 1,
          valveHistoryPagination?.limit || 5
        );
        
        if (response && response.data) {
          setValveHistory(response.data);
        }
        
        if (response && response.pagination) {
          setValveHistoryPagination(response.pagination);
        }
      } catch (err) {
        console.error('Error fetching valve history:', err);
        // Set empty data on error to prevent undefined access
        setValveHistory([]);
      } finally {
        setIsLoadingValveHistory(false);
      }
    };
    
    fetchValveHistory();
  }, [selectedDays, valveHistoryPagination?.page, valveHistoryPagination?.limit]);
  
  // Handle valve state change
  const handleValveChange = () => {
    // Refresh valve history when valve state changes
    const fetchValveHistory = async () => {
      try {
        const response = await api.getValveHistory(
          DEFAULT_DEVICE_ID, 
          selectedDays,
          valveHistoryPagination?.page || 1,
          valveHistoryPagination?.limit || 5
        );
        
        if (response && response.data) {
          setValveHistory(response.data);
        }
        
        if (response && response.pagination) {
          setValveHistoryPagination(response.pagination);
        }
      } catch (err) {
        console.error('Error fetching valve history:', err);
        // Set empty data on error
        setValveHistory([]);
      }
    };
    
    fetchValveHistory();
  };
  
  // Handle valve history page change
  const handleValveHistoryPageChange = (page: number) => {
    setValveHistoryPagination(prev => ({
      ...(prev || { total: 0, limit: 5, pages: 1 }),
      page
    }));
  };

  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Irrigation Control</h1>
        <TimeRangeSelector 
          selectedDays={selectedDays} 
          onSelectDays={setSelectedDays} 
        />
      </div>
      
      {/* Tabs Navigation */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            <button
              onClick={() => setActiveTab('manual')}
              className={`mr-1 py-4 px-4 flex items-center border-b-2 font-medium text-sm ${
                activeTab === 'manual'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Droplet className="mr-2 h-4 w-4" />
              Manual Control
            </button>
            <button
              onClick={() => setActiveTab('automation')}
              className={`mr-1 py-4 px-4 flex items-center border-b-2 font-medium text-sm ${
                activeTab === 'automation'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Settings className="mr-2 h-4 w-4" />
              Basic Automation
            </button>
            <button
              onClick={() => setActiveTab('profiles')}
              className={`mr-1 py-4 px-4 flex items-center border-b-2 font-medium text-sm ${
                activeTab === 'profiles'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <ListFilter className="mr-2 h-4 w-4" />
              Advanced Profiles
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`mr-1 py-4 px-4 flex items-center border-b-2 font-medium text-sm ${
                activeTab === 'history'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <History className="mr-2 h-4 w-4" />
              Valve History
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        <div className="mt-4">
          {/* Manual Control Tab */}
          {activeTab === 'manual' && (
            <div className="border rounded-lg shadow-sm overflow-hidden">
              <div className="p-4 bg-gray-50 border-b">
                <h2 className="text-xl font-semibold">Valve Control</h2>
              </div>
              <div className="p-4">
                <ValveControl 
                  deviceId={DEFAULT_DEVICE_ID} 
                  onValveChange={handleValveChange} 
                />
              </div>
            </div>
          )}
          
          {/* Automation Tab */}
          {activeTab === 'automation' && (
            <div className="border rounded-lg shadow-sm overflow-hidden">
              <div className="p-4 bg-gray-50 border-b">
                <h2 className="text-xl font-semibold">Automation Settings</h2>
              </div>
              <div className="p-4">
                <AutomationSettings 
                  deviceId={DEFAULT_DEVICE_ID} 
                />
              </div>
            </div>
          )}
          
          {/* Profiles Tab */}
          {activeTab === 'profiles' && (
            <div className="border rounded-lg shadow-sm overflow-hidden">
              <div className="p-4 bg-gray-50 border-b">
                <h2 className="text-xl font-semibold">Advanced Watering Profiles</h2>
              </div>
              <div className="p-4">
                <WateringProfiles deviceId={DEFAULT_DEVICE_ID} />
              </div>
            </div>
          )}
          
          {/* History Tab */}
          {activeTab === 'history' && (
            <div className="border rounded-lg shadow-sm overflow-hidden">
              <div className="p-4 bg-gray-50 border-b">
                <h2 className="text-xl font-semibold">Valve History</h2>
              </div>
              <div className="p-4">
                <ValveHistory 
                  valveHistory={valveHistory || []}
                  isLoading={isLoadingValveHistory}
                  pagination={valveHistoryPagination || { total: 0, page: 1, limit: 5, pages: 1 }}
                  onPageChange={handleValveHistoryPageChange}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 