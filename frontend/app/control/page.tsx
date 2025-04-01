'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
      
      <Tabs defaultValue="manual" className="mb-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="manual" className="flex items-center">
            <Droplet className="mr-2 h-4 w-4" />
            Manual Control
          </TabsTrigger>
          <TabsTrigger value="automation" className="flex items-center">
            <Settings className="mr-2 h-4 w-4" />
            Basic Automation
          </TabsTrigger>
          <TabsTrigger value="profiles" className="flex items-center">
            <ListFilter className="mr-2 h-4 w-4" />
            Advanced Profiles
          </TabsTrigger>
          <TabsTrigger value="history" className="flex items-center">
            <History className="mr-2 h-4 w-4" />
            Valve History
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="manual">
          <Card>
            <CardHeader>
              <CardTitle>Valve Control</CardTitle>
            </CardHeader>
            <CardContent>
              <ValveControl 
                deviceId={DEFAULT_DEVICE_ID} 
                onValveChange={handleValveChange} 
              />
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="automation">
          <Card>
            <CardHeader>
              <CardTitle>Automation Settings</CardTitle>
            </CardHeader>
            <CardContent>
              <AutomationSettings 
                deviceId={DEFAULT_DEVICE_ID} 
              />
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="profiles">
          <Card>
            <CardHeader>
              <CardTitle>Advanced Watering Profiles</CardTitle>
            </CardHeader>
            <CardContent>
              <WateringProfiles deviceId={DEFAULT_DEVICE_ID} />
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle>Valve History</CardTitle>
            </CardHeader>
            <CardContent>
              <ValveHistory 
                valveHistory={valveHistory || []}
                isLoading={isLoadingValveHistory}
                pagination={valveHistoryPagination || { total: 0, page: 1, limit: 5, pages: 1 }}
                onPageChange={handleValveHistoryPageChange}
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
} 