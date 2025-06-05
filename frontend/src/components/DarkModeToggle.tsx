import React, { useState } from 'react';
import Logo from './Logo';

const DarkModeToggle: React.FC = () => {
  const [isDarkMode, setIsDarkMode] = useState(false);

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
    // In a real app, you would apply dark mode to the entire site here
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-lg font-semibold mb-4">Logo Preview</h2>
      
      <div className="flex flex-col space-y-6">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Light Mode:</span>
          <div className="p-4 bg-white border rounded">
            <Logo inverted={true} />
          </div>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Dark Mode:</span>
          <div className="p-4 bg-gray-800 border border-gray-700 rounded">
            <Logo inverted={false} />
          </div>
        </div>
        
        <div className="flex items-center justify-between pt-4 border-t">
          <span className="text-sm font-medium text-gray-700">Toggle Dark Mode:</span>
          <button 
            onClick={toggleDarkMode}
            className={`relative inline-flex h-6 w-11 items-center rounded-full ${isDarkMode ? 'bg-blue-600' : 'bg-gray-200'}`}
          >
            <span className="sr-only">Toggle dark mode</span>
            <span 
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${isDarkMode ? 'translate-x-6' : 'translate-x-1'}`} 
            />
          </button>
        </div>
      </div>
      
      <div className={`mt-6 p-4 rounded ${isDarkMode ? 'bg-gray-800 text-white' : 'bg-white text-gray-800 border'}`}>
        <div className="flex items-center justify-center">
          <Logo inverted={!isDarkMode} />
        </div>
        <p className={`mt-4 text-sm text-center ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
          This shows how the logo adapts to dark/light modes
        </p>
      </div>
    </div>
  );
};

export default DarkModeToggle; 