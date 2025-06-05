import React from 'react';

interface ProgressSectionProps {
  progress: string[];
  loading: boolean;
}

const ProgressSection: React.FC<ProgressSectionProps> = ({ progress, loading }) => {
  if (progress.length === 0) return null;
  
  return (
    <section className="bg-white rounded-xl shadow-md p-6 mb-8">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Processing Status</h3>
        {loading && (
          <div className="flex items-center">
            <div className="animate-pulse bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-xs font-medium">
              Processing
            </div>
          </div>
        )}
      </div>
      
      <div className="space-y-2 max-h-48 overflow-y-auto">
        {progress.map((msg, index) => (
          <div 
            key={index} 
            className={`py-2 px-3 rounded-lg text-sm ${
              msg.includes('Error') 
                ? 'bg-red-50 text-red-700' 
                : msg.includes('complete') 
                  ? 'bg-green-50 text-green-700'
                  : 'bg-gray-50 text-gray-700'
            }`}
          >
            {msg}
          </div>
        ))}
      </div>
    </section>
  );
};

export default ProgressSection; 