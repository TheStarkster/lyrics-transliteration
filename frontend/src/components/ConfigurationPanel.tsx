import React, { useState } from 'react';
import { FiInfo } from 'react-icons/fi';

interface ConfigurationPanelProps {
  language: string;
  handleLanguageChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  handleUpload: () => void;
  file: File | null;
  loading: boolean;
  wsConnected: boolean;
  clientId: string;
  model: string;
  handleModelChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  beamSize: number;
  handleBeamSizeChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

const ConfigurationPanel: React.FC<ConfigurationPanelProps> = ({
  language,
  handleLanguageChange,
  handleUpload,
  file,
  loading,
  wsConnected,
  clientId,
  model,
  handleModelChange,
  beamSize,
  handleBeamSizeChange
}) => {
  const [showModelTooltip, setShowModelTooltip] = useState(false);
  const [showBeamTooltip, setShowBeamTooltip] = useState(false);

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
            <option value="te">Telugu</option>
            <option value="hi">Hindi</option>
          </select>
          <p className="mt-1 text-xs text-gray-500">Select the language of your audio file</p>
        </div>
        
        <div>
          <div className="flex items-center">
            <label htmlFor="model-select" className="block text-sm font-medium text-gray-700 mb-1">
              Whisper Model
            </label>
            <button 
              className="ml-1 text-gray-500 hover:text-gray-700"
              onMouseEnter={() => setShowModelTooltip(true)}
              onMouseLeave={() => setShowModelTooltip(false)}
            >
              <FiInfo size={16} />
            </button>
            {showModelTooltip && (
              <div className="absolute mt-1 z-10 p-2 text-xs bg-gray-800 text-white rounded shadow-lg max-w-xs">
                Select the Whisper model size. Larger models are more accurate but may be slower. Large-v3 is the most accurate.
              </div>
            )}
          </div>
          <select 
            id="model-select" 
            value={model} 
            onChange={handleModelChange}
            className="w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
          >
            <option value="large-v3">large-v3 (best quality)</option>
            <option value="large">large</option>
            <option value="medium">medium</option>
            <option value="small">small</option>
            <option value="base">base (fastest)</option>
          </select>
          <p className="mt-1 text-xs text-gray-500">Select the model size for transcription</p>
        </div>
        
        <div>
          <div className="flex items-center">
            <label htmlFor="beam-size" className="block text-sm font-medium text-gray-700 mb-1">
              Beam Size: {beamSize}
            </label>
            <button 
              className="ml-1 text-gray-500 hover:text-gray-700"
              onMouseEnter={() => setShowBeamTooltip(true)}
              onMouseLeave={() => setShowBeamTooltip(false)}
            >
              <FiInfo size={16} />
            </button>
            {showBeamTooltip && (
              <div className="absolute mt-1 z-10 p-2 text-xs bg-gray-800 text-white rounded shadow-lg max-w-xs">
                Beam size controls how many alternatives the model considers. Higher values provide better accuracy but slower processing.
              </div>
            )}
          </div>
          <input
            type="range"
            id="beam-size"
            min="1"
            max="20"
            value={beamSize}
            onChange={handleBeamSizeChange}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>1 (Fastest)</span>
            <span>20 (Most Accurate)</span>
          </div>
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