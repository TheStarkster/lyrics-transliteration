import React from 'react';

interface LogoProps {
  inverted?: boolean;
}

const Logo: React.FC<LogoProps> = () => {
  return (
    <div className="flex items-center">
      <img 
        src="/logo.jpeg" 
        alt="DestinPQ" 
        className="h-12 w-12 filter invert" 
        style={{ filter: 'invert(100%)' }}
      />
    </div>
  );
};

export default Logo; 