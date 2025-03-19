'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { createZone } from '@/app/services/api';

interface ZoneCreationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onZoneCreated: () => void;
}

export function ZoneCreationDialog({
  open,
  onOpenChange,
  onZoneCreated,
}: ZoneCreationDialogProps) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    device_id: '',
    width: '',
    length: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await createZone({
        name: formData.name,
        description: formData.description || undefined,
        device_id: formData.device_id || undefined,
        width: Number(formData.width),
        length: Number(formData.length),
      });

      toast.success('Zone created successfully');

      setFormData({
        name: '',
        description: '',
        device_id: '',
        width: '',
        length: '',
      });

      onZoneCreated();
      onOpenChange(false);
    } catch (error) {
      toast.error('Failed to create zone');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New Zone</DialogTitle>
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
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                setFormData((prev) => ({ ...prev, description: e.target.value }))
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="device_id">Device ID (optional)</Label>
            <Input
              id="device_id"
              value={formData.device_id}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setFormData((prev) => ({ ...prev, device_id: e.target.value }))
              }
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="width">Width (meters)</Label>
              <Input
                id="width"
                type="number"
                min="0.1"
                step="0.1"
                value={formData.width}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setFormData((prev) => ({ ...prev, width: e.target.value }))
                }
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="length">Length (meters)</Label>
              <Input
                id="length"
                type="number"
                min="0.1"
                step="0.1"
                value={formData.length}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setFormData((prev) => ({ ...prev, length: e.target.value }))
                }
                required
              />
            </div>
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
              {isSubmitting ? 'Creating...' : 'Create Zone'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
} 