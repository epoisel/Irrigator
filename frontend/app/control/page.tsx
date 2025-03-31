'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { api, ValveAction } from '../services/api';
import ValveControl from '../components/ValveControl';
import AutomationSettings from '../components/AutomationSettings';
import ValveHistory from '../components/ValveHistory';
import TimeRangeSelector from '../components/TimeRangeSelector';

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
          valveHistoryPagination.page,
          valveHistoryPagination.limit
        );
        
        setValveHistory(response.data);
        setValveHistoryPagination(response.pagination);
      } catch (err) {
        console.error('Error fetching valve history:', err);
      } finally {
        setIsLoadingValveHistory(false);
      }
    };
    
    fetchValveHistory();
  }, [selectedDays, valveHistoryPagination.page, valveHistoryPagination.limit]);
  
  // Handle valve state change
  const handleValveChange = () => {
    // Refresh valve history when valve state changes
    const fetchValveHistory = async () => {
      try {
        const response = await api.getValveHistory(
          DEFAULT_DEVICE_ID, 
          selectedDays,
          valveHistoryPagination.page,
          valveHistoryPagination.limit
        );
        
        setValveHistory(response.data);
        setValveHistoryPagination(response.pagination);
      } catch (err) {
        console.error('Error fetching valve history:', err);
      }
    };
    
    fetchValveHistory();
  };
  
  // Handle valve history page change
  const handleValveHistoryPageChange = (page: number) => {
    setValveHistoryPagination(prev => ({
      ...prev,
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
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="manual">Manual Control</TabsTrigger>
          <TabsTrigger value="automation">Automation Rules</TabsTrigger>
        </TabsList>
        
        <TabsContent value="manual">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="md:col-span-2">
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
            
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle>Valve History</CardTitle>
              </CardHeader>
              <CardContent>
                <ValveHistory 
                  valveHistory={valveHistory} 
                  isLoading={isLoadingValveHistory}
                  pagination={valveHistoryPagination}
                  onPageChange={handleValveHistoryPageChange}
                />
              </CardContent>
            </Card>
          </div>
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
      </Tabs>
    </div>
  );
} 