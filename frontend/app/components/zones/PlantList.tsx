'use client';

import { Plant } from '@/app/services/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Edit, Trash2 } from 'lucide-react';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';

interface PlantListProps {
  plants: Plant[];
  onDelete: (plantId: number) => void;
  onEdit: (plant: Plant) => void;
}

export function PlantList({ plants, onDelete, onEdit }: PlantListProps) {
  if (!plants || plants.length === 0) {
    return (
      <div className="text-sm text-muted-foreground text-center py-4">
        No plants added yet
      </div>
    );
  }

  return (
    <div className="space-y-4 mt-4">
      <h3 className="text-lg font-semibold">Plants</h3>
      <div className="grid grid-cols-1 gap-4">
        {plants.map((plant) => (
          <Card key={plant.id} className="relative">
            <CardContent className="pt-4">
              <div className="flex justify-between items-start">
                <div className="flex-grow pr-4">
                  <h4 className="font-medium">{plant.name}</h4>
                  <p className="text-sm text-muted-foreground">{plant.species}</p>
                  <div className="text-sm mt-1">
                    <p>Position: ({plant.position_x}m, {plant.position_y}m)</p>
                    <p>Planted: {new Date(plant.planting_date).toLocaleDateString()}</p>
                    {plant.water_requirements && (
                      <p>Water: {plant.water_requirements}</p>
                    )}
                  </div>
                  {plant.notes && (
                    <p className="text-sm mt-2 text-muted-foreground">{plant.notes}</p>
                  )}
                </div>
                <div className="flex-shrink-0 flex space-x-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onEdit(plant)}
                    className="h-8 w-8"
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Delete Plant</AlertDialogTitle>
                        <AlertDialogDescription>
                          Are you sure you want to delete {plant.name}? This action cannot be undone.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction onClick={() => onDelete(plant.id)}>
                          Delete
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
} 