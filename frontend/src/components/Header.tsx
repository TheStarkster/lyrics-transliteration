import React from 'react';
import { Link } from 'react-router-dom';
import Logo from './Logo';

interface HeaderProps {
  wsConnected: boolean;
}

const Header: React.FC<HeaderProps> = ({ wsConnected }) => {
  return (
    <header className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
        <div className="flex items-center">
          <Link to="/" className="flex items-center">
            <Logo inverted={true} />
          </Link>
          <div className="ml-6 pl-6 border-l border-gray-200">
            <h2 className="text-lg font-semibold text-primary">Lyrics Transliteration</h2>
            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full uppercase font-medium">Beta</span>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <a href="https://www.destinpq.com/" className="text-sm text-gray-600 hover:text-gray-900">Main Site</a>
          <div className="flex items-center space-x-1">
            <span className={`h-2 w-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`}></span>
            <span className="text-sm text-gray-500">{wsConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header; 