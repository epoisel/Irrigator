'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Edit2, Trash2, Flower2 } from 'lucide-react';
import { toast } from 'sonner';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';
import { Zone, deleteZone, Plant as PlantType, deletePlant } from '@/app/services/api';
import { ZoneEditDialog } from './ZoneEditDialog';
import { PlantDialog } from './PlantDialog';
import { PlantList } from './PlantList';

interface ZoneCardProps {
  zone: Zone;
  onUpdate: () => void;
}

export function ZoneCard({ zone, onUpdate }: ZoneCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [isAddingPlant, setIsAddingPlant] = useState(false);
  const [selectedPlant, setSelectedPlant] = useState<PlantType | null>(null);

  const handleDelete = async () => {
    try {
      await deleteZone(zone.id);
      toast.success('Zone deleted successfully');
      onUpdate();
    } catch (error) {
      toast.error('Failed to delete zone');
    }
  };

  const handleDeletePlant = async (plantId: number) => {
    try {
      await deletePlant(zone.id, plantId);
      toast.success('Plant deleted successfully');
      onUpdate();
    } catch (error) {
      toast.error('Failed to delete plant');
    }
  };

  const handleEditPlant = (plant: PlantType) => {
    setSelectedPlant(plant);
    setIsAddingPlant(true);
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-2xl font-bold">{zone.name}</CardTitle>
        <div className="flex space-x-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() => {
              setSelectedPlant(null);
              setIsAddingPlant(true);
            }}
          >
            <Flower2 className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            onClick={() => setIsEditing(true)}
          >
            <Edit2 className="h-4 w-4" />
          </Button>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="outline" size="icon">
                <Trash2 className="h-4 w-4" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                <AlertDialogDescription>
                  This action cannot be undone. This will permanently delete the zone
                  and all its associated plants and history.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleDelete}>Delete</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {zone.description && (
            <p className="text-sm text-muted-foreground">{zone.description}</p>
          )}
          <div className="flex justify-between text-sm">
            <span>Size: {zone.width}m × {zone.length}m</span>
            <span>{zone.plants?.length || 0} plants</span>
          </div>
          {zone.device_id && (
            <div className="text-sm text-muted-foreground">
              Device ID: {zone.device_id}
            </div>
          )}

          {zone.plants && (
            <PlantList
              plants={zone.plants}
              onDelete={handleDeletePlant}
              onEdit={handleEditPlant}
            />
          )}
        </div>
      </CardContent>

      <ZoneEditDialog
        zone={zone}
        open={isEditing}
        onOpenChange={setIsEditing}
        onZoneUpdated={onUpdate}
      />

      <PlantDialog
        zoneId={zone.id}
        open={isAddingPlant}
        onOpenChange={setIsAddingPlant}
        onPlantAdded={onUpdate}
        plant={selectedPlant}
      />
    </Card>
  );
} 