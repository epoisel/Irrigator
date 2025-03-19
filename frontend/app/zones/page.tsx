'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Plus } from 'lucide-react';
import { ZoneCreationDialog } from '../components/zones/ZoneCreationDialog';
import { ZoneCard } from '../components/zones/ZoneCard';
import { useToast } from '@/components/ui/use-toast';
import { fetchZones } from '../services/api';

interface Zone {
  id: number;
  name: string;
  description: string | null;
  device_id: string | null;
  width: number;
  length: number;
  created_at: string;
  updated_at: string;
  plants?: Plant[];
}

interface Plant {
  id: number;
  name: string;
  species: string;
  planting_date: string;
  position_x: number;
  position_y: number;
  notes: string | null;
  water_requirements: string | null;
}

export default function ZonesPage() {
  const [zones, setZones] = useState<Zone[]>([]);
  const [isCreatingZone, setIsCreatingZone] = useState(false);
  const { toast } = useToast();

  const loadZones = async () => {
    try {
      const zonesData = await fetchZones();
      setZones(zonesData);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load zones',
        variant: 'destructive',
      });
    }
  };

  useEffect(() => {
    loadZones();
  }, []);

  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Garden Zones</h1>
        <Button onClick={() => setIsCreatingZone(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Zone
        </Button>
      </div>

      {zones.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>No Zones Yet</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              Create your first garden zone to start planning and monitoring your plants.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {zones.map((zone) => (
            <ZoneCard
              key={zone.id}
              zone={zone}
              onUpdate={loadZones}
            />
          ))}
        </div>
      )}

      <ZoneCreationDialog
        open={isCreatingZone}
        onOpenChange={setIsCreatingZone}
        onZoneCreated={loadZones}
      />
    </div>
  );
} 