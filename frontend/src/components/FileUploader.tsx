import React, { useRef } from 'react';

interface FileUploaderProps {
  file: File | null;
  setFile: (file: File | null) => void;
}

const FileUploader: React.FC<FileUploaderProps> = ({ file, setFile }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const triggerFileInput = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  return (
    <div>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Upload Your Audio</h3>
      
      <div 
        onClick={triggerFileInput}
        className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-primary transition-colors"
      >
        <input 
          ref={fileInputRef}
          type="file" 
          accept="audio/*" 
          onChange={handleFileChange} 
          className="hidden"
        />
        
        {file ? (
          <div className="space-y-2">
            <div className="w-12 h-12 bg-blue-100 text-primary rounded-full flex items-center justify-center mx-auto">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
              </svg>
            </div>
            <p className="text-sm font-medium text-gray-900">{file.name}</p>
            <p className="text-xs text-gray-500">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
            <button 
              onClick={(e) => { e.stopPropagation(); setFile(null); }}
              className="text-xs text-red-600 hover:text-red-800"
            >
              Remove
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <p className="text-sm font-medium text-gray-700">Drag and drop your audio file here</p>
            <p className="text-xs text-gray-500">Or click to browse</p>
            <p className="text-xs text-gray-400">Supports MP3, WAV, M4A, etc.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileUploader; 