'use client';

interface TimeRangeSelectorProps {
  selectedDays: number;
  onSelectDays: (days: number) => void;
}

export default function TimeRangeSelector({ selectedDays, onSelectDays }: TimeRangeSelectorProps) {
  const timeRanges = [
    { label: '1 Day', value: 1 },
    { label: '7 Days', value: 7 },
    { label: '30 Days', value: 30 }
  ];
  
  return (
    <div className="bg-white rounded-lg shadow-md p-4 mb-6">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">Time Range:</span>
        <div className="flex space-x-2">
          {timeRanges.map((range) => (
            <button
              key={range.value}
              onClick={() => onSelectDays(range.value)}
              className={`px-3 py-1 text-sm rounded-md transition-colors
                ${selectedDays === range.value
                  ? 'bg-primary-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
            >
              {range.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
} 