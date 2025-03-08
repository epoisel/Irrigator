'use client';

import { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import { format } from 'date-fns';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions
} from 'chart.js';
import { MoistureData } from '../services/api';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface MoistureChartProps {
  moistureData: MoistureData[];
  isLoading: boolean;
}

export default function MoistureChart({ moistureData, isLoading }: MoistureChartProps) {
  const [chartData, setChartData] = useState<any>({
    labels: [],
    datasets: []
  });
  
  useEffect(() => {
    if (moistureData && moistureData.length > 0) {
      // Format data for chart
      const labels = moistureData.map(item => 
        format(new Date(item.timestamp), 'MMM dd, HH:mm')
      );
      
      const moistureValues = moistureData.map(item => item.moisture);
      
      setChartData({
        labels,
        datasets: [
          {
            label: 'Moisture Level (%)',
            data: moistureValues,
            borderColor: 'rgb(34, 197, 94)',
            backgroundColor: 'rgba(34, 197, 94, 0.5)',
            tension: 0.3,
            pointRadius: 2,
            pointHoverRadius: 5
          }
        ]
      });
    }
  }, [moistureData]);
  
  const chartOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Moisture Level Trend',
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            return `Moisture: ${context.parsed.y.toFixed(1)}%`;
          }
        }
      }
    },
    scales: {
      y: {
        min: 0,
        max: 100,
        title: {
          display: true,
          text: 'Moisture (%)'
        }
      },
      x: {
        title: {
          display: true,
          text: 'Time'
        }
      }
    }
  };
  
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4">Moisture Trend</h2>
      
      {isLoading ? (
        <div className="flex justify-center items-center h-64">
          <div className="loading-spinner"></div>
        </div>
      ) : moistureData.length === 0 ? (
        <div className="flex justify-center items-center h-64 text-gray-500">
          No moisture data available
        </div>
      ) : (
        <div className="h-64">
          <Line data={chartData} options={chartOptions} />
        </div>
      )}
    </div>
  );
} 