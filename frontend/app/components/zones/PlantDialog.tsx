'use client';

import { useEffect, useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { createPlant, Plant, updatePlant } from '@/app/services/api';

interface PlantDialogProps {
  zoneId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onPlantAdded: () => void;
  plant?: Plant | null;
}

export function PlantDialog({
  zoneId,
  open,
  onOpenChange,
  onPlantAdded,
  plant,
}: PlantDialogProps) {
  const [formData, setFormData] = useState({
    name: '',
    species: '',
    planting_date: new Date().toISOString().split('T')[0],
    position_x: '',
    position_y: '',
    notes: '',
    water_requirements: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (open && plant) {
      setFormData({
        name: plant.name,
        species: plant.species,
        planting_date: plant.planting_date,
        position_x: String(plant.position_x),
        position_y: String(plant.position_y),
        notes: plant.notes || '',
        water_requirements: plant.water_requirements || '',
      });
    } else if (open) {
      setFormData({
        name: '',
        species: '',
        planting_date: new Date().toISOString().split('T')[0],
        position_x: '',
        position_y: '',
        notes: '',
        water_requirements: '',
      });
    }
  }, [open, plant]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const plantData = {
        name: formData.name,
        species: formData.species,
        planting_date: formData.planting_date,
        position_x: Number(formData.position_x),
        position_y: Number(formData.position_y),
        notes: formData.notes || undefined,
        water_requirements: formData.water_requirements || undefined,
      };

      if (plant) {
        await updatePlant(zoneId, plant.id, plantData);
        toast.success('Plant updated successfully');
      } else {
        await createPlant(zoneId, plantData);
        toast.success('Plant added successfully');
      }

      onPlantAdded();
      onOpenChange(false);
    } catch (error) {
      toast.error(plant ? 'Failed to update plant' : 'Failed to add plant');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{plant ? 'Edit Plant' : 'Add New Plant'}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setFormData((prev) => ({ ...prev, name: e.target.value }))
              }
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="species">Species</Label>
            <Input
              id="species"
              value={formData.species}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setFormData((prev) => ({ ...prev, species: e.target.value }))
              }
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="planting_date">Planting Date</Label>
            <Input
              id="planting_date"
              type="date"
              value={formData.planting_date}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setFormData((prev) => ({ ...prev, planting_date: e.target.value }))
              }
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="position_x">Position X (meters)</Label>
              <Input
                id="position_x"
                type="number"
                min="0"
                step="0.1"
                value={formData.position_x}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setFormData((prev) => ({ ...prev, position_x: e.target.value }))
                }
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="position_y">Position Y (meters)</Label>
              <Input
                id="position_y"
                type="number"
                min="0"
                step="0.1"
                value={formData.position_y}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setFormData((prev) => ({ ...prev, position_y: e.target.value }))
                }
                required
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="water_requirements">Water Requirements</Label>
            <Input
              id="water_requirements"
              placeholder="e.g., Daily, Twice weekly, etc."
              value={formData.water_requirements}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setFormData((prev) => ({
                  ...prev,
                  water_requirements: e.target.value,
                }))
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="notes">Notes</Label>
            <Textarea
              id="notes"
              value={formData.notes}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                setFormData((prev) => ({ ...prev, notes: e.target.value }))
              }
              placeholder="Add any special care instructions or notes..."
            />
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? (plant ? 'Saving...' : 'Adding...') : (plant ? 'Save Changes' : 'Add Plant')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
} 