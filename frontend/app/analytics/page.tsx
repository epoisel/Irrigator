'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { api, MoistureData } from '../services/api';
import MoistureChart from '../components/MoistureChart';
import PlantMeasurements from '../components/PlantMeasurements';
import TimeRangeSelector from '../components/TimeRangeSelector';
import { LucideDroplets, LineChart, FlowerIcon } from 'lucide-react';

// Default device ID - this would typically come from user selection or configuration
const DEFAULT_DEVICE_ID = process.env.NEXT_PUBLIC_DEFAULT_DEVICE_ID || 'pico_01';

export default function AnalyticsPage() {
  const [moistureData, setMoistureData] = useState<MoistureData[]>([]);
  const [selectedDays, setSelectedDays] = useState<number>(7);
  const [isLoadingMoisture, setIsLoadingMoisture] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Load moisture data
  useEffect(() => {
    const fetchMoistureData = async () => {
      try {
        setIsLoadingMoisture(true);
        setError(null);
        
        const data = await api.getMoistureData(DEFAULT_DEVICE_ID, selectedDays);
        setMoistureData(data);
      } catch (err) {
        setError('Failed to load moisture data');
        console.error('Error fetching moisture data:', err);
      } finally {
        setIsLoadingMoisture(false);
      }
    };
    
    fetchMoistureData();
  }, [selectedDays]);

  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
        <TimeRangeSelector 
          selectedDays={selectedDays} 
          onSelectDays={setSelectedDays} 
        />
      </div>
      
      <Tabs defaultValue="moisture" className="mb-6">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="moisture" className="flex items-center">
            <LucideDroplets className="mr-2 h-4 w-4" />
            Moisture Analytics
          </TabsTrigger>
          <TabsTrigger value="growth" className="flex items-center">
            <FlowerIcon className="mr-2 h-4 w-4" />
            Plant Growth Tracking
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="moisture">
          <div className="grid grid-cols-1 gap-6">
            {error && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                <p>{error}</p>
              </div>
            )}
            
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <LineChart className="mr-2 h-5 w-5" />
                  Moisture Trends
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <MoistureChart 
                    moistureData={moistureData} 
                    isLoading={isLoadingMoisture} 
                  />
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>Moisture Data Statistics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="text-sm text-gray-500">Average Moisture</div>
                    <div className="text-2xl font-bold">
                      {moistureData.length > 0 
                        ? `${(moistureData.reduce((sum, item) => sum + item.moisture, 0) / moistureData.length).toFixed(1)}%`
                        : 'No data'}
                    </div>
                  </div>
                  
                  <div className="bg-green-50 p-4 rounded-lg">
                    <div className="text-sm text-gray-500">Highest Moisture</div>
                    <div className="text-2xl font-bold">
                      {moistureData.length > 0 
                        ? `${Math.max(...moistureData.map(item => item.moisture)).toFixed(1)}%`
                        : 'No data'}
                    </div>
                  </div>
                  
                  <div className="bg-red-50 p-4 rounded-lg">
                    <div className="text-sm text-gray-500">Lowest Moisture</div>
                    <div className="text-2xl font-bold">
                      {moistureData.length > 0 
                        ? `${Math.min(...moistureData.map(item => item.moisture)).toFixed(1)}%`
                        : 'No data'}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        
        <TabsContent value="growth">
          <Card>
            <CardContent className="pt-6">
              <PlantMeasurements deviceId={DEFAULT_DEVICE_ID} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
} 