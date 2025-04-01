'use client';

import { useState, useEffect } from 'react';
import { api, WateringProfile } from '../services/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Plus, Edit, Trash2, Check, Clock, Droplet } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { toast } from 'sonner';
import { ProfileDialog } from './ProfileDialog';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface WateringProfilesProps {
  deviceId: string;
}

export default function WateringProfiles({ deviceId }: WateringProfilesProps) {
  const [profiles, setProfiles] = useState<WateringProfile[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedProfile, setSelectedProfile] = useState<WateringProfile | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState<boolean>(false);
  
  const loadProfiles = async () => {
    try {
      setIsLoading(true);
      const data = await api.getWateringProfiles(deviceId);
      setProfiles(data);
    } catch (error) {
      console.error('Error loading profiles:', error);
      toast.error('Failed to load watering profiles');
    } finally {
      setIsLoading(false);
    }
  };
  
  useEffect(() => {
    loadProfiles();
  }, [deviceId]);
  
  const handleAddProfile = () => {
    setSelectedProfile(null);
    setIsDialogOpen(true);
  };
  
  const handleEditProfile = (profile: WateringProfile) => {
    setSelectedProfile(profile);
    setIsDialogOpen(true);
  };
  
  const handleDeleteProfile = async (profileId: number) => {
    try {
      await api.deleteWateringProfile(profileId);
      toast.success('Profile deleted successfully');
      loadProfiles();
    } catch (error) {
      console.error('Error deleting profile:', error);
      toast.error('Failed to delete profile');
    }
  };
  
  const handleSetDefault = async (profileId: number) => {
    try {
      await api.setDefaultProfile(profileId);
      toast.success('Profile set as default');
      loadProfiles();
    } catch (error) {
      console.error('Error setting default profile:', error);
      toast.error('Failed to set profile as default');
    }
  };
  
  const formatDuration = (seconds: number) => {
    if (seconds < 60) {
      return `${seconds} seconds`;
    } else if (seconds < 3600) {
      return `${Math.floor(seconds / 60)} minutes`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours} hour${hours > 1 ? 's' : ''}${minutes > 0 ? ` ${minutes} min` : ''}`;
    }
  };
  
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Watering Profiles</h2>
        <Button onClick={handleAddProfile} size="sm">
          <Plus className="mr-2 h-4 w-4" />
          Add Profile
        </Button>
      </div>
      
      {isLoading ? (
        <div className="flex justify-center py-8">
          <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
        </div>
      ) : profiles.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-muted-foreground">No watering profiles found. Create your first profile to customize watering behaviors.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {profiles.map((profile) => (
            <Card key={profile.id} className={profile.is_default ? 'border-2 border-blue-500' : ''}>
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="flex items-center">
                      {profile.name}
                      {profile.is_default && (
                        <Badge variant="default" className="ml-2 bg-blue-500">Default</Badge>
                      )}
                    </CardTitle>
                    <p className="text-xs text-muted-foreground mt-1">
                      Updated {formatDistanceToNow(new Date(profile.updated_at), { addSuffix: true })}
                    </p>
                  </div>
                  <div className="flex space-x-1">
                    {!profile.is_default && (
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button 
                              variant="ghost" 
                              size="icon" 
                              onClick={() => handleSetDefault(profile.id)}
                            >
                              <Check className="h-4 w-4" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>Set as default</TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    )}
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            onClick={() => handleEditProfile(profile)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Edit profile</TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                    
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Delete Profile</AlertDialogTitle>
                          <AlertDialogDescription>
                            Are you sure you want to delete the "{profile.name}" profile? This action cannot be undone.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Cancel</AlertDialogCancel>
                          <AlertDialogAction 
                            onClick={() => handleDeleteProfile(profile.id)}
                            className="bg-red-500 hover:bg-red-600"
                          >
                            Delete
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="flex items-center">
                    <Droplet className="h-4 w-4 mr-2 text-blue-500" />
                    <span className="text-muted-foreground">Watering:</span>
                    <span className="ml-auto font-medium">{formatDuration(profile.watering_duration)}</span>
                  </div>
                  <div className="flex items-center">
                    <Clock className="h-4 w-4 mr-2 text-amber-500" />
                    <span className="text-muted-foreground">Wait time:</span>
                    <span className="ml-auto font-medium">{formatDuration(profile.wicking_wait_time)}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-muted-foreground">Max cycles:</span>
                    <span className="ml-auto font-medium">{profile.max_daily_cycles} per day</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-muted-foreground">Check interval:</span>
                    <span className="ml-auto font-medium">{formatDuration(profile.sensing_interval)}</span>
                  </div>
                </div>
                
                {(profile.reservoir_limit || profile.max_watering_per_day) && (
                  <div className="mt-3 pt-3 border-t border-gray-100 text-sm">
                    <h4 className="font-medium mb-1">Reservoir limits:</h4>
                    <ul className="text-muted-foreground">
                      {profile.reservoir_volume && profile.reservoir_limit && (
                        <li>Volume: {profile.reservoir_volume} ml (max {profile.reservoir_limit}%)</li>
                      )}
                      {profile.max_watering_per_day && (
                        <li>Max watering: {profile.max_watering_per_day} minutes/day</li>
                      )}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      
      <ProfileDialog
        open={isDialogOpen}
        onOpenChange={setIsDialogOpen}
        profile={selectedProfile}
        deviceId={deviceId}
        onProfileSaved={loadProfiles}
      />
    </div>
  );
} 