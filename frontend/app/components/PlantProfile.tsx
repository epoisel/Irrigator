'use client';

import React, { useState, useEffect } from 'react';
import { PlantMeasurement, PlantPhoto, getMeasurements, updateMeasurement, deleteMeasurement, uploadPhoto, getPhotos, getPhotoUrl, deletePhoto } from '../services/measurements';
import { Line } from 'react-chartjs-2';
import Image from 'next/image';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import type { CheckedState } from "@radix-ui/react-checkbox";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface Props {
    deviceId: string;
    plantName: string;
    isOpen: boolean;
    onClose: () => void;
}

interface PlantSummary {
    totalMeasurements: number;
    averageHealth: number;
    growthRate: number;
    careHistory: {
        fertilized: number;
        pruned: number;
    };
    latestHeight?: number;
    heightGrowth?: number;
}

const PlantProfile: React.FC<Props> = ({ deviceId, plantName, isOpen, onClose }) => {
    const [measurements, setMeasurements] = useState<PlantMeasurement[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [editingMeasurement, setEditingMeasurement] = useState<PlantMeasurement | null>(null);
    const [deletingMeasurement, setDeletingMeasurement] = useState<PlantMeasurement | null>(null);
    const [summary, setSummary] = useState<PlantSummary | null>(null);
    const [selectedPhoto, setSelectedPhoto] = useState<PlantPhoto | null>(null);
    const [uploadingPhoto, setUploadingPhoto] = useState(false);

    useEffect(() => {
        if (isOpen) {
            fetchMeasurements();
        }
    }, [isOpen, deviceId, plantName]);

    useEffect(() => {
        if (measurements.length > 0) {
            calculateSummary();
        }
    }, [measurements]);

    const fetchMeasurements = async () => {
        try {
            setLoading(true);
            const data = await getMeasurements(deviceId);
            const filteredData = data.filter((m: PlantMeasurement) => m.plant_name === plantName);
            setMeasurements(filteredData);
        } catch (err) {
            setError('Failed to fetch measurements');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const calculateSummary = () => {
        const sortedMeasurements = [...measurements].sort((a, b) => 
            new Date(a.timestamp || '').getTime() - new Date(b.timestamp || '').getTime()
        );

        let growthRate = 0;
        if (sortedMeasurements.length >= 2) {
            const firstMeasurement = sortedMeasurements[0];
            const lastMeasurement = sortedMeasurements[sortedMeasurements.length - 1];
            
            if (firstMeasurement?.height && lastMeasurement?.height && firstMeasurement.timestamp && lastMeasurement.timestamp) {
                const daysDiff = (new Date(lastMeasurement.timestamp).getTime() - new Date(firstMeasurement.timestamp).getTime()) / (1000 * 60 * 60 * 24);
                if (daysDiff > 0) {
                    growthRate = (lastMeasurement.height - firstMeasurement.height) / daysDiff;
                }
            }
        }

        const lastMeasurement = sortedMeasurements[sortedMeasurements.length - 1];
        const firstMeasurement = sortedMeasurements[0];

        const summary: PlantSummary = {
            totalMeasurements: measurements.length,
            averageHealth: measurements.reduce((sum: number, m: PlantMeasurement) => sum + (m.health_score || 0), 0) / measurements.length || 0,
            growthRate,
            careHistory: {
                fertilized: measurements.filter((m: PlantMeasurement) => m.fertilized === true).length,
                pruned: measurements.filter((m: PlantMeasurement) => m.pruned === true).length,
            },
            latestHeight: lastMeasurement?.height,
            heightGrowth: lastMeasurement?.height && firstMeasurement?.height
                ? lastMeasurement.height - firstMeasurement.height
                : undefined
        };

        setSummary(summary);
    };

    const handleEdit = (measurement: PlantMeasurement) => {
        setEditingMeasurement(measurement);
    };

    const handleSave = async () => {
        if (!editingMeasurement?.id) return;

        try {
            setLoading(true);
            const updatedMeasurement: PlantMeasurement = {
                ...editingMeasurement,
                height: editingMeasurement.height || 0,
                leaf_count: editingMeasurement.leaf_count || 0,
                fertilized: editingMeasurement.fertilized === true,
                pruned: editingMeasurement.pruned === true,
                id: editingMeasurement.id
            };
            
            if (typeof updatedMeasurement.id === 'number') {
                await updateMeasurement(updatedMeasurement.id, updatedMeasurement);
                setEditingMeasurement(null);
                await fetchMeasurements();
            }
        } catch (err) {
            setError('Failed to update measurement');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!editingMeasurement) return;
        const { name, value } = e.target;
        setEditingMeasurement({
            ...editingMeasurement,
            [name]: value
        });
    };

    const handleCheckboxChange = (field: 'fertilized' | 'pruned') => (checked: CheckedState) => {
        if (!editingMeasurement) return;
        setEditingMeasurement({
            ...editingMeasurement,
            [field]: checked === true
        });
    };

    const handleDelete = async (measurement: PlantMeasurement) => {
        if (!measurement.id) {
            setError('Cannot delete measurement: Invalid ID');
            return;
        }

        try {
            setError(null); // Clear any previous errors
            setLoading(true);
            
            await deleteMeasurement(measurement.id);
            setDeletingMeasurement(null);
            
            // Refresh the measurements list
            await fetchMeasurements();
            
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to delete measurement';
            setError(errorMessage);
            console.error('Delete error:', err);
        } finally {
            setLoading(false);
        }
    };

    const handlePhotoUpload = async (measurementId: number, event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        try {
            setUploadingPhoto(true);
            await uploadPhoto(measurementId, file);
            await fetchMeasurements();
        } catch (err) {
            setError('Failed to upload photo');
            console.error(err);
        } finally {
            setUploadingPhoto(false);
        }
    };

    const handleDeletePhoto = async (photoId: number) => {
        try {
            setLoading(true);
            await deletePhoto(photoId);
            await fetchMeasurements();
            setSelectedPhoto(null);
        } catch (err) {
            setError('Failed to delete photo');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const chartData = {
        labels: measurements.map(m => new Date(m.timestamp!).toLocaleDateString()),
        datasets: [
            {
                label: 'Height (cm)',
                data: measurements.map(m => m.height),
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            },
            {
                label: 'Health Score',
                data: measurements.map(m => m.health_score),
                borderColor: 'rgb(255, 99, 132)',
                tension: 0.1
            }
        ]
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-4xl">
                <DialogHeader>
                    <DialogTitle>{plantName} - Plant Profile</DialogTitle>
                </DialogHeader>
                
                {error && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                        {error}
                    </div>
                )}

                <div className="space-y-6">
                    {/* Plant Summary */}
                    {summary && (
                        <div className="bg-white p-6 rounded-lg shadow">
                            <h3 className="text-lg font-semibold mb-4">Plant Summary</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <p className="text-sm text-gray-600">Total Measurements</p>
                                    <p className="text-lg font-medium">{summary.totalMeasurements}</p>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-600">Average Health Score</p>
                                    <p className="text-lg font-medium">{summary.averageHealth.toFixed(1)}</p>
                                </div>
                                {summary.growthRate !== 0 && (
                                    <div>
                                        <p className="text-sm text-gray-600">Growth Rate</p>
                                        <p className="text-lg font-medium">{summary.growthRate.toFixed(2)} cm/day</p>
                                    </div>
                                )}
                                {summary.heightGrowth !== undefined && (
                                    <div>
                                        <p className="text-sm text-gray-600">Total Growth</p>
                                        <p className="text-lg font-medium">{summary.heightGrowth.toFixed(1)} cm</p>
                                    </div>
                                )}
                                <div>
                                    <p className="text-sm text-gray-600">Care History</p>
                                    <p className="text-lg font-medium">
                                        Fertilized {summary.careHistory.fertilized} times<br />
                                        Pruned {summary.careHistory.pruned} times
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Growth Chart */}
                    <div className="bg-white p-6 rounded-lg shadow">
                        <h3 className="text-lg font-semibold mb-4">Growth History</h3>
                        <div className="h-64">
                            <Line
                                data={chartData}
                                options={{
                                    responsive: true,
                                    maintainAspectRatio: false,
                                    scales: {
                                        y: {
                                            beginAtZero: true
                                        }
                                    }
                                }}
                            />
                        </div>
                    </div>

                    {/* Photo Gallery */}
                    <div className="bg-white p-6 rounded-lg shadow">
                        <h3 className="text-lg font-semibold mb-4">Photo Gallery</h3>
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                            {measurements.map((measurement) => (
                                measurement.photos?.map((photo) => (
                                    <div key={photo.id} className="relative group">
                                        <Image
                                            src={getPhotoUrl(photo.id)}
                                            alt={`Plant photo from ${new Date(photo.timestamp).toLocaleDateString()}`}
                                            width={200}
                                            height={200}
                                            className="rounded-lg object-cover cursor-pointer"
                                            onClick={() => setSelectedPhoto(photo)}
                                        />
                                        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-opacity flex items-center justify-center opacity-0 group-hover:opacity-100">
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleDeletePhoto(photo.id);
                                                }}
                                                className="text-white bg-red-600 hover:bg-red-700 px-3 py-1 rounded-md"
                                            >
                                                Delete
                                            </button>
                                        </div>
                                    </div>
                                ))
                            ))}
                        </div>
                    </div>

                    {/* Measurement History Table */}
                    <div className="bg-white p-6 rounded-lg shadow overflow-x-auto">
                        <h3 className="text-lg font-semibold mb-4">Measurement History</h3>
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Height</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Leaf Count</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Health Score</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Photos</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {measurements.map((measurement) => (
                                    <tr key={measurement.id}>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {new Date(measurement.timestamp!).toLocaleDateString()}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {measurement.height ? `${measurement.height} cm` : '-'}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {measurement.leaf_count || '-'}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {measurement.health_score || '-'}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            <div className="flex items-center space-x-2">
                                                <span>{measurement.photos?.length || 0} photos</span>
                                                <label className="cursor-pointer bg-indigo-600 text-white px-2 py-1 rounded text-xs hover:bg-indigo-700">
                                                    Add Photo
                                                    <input
                                                        type="file"
                                                        accept="image/*"
                                                        className="hidden"
                                                        onChange={(e) => handlePhotoUpload(measurement.id!, e)}
                                                        disabled={uploadingPhoto}
                                                    />
                                                </label>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                                            <button
                                                onClick={() => handleEdit(measurement)}
                                                className="text-indigo-600 hover:text-indigo-900"
                                            >
                                                Edit
                                            </button>
                                            <button
                                                onClick={() => setDeletingMeasurement(measurement)}
                                                className="text-red-600 hover:text-red-900"
                                            >
                                                Delete
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Edit Measurement Dialog */}
                    {editingMeasurement && (
                        <Dialog open={!!editingMeasurement} onOpenChange={() => setEditingMeasurement(null)}>
                            <DialogContent>
                                <DialogHeader>
                                    <DialogTitle>Edit Measurement</DialogTitle>
                                </DialogHeader>
                                <form onSubmit={(e) => {
                                    e.preventDefault();
                                    handleSave();
                                }} className="space-y-4">
                                    <div className="space-y-4">
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="space-y-2">
                                                <Label htmlFor="height">Height (cm)</Label>
                                                <Input
                                                    id="height"
                                                    type="number"
                                                    name="height"
                                                    value={editingMeasurement.height || ''}
                                                    onChange={handleInputChange}
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <Label htmlFor="leaf_count">Leaf Count</Label>
                                                <Input
                                                    id="leaf_count"
                                                    type="number"
                                                    name="leaf_count"
                                                    value={editingMeasurement.leaf_count || ''}
                                                    onChange={handleInputChange}
                                                />
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="space-y-2">
                                                <Label htmlFor="stem_thickness">Stem Thickness (mm)</Label>
                                                <Input
                                                    id="stem_thickness"
                                                    type="number"
                                                    name="stem_thickness"
                                                    value={editingMeasurement.stem_thickness || ''}
                                                    onChange={handleInputChange}
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <Label htmlFor="canopy_width">Canopy Width (cm)</Label>
                                                <Input
                                                    id="canopy_width"
                                                    type="number"
                                                    name="canopy_width"
                                                    value={editingMeasurement.canopy_width || ''}
                                                    onChange={handleInputChange}
                                                />
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="space-y-2">
                                                <Label htmlFor="leaf_color">Leaf Color (1-5)</Label>
                                                <Input
                                                    id="leaf_color"
                                                    type="number"
                                                    name="leaf_color"
                                                    min="1"
                                                    max="5"
                                                    value={editingMeasurement.leaf_color || ''}
                                                    onChange={handleInputChange}
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <Label htmlFor="leaf_firmness">Leaf Firmness (1-5)</Label>
                                                <Input
                                                    id="leaf_firmness"
                                                    type="number"
                                                    name="leaf_firmness"
                                                    min="1"
                                                    max="5"
                                                    value={editingMeasurement.leaf_firmness || ''}
                                                    onChange={handleInputChange}
                                                />
                                            </div>
                                        </div>

                                        <div className="space-y-2">
                                            <Label htmlFor="notes">Notes</Label>
                                            <Input
                                                id="notes"
                                                name="notes"
                                                value={editingMeasurement.notes || ''}
                                                onChange={handleInputChange}
                                            />
                                        </div>

                                        <div className="flex space-x-4">
                                            <div className="flex items-center space-x-2">
                                                <Checkbox
                                                    id="fertilized"
                                                    name="fertilized"
                                                    checked={editingMeasurement.fertilized || false}
                                                    onCheckedChange={handleCheckboxChange('fertilized')}
                                                />
                                                <Label htmlFor="fertilized">Fertilized</Label>
                                            </div>
                                            <div className="flex items-center space-x-2">
                                                <Checkbox
                                                    id="pruned"
                                                    name="pruned"
                                                    checked={editingMeasurement.pruned || false}
                                                    onCheckedChange={handleCheckboxChange('pruned')}
                                                />
                                                <Label htmlFor="pruned">Pruned</Label>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex justify-end space-x-2">
                                        <Button
                                            type="button"
                                            variant="outline"
                                            onClick={() => setEditingMeasurement(null)}
                                        >
                                            Cancel
                                        </Button>
                                        <Button type="submit" disabled={loading}>
                                            {loading ? 'Saving...' : 'Save Changes'}
                                        </Button>
                                    </div>
                                </form>
                            </DialogContent>
                        </Dialog>
                    )}

                    {/* Delete Confirmation Dialog */}
                    <AlertDialog open={!!deletingMeasurement} onOpenChange={() => setDeletingMeasurement(null)}>
                        <AlertDialogContent>
                            <AlertDialogHeader>
                                <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                                <AlertDialogDescription>
                                    This will permanently delete this measurement. This action cannot be undone.
                                </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction
                                    onClick={() => deletingMeasurement && handleDelete(deletingMeasurement)}
                                    className="bg-red-600 hover:bg-red-700 text-white"
                                >
                                    Delete
                                </AlertDialogAction>
                            </AlertDialogFooter>
                        </AlertDialogContent>
                    </AlertDialog>

                    {/* Photo Preview Dialog */}
                    <Dialog open={!!selectedPhoto} onOpenChange={() => setSelectedPhoto(null)}>
                        <DialogContent className="max-w-3xl">
                            <DialogHeader>
                                <DialogTitle>Photo Preview</DialogTitle>
                            </DialogHeader>
                            {selectedPhoto && (
                                <div className="relative">
                                    <Image
                                        src={getPhotoUrl(selectedPhoto.id)}
                                        alt={`Plant photo from ${new Date(selectedPhoto.timestamp).toLocaleDateString()}`}
                                        width={800}
                                        height={600}
                                        className="rounded-lg object-contain"
                                    />
                                    <button
                                        onClick={() => handleDeletePhoto(selectedPhoto.id)}
                                        className="absolute top-2 right-2 bg-red-600 text-white px-3 py-1 rounded-md hover:bg-red-700"
                                    >
                                        Delete
                                    </button>
                                </div>
                            )}
                        </DialogContent>
                    </Dialog>
                </div>
            </DialogContent>
        </Dialog>
    );
};

export default PlantProfile; 