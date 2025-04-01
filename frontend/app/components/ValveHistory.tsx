'use client';

import { format } from 'date-fns';
import { ValveAction } from '../services/api';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface ValveHistoryProps {
  valveHistory: ValveAction[];
  isLoading: boolean;
  pagination: {
    total: number;
    page: number;
    limit: number;
    pages: number;
  };
  onPageChange: (page: number) => void;
}

export default function ValveHistory({ 
  valveHistory = [], 
  isLoading, 
  pagination = { total: 0, page: 1, limit: 5, pages: 1 }, 
  onPageChange 
}: ValveHistoryProps) {
  // Calculate pagination values with safe defaults
  const { 
    total: totalItems = 0, 
    page: currentPage = 1, 
    limit = 5,
    pages: totalPages = 1 
  } = pagination || {};
  
  const startIndex = Math.max(0, (currentPage - 1) * limit);
  const endIndex = Math.min(startIndex + limit, totalItems);
  
  // Handle pagination
  const goToNextPage = () => {
    if (currentPage < totalPages) {
      onPageChange(currentPage + 1);
    }
  };
  
  const goToPreviousPage = () => {
    if (currentPage > 1) {
      onPageChange(currentPage - 1);
    }
  };
  
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4">Valve Activity History</h2>
      
      {isLoading ? (
        <div className="flex justify-center items-center h-64">
          <div className="loading-spinner"></div>
        </div>
      ) : (!valveHistory || valveHistory.length === 0) ? (
        <div className="flex justify-center items-center h-64 text-gray-500">
          No valve activity recorded
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Time
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {valveHistory.map((action) => (
                  <tr key={action.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {format(new Date(action.timestamp), 'MMM dd, yyyy HH:mm:ss')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                        ${action.state === 1 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'}`}>
                        {action.state === 1 ? 'Turned ON' : 'Turned OFF'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {/* Pagination controls */}
          <div className="flex items-center justify-between mt-4 text-sm">
            <div>
              {totalItems > 0 && `Showing ${startIndex + 1}-${endIndex} of ${totalItems} entries`}
            </div>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={goToPreviousPage} 
                disabled={currentPage <= 1}
              >
                <ChevronLeft className="h-4 w-4 mr-1" />
                Previous
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={goToNextPage} 
                disabled={currentPage >= totalPages}
              >
                Next
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
} 