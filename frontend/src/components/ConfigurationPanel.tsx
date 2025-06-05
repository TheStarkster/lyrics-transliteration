import React from 'react';

interface ConfigurationPanelProps {
  language: string;
  handleLanguageChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  handleUpload: () => void;
  file: File | null;
  loading: boolean;
  wsConnected: boolean;
  clientId: string;
}

const ConfigurationPanel: React.FC<ConfigurationPanelProps> = ({
  language,
  handleLanguageChange,
  handleUpload,
  file,
  loading,
  wsConnected,
  clientId
}) => {
  return (
    <div>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Configuration</h3>
      
      <div className="space-y-4">
        <div>
          <label htmlFor="language-select" className="block text-sm font-medium text-gray-700 mb-1">
            Language
          </label>
          <select 
            id="language-select" 
            value={language} 
            onChange={handleLanguageChange}
            className="w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
          >
            <option value="Telugu">Telugu</option>
            <option value="Hindi">Hindi</option>
          </select>
          <p className="mt-1 text-xs text-gray-500">Select the language of your audio file</p>
        </div>
        
        <button 
          onClick={handleUpload} 
          disabled={!file || loading || !wsConnected || !clientId}
          className={`w-full py-2 px-4 rounded-md text-white font-medium ${!file || loading || !wsConnected || !clientId 
            ? 'bg-gray-400 cursor-not-allowed' 
            : 'bg-primary hover:bg-primary/90'} transition-colors shadow-sm flex items-center justify-center`}
        >
          {loading && (
            <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          )}
          {!wsConnected ? 'Connecting to server...' : loading ? 'Processing...' : 'Extract Lyrics'}
        </button>
      </div>
    </div>
  );
};

export default ConfigurationPanel; 