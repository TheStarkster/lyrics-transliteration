import React from 'react';

const HeroSection: React.FC = () => {
  return (
    <section className="text-center mb-12 pt-6">
      <h2 className="text-4xl font-extrabold text-gray-900 mb-2">Professional Lyrics Transliteration</h2>
      <p className="text-md text-gray-600 max-w-2xl mx-auto mb-6">
        AI-powered technology that transcribes and transliterates song lyrics into English with precise timestamps.
      </p>
      <div className="flex flex-wrap justify-center gap-4 text-sm text-gray-600">
        <div className="flex items-center">
          <svg className="h-5 w-5 text-blue-500 mr-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <span>Multiple language support</span>
        </div>
        <div className="flex items-center">
          <svg className="h-5 w-5 text-blue-500 mr-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <span>Export as SRT for video subtitles</span>
        </div>
        <div className="flex items-center">
          <svg className="h-5 w-5 text-blue-500 mr-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <span>Edit and customize results</span>
        </div>
      </div>
    </section>
  );
};

export default HeroSection; 