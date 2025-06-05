import React from 'react';
import FileUploader from './FileUploader';
import ConfigurationPanel from './ConfigurationPanel';

interface UploadSectionProps {
  file: File | null;
  setFile: (file: File | null) => void;
  language: string;
  handleLanguageChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  handleUpload: () => void;
  loading: boolean;
  wsConnected: boolean;
  clientId: string;
}

const UploadSection: React.FC<UploadSectionProps> = ({
  file,
  setFile,
  language,
  handleLanguageChange,
  handleUpload,
  loading,
  wsConnected,
  clientId
}) => {
  return (
    <section className="bg-white rounded-xl shadow-md p-6 mb-8">
      <div className="grid md:grid-cols-2 gap-8">
        <FileUploader file={file} setFile={setFile} />
        
        <ConfigurationPanel 
          language={language}
          handleLanguageChange={handleLanguageChange}
          handleUpload={handleUpload}
          file={file}
          loading={loading}
          wsConnected={wsConnected}
          clientId={clientId}
        />
      </div>
    </section>
  );
};

export default UploadSection; 