import React, { useState, useEffect } from 'react';
import { addMeasurement, getMeasurements, PlantMeasurement } from '../services/measurements';
import { Line } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
} from 'chart.js';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

interface Props {
    deviceId: string;
}

const PlantMeasurements: React.FC<Props> = ({ deviceId }) => {
    const [measurements, setMeasurements] = useState<PlantMeasurement[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [formData, setFormData] = useState<PlantMeasurement>({
        device_id: deviceId,
        height: undefined,
        leaf_count: undefined,
        stem_thickness: undefined,
        canopy_width: undefined,
        leaf_color: undefined,
        leaf_firmness: undefined,
        health_score: undefined,
        notes: '',
        fertilized: false,
        pruned: false,
        ph_reading: undefined,
    });

    useEffect(() => {
        fetchMeasurements();
    }, [deviceId]);

    const fetchMeasurements = async () => {
        try {
            setLoading(true);
            const data = await getMeasurements(deviceId);
            setMeasurements(data);
            setError(null);
        } catch (err) {
            setError('Failed to fetch measurements');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            setLoading(true);
            await addMeasurement(formData);
            await fetchMeasurements();
            // Reset form
            setFormData({
                device_id: deviceId,
                height: undefined,
                leaf_count: undefined,
                stem_thickness: undefined,
                canopy_width: undefined,
                leaf_color: undefined,
                leaf_firmness: undefined,
                health_score: undefined,
                notes: '',
                fertilized: false,
                pruned: false,
                ph_reading: undefined,
            });
            setError(null);
        } catch (err) {
            setError('Failed to add measurement');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        const { name, value, type } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' 
                ? (e.target as HTMLInputElement).checked 
                : type === 'number' 
                    ? parseFloat(value) || undefined
                    : value
        }));
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
        <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-xl font-semibold mb-4">Add Plant Measurement</h2>
                {error && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                        {error}
                    </div>
                )}
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700">
                                Height (cm)
                                <input
                                    type="number"
                                    name="height"
                                    value={formData.height || ''}
                                    onChange={handleInputChange}
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                    step="0.1"
                                />
                            </label>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">
                                Leaf Count
                                <input
                                    type="number"
                                    name="leaf_count"
                                    value={formData.leaf_count || ''}
                                    onChange={handleInputChange}
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                />
                            </label>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">
                                Stem Thickness (mm)
                                <input
                                    type="number"
                                    name="stem_thickness"
                                    value={formData.stem_thickness || ''}
                                    onChange={handleInputChange}
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                    step="0.1"
                                />
                            </label>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">
                                Canopy Width (cm)
                                <input
                                    type="number"
                                    name="canopy_width"
                                    value={formData.canopy_width || ''}
                                    onChange={handleInputChange}
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                    step="0.1"
                                />
                            </label>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">
                                Leaf Color (1-5)
                                <select
                                    name="leaf_color"
                                    value={formData.leaf_color || ''}
                                    onChange={handleInputChange}
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                >
                                    <option value="">Select...</option>
                                    <option value="1">1 - Very Yellow</option>
                                    <option value="2">2 - Pale Green</option>
                                    <option value="3">3 - Normal Green</option>
                                    <option value="4">4 - Deep Green</option>
                                    <option value="5">5 - Very Deep Green</option>
                                </select>
                            </label>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">
                                Leaf Firmness (1-5)
                                <select
                                    name="leaf_firmness"
                                    value={formData.leaf_firmness || ''}
                                    onChange={handleInputChange}
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                >
                                    <option value="">Select...</option>
                                    <option value="1">1 - Very Wilted</option>
                                    <option value="2">2 - Slightly Wilted</option>
                                    <option value="3">3 - Normal</option>
                                    <option value="4">4 - Firm</option>
                                    <option value="5">5 - Very Firm</option>
                                </select>
                            </label>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">
                                Health Score (1-10)
                                <input
                                    type="number"
                                    name="health_score"
                                    value={formData.health_score || ''}
                                    onChange={handleInputChange}
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                    min="1"
                                    max="10"
                                />
                            </label>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">
                                pH Reading
                                <input
                                    type="number"
                                    name="ph_reading"
                                    value={formData.ph_reading || ''}
                                    onChange={handleInputChange}
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                    step="0.1"
                                    min="0"
                                    max="14"
                                />
                            </label>
                        </div>
                    </div>
                    
                    <div className="flex space-x-4">
                        <label className="flex items-center">
                            <input
                                type="checkbox"
                                name="fertilized"
                                checked={formData.fertilized}
                                onChange={handleInputChange}
                                className="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            />
                            <span className="ml-2">Fertilized</span>
                        </label>
                        <label className="flex items-center">
                            <input
                                type="checkbox"
                                name="pruned"
                                checked={formData.pruned}
                                onChange={handleInputChange}
                                className="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            />
                            <span className="ml-2">Pruned</span>
                        </label>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700">
                            Notes
                            <textarea
                                name="notes"
                                value={formData.notes}
                                onChange={handleInputChange}
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                rows={3}
                            />
                        </label>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50"
                    >
                        {loading ? 'Saving...' : 'Save Measurement'}
                    </button>
                </form>
            </div>

            {measurements.length > 0 && (
                <div className="bg-white p-6 rounded-lg shadow">
                    <h2 className="text-xl font-semibold mb-4">Growth History</h2>
                    <div className="h-96">
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
            )}

            {measurements.length > 0 && (
                <div className="bg-white p-6 rounded-lg shadow overflow-x-auto">
                    <h2 className="text-xl font-semibold mb-4">Measurement History</h2>
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Height</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Leaf Count</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Health Score</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Notes</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {measurements.map((measurement, index) => (
                                <tr key={index}>
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
                                    <td className="px-6 py-4 text-sm text-gray-500">
                                        {measurement.notes || '-'}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

export default PlantMeasurements; 