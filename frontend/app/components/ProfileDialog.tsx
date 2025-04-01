'use client';

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
// Commented out until shadcn components are installed
// import { Switch } from '@/components/ui/switch';
// import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import { api, WateringProfile, CreateWateringProfileData } from '../services/api';

// Helper function to convert minutes to seconds
const minutesToSeconds = (minutes: number): number => {
  return minutes * 60;
};

// Helper function to convert seconds to minutes
const secondsToMinutes = (seconds: number): number => {
  return seconds / 60;
};

interface ProfileDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  profile: WateringProfile | null;
  deviceId: string;
  onProfileSaved: () => void;
}

export function ProfileDialog({ 
  open, 
  onOpenChange, 
  profile, 
  deviceId,
  onProfileSaved 
}: ProfileDialogProps) {
  const [formData, setFormData] = useState<CreateWateringProfileData>({
    name: '',
    device_id: deviceId,
    is_default: 0,
    watering_duration: 300,
    wicking_wait_time: 3600,
    max_daily_cycles: 4,
    sensing_interval: 300,
    reservoir_limit: undefined,
    reservoir_volume: undefined,
    max_watering_per_day: undefined
  });
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isDefault, setIsDefault] = useState(false);
  
  useEffect(() => {
    // If dialog is opened and there's a profile, set form data
    if (open && profile) {
      setFormData({
        name: profile.name,
        device_id: profile.device_id,
        is_default: profile.is_default,
        watering_duration: profile.watering_duration,
        wicking_wait_time: profile.wicking_wait_time,
        max_daily_cycles: profile.max_daily_cycles,
        sensing_interval: profile.sensing_interval,
        reservoir_limit: profile.reservoir_limit || undefined,
        reservoir_volume: profile.reservoir_volume || undefined,
        max_watering_per_day: profile.max_watering_per_day || undefined
      });
      setIsDefault(profile.is_default === 1);
      
      // Check if any advanced settings are set
      if (profile.reservoir_limit || profile.reservoir_volume || profile.max_watering_per_day) {
        setShowAdvanced(true);
      }
    } else if (open) {
      // Reset form for new profile
      setFormData({
        name: '',
        device_id: deviceId,
        is_default: 0,
        watering_duration: 300,
        wicking_wait_time: 3600,
        max_daily_cycles: 4,
        sensing_interval: 300,
        reservoir_limit: undefined,
        reservoir_volume: undefined,
        max_watering_per_day: undefined
      });
      setIsDefault(false);
      setShowAdvanced(false);
    }
  }, [open, profile, deviceId]);
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'number') {
      const numericValue = value === '' ? undefined : Number(value);
      setFormData(prev => ({ ...prev, [name]: numericValue }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };
  
  const handleSwitchChange = (checked: boolean) => {
    setIsDefault(checked);
    setFormData(prev => ({ ...prev, is_default: checked ? 1 : 0 }));
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name) {
      toast.error('Profile name is required');
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      if (profile) {
        // Update existing profile
        await api.updateWateringProfile(profile.id, formData);
        toast.success('Profile updated successfully');
      } else {
        // Create new profile
        await api.createWateringProfile(formData);
        toast.success('Profile created successfully');
      }
      
      onOpenChange(false);
      onProfileSaved();
    } catch (error) {
      console.error('Error saving profile:', error);
      toast.error('Failed to save profile');
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{profile ? 'Edit Profile' : 'Create Profile'}</DialogTitle>
            <DialogDescription>
              Configure how your irrigation system manages watering cycles and sensors.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-4 items-center gap-2">
              <Label htmlFor="name" className="col-span-1">Name</Label>
              <Input
                id="name"
                name="name"
                placeholder="Profile name"
                value={formData.name}
                onChange={handleInputChange}
                className="col-span-3"
                required
              />
            </div>
            
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="is_default">Default Profile</Label>
                <p className="text-xs text-muted-foreground">Make this the active profile</p>
              </div>
              {/* We need to install the shadcn/ui switch component */}
              <input
                id="is_default"
                type="checkbox"
                checked={isDefault}
                onChange={(e) => handleSwitchChange(e.target.checked)}
                className="h-4 w-4"
              />
            </div>
            
            <hr className="my-4" />
            
            <div className="grid grid-cols-4 items-center gap-2">
              <Label htmlFor="watering_duration" className="col-span-2">
                Watering Duration
              </Label>
              <div className="col-span-2 flex items-center">
                <Input
                  id="watering_duration"
                  name="watering_duration_minutes"
                  type="number"
                  value={secondsToMinutes(formData.watering_duration || 300)}
                  onChange={(e) => {
                    const minutes = Number(e.target.value);
                    setFormData(prev => ({ 
                      ...prev, 
                      watering_duration: minutesToSeconds(minutes || 0) 
                    }));
                  }}
                  min="0.5"
                  step="0.5"
                  className="mr-2"
                />
                <span className="text-sm">minutes</span>
              </div>
            </div>
            
            <div className="grid grid-cols-4 items-center gap-2">
              <Label htmlFor="wicking_wait_time" className="col-span-2">
                Wait Time Between Cycles
              </Label>
              <div className="col-span-2 flex items-center">
                <Input
                  id="wicking_wait_time"
                  name="wicking_wait_time_minutes"
                  type="number"
                  value={secondsToMinutes(formData.wicking_wait_time || 3600)}
                  onChange={(e) => {
                    const minutes = Number(e.target.value);
                    setFormData(prev => ({ 
                      ...prev, 
                      wicking_wait_time: minutesToSeconds(minutes || 0) 
                    }));
                  }}
                  min="5"
                  step="5"
                  className="mr-2"
                />
                <span className="text-sm">minutes</span>
              </div>
            </div>
            
            <div className="grid grid-cols-4 items-center gap-2">
              <Label htmlFor="max_daily_cycles" className="col-span-2">
                Max Daily Cycles
              </Label>
              <div className="col-span-2">
                <Input
                  id="max_daily_cycles"
                  name="max_daily_cycles"
                  type="number"
                  value={formData.max_daily_cycles || 4}
                  onChange={handleInputChange}
                  min="1"
                  max="24"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-4 items-center gap-2">
              <Label htmlFor="sensing_interval" className="col-span-2">
                Sensing Interval
              </Label>
              <div className="col-span-2 flex items-center">
                <Input
                  id="sensing_interval"
                  name="sensing_interval_minutes"
                  type="number"
                  value={secondsToMinutes(formData.sensing_interval || 300)}
                  onChange={(e) => {
                    const minutes = Number(e.target.value);
                    setFormData(prev => ({ 
                      ...prev, 
                      sensing_interval: minutesToSeconds(minutes || 0) 
                    }));
                  }}
                  min="1"
                  step="1"
                  className="mr-2"
                />
                <span className="text-sm">minutes</span>
              </div>
            </div>
            
            <div className="mt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowAdvanced(!showAdvanced)}
                size="sm"
              >
                {showAdvanced ? "Hide Advanced Settings" : "Show Advanced Settings"}
              </Button>
            </div>
            
            {showAdvanced && (
              <div className="space-y-4 mt-2">
                <hr className="my-4" />
                <h4 className="text-sm font-medium">Reservoir Management</h4>
                
                <div className="grid grid-cols-4 items-center gap-2">
                  <Label htmlFor="reservoir_volume" className="col-span-2">
                    Reservoir Volume (ml)
                  </Label>
                  <div className="col-span-2">
                    <Input
                      id="reservoir_volume"
                      name="reservoir_volume"
                      type="number"
                      value={formData.reservoir_volume || ''}
                      onChange={handleInputChange}
                      placeholder="Optional"
                      min="0"
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-4 items-center gap-2">
                  <Label htmlFor="reservoir_limit" className="col-span-2">
                    Usage Limit (%)
                  </Label>
                  <div className="col-span-2">
                    <Input
                      id="reservoir_limit"
                      name="reservoir_limit"
                      type="number"
                      value={formData.reservoir_limit || ''}
                      onChange={handleInputChange}
                      placeholder="Optional"
                      min="0"
                      max="100"
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-4 items-center gap-2">
                  <Label htmlFor="max_watering_per_day" className="col-span-2">
                    Max Watering (min/day)
                  </Label>
                  <div className="col-span-2">
                    <Input
                      id="max_watering_per_day"
                      name="max_watering_per_day"
                      type="number"
                      value={formData.max_watering_per_day || ''}
                      onChange={handleInputChange}
                      placeholder="Optional"
                      min="0"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
          
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : profile ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
} 