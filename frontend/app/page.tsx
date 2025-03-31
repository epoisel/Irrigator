'use client';

import { useState, useEffect } from 'react';
import { api, MoistureData } from './services/api';
import MoistureCard from './components/MoistureCard';
import ValveControl from './components/ValveControl';
import MoistureChart from './components/MoistureChart';
import TimeRangeSelector from './components/TimeRangeSelector';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Map, Droplet, Flower2 } from 'lucide-react';
import Link from 'next/link';

// Default device ID - this would typically come from user selection or configuration
const DEFAULT_DEVICE_ID = process.env.NEXT_PUBLIC_DEFAULT_DEVICE_ID || 'pico_01';

export default function Home() {
  // State for data
  const [moistureData, setMoistureData] = useState<MoistureData[]>([]);
  const [currentMoisture, setCurrentMoisture] = useState<MoistureData | null>(null);
  
  // State for UI
  const [selectedDays, setSelectedDays] = useState<number>(1);
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
  
  return (
    <div className="space-y-8">
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          <p>{error}</p>
        </div>
      )}
      
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">System Dashboard</h1>
        <TimeRangeSelector 
          selectedDays={selectedDays} 
          onSelectDays={setSelectedDays} 
        />
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <MoistureCard 
          moistureData={currentMoisture} 
          isLoading={isLoadingMoisture} 
        />
        <ValveControl 
          deviceId={DEFAULT_DEVICE_ID} 
          onValveChange={() => {}} 
        />
      </div>
      
      <div className="mb-6">
        <MoistureChart 
          moistureData={moistureData} 
          isLoading={isLoadingMoisture} 
        />
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <Link href="/control" className="block">
          <Card className="h-full hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Droplet className="mr-2 h-5 w-5 text-blue-500" />
                Control Center
              </CardTitle>
              <CardDescription>Manage irrigation system settings</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Control valves, modify automation rules, and configure timing settings
              </p>
            </CardContent>
            <CardFooter>
              <Button variant="outline" className="w-full">Go to Control</Button>
            </CardFooter>
          </Card>
        </Link>
        
        <Link href="/zones" className="block">
          <Card className="h-full hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Map className="mr-2 h-5 w-5 text-green-500" />
                Garden Zones
              </CardTitle>
              <CardDescription>Manage garden zones and plants</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Add, edit and monitor zones in your garden and the plants within them
              </p>
            </CardContent>
            <CardFooter>
              <Button variant="outline" className="w-full">Manage Zones</Button>
            </CardFooter>
          </Card>
        </Link>
        
        <Link href="/analytics" className="block">
          <Card className="h-full hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center">
                <LineChart className="mr-2 h-5 w-5 text-purple-500" />
                Analytics
              </CardTitle>
              <CardDescription>View detailed system data</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Explore moisture trends, watering history, and plant growth data
              </p>
            </CardContent>
            <CardFooter>
              <Button variant="outline" className="w-full">View Analytics</Button>
            </CardFooter>
          </Card>
        </Link>
      </div>
    </div>
  );
} 