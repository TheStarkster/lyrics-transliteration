import React, { useState } from 'react';
import type { TranscriptSegment } from './types';
import { TabView } from './types';
import { formatTime } from './utils';

interface ResultsSectionProps {
  transcript: string;
  transliteration: string;
  segments: TranscriptSegment[];
  activeTab: TabView;
  handleTabChange: (tab: TabView) => void;
  language: string;
  downloadSRT: () => void;
  handleRemoveSegment: (segmentId: number) => void;
  handleUpdateSegment: (segmentId: number, field: 'text' | 'transliteration', value: string) => void;
}

const ResultsSection: React.FC<ResultsSectionProps> = ({
  transcript,
  transliteration,
  segments,
  activeTab,
  handleTabChange,
  language,
  downloadSRT,
  handleRemoveSegment,
  handleUpdateSegment
}) => {
  const [editingSegmentId, setEditingSegmentId] = useState<number | null>(null);
  const [editValue, setEditValue] = useState<string>('');

  if (!transcript && !transliteration) return null;
  
  const startEditing = (segment: TranscriptSegment) => {
    setEditingSegmentId(segment.id);
    setEditValue(activeTab === TabView.ORIGINAL ? segment.text : segment.transliteration || '');
  };

  const saveEdit = (segmentId: number) => {
    handleUpdateSegment(
      segmentId, 
      activeTab === TabView.ORIGINAL ? 'text' : 'transliteration', 
      editValue
    );
    setEditingSegmentId(null);
  };

  const cancelEdit = () => {
    setEditingSegmentId(null);
  };
  
  return (
    <section className="bg-white rounded-xl shadow-md p-6">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Extraction Results</h3>
        
        {segments.length > 0 && (
          <button
            onClick={downloadSRT}
            className="flex items-center gap-1 py-1.5 px-3 bg-green-100 hover:bg-green-200 text-green-800 rounded-full text-sm font-medium transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Download SRT
          </button>
        )}
      </div>
      
      <div className="border-b border-gray-200 mb-6">
        <div className="flex">
          <button
            onClick={() => handleTabChange(TabView.ORIGINAL)}
            className={`px-4 py-2 text-sm font-medium ${
              activeTab === TabView.ORIGINAL
                ? 'border-b-2 border-primary text-primary' 
                : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            {language} (Original)
          </button>
          <button
            onClick={() => handleTabChange(TabView.TRANSLITERATION)}
            className={`px-4 py-2 text-sm font-medium ${
              activeTab === TabView.TRANSLITERATION
                ? 'border-b-2 border-primary text-primary' 
                : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            English Transliteration
          </button>
        </div>
      </div>
      
      <div className="bg-gray-50 rounded-lg p-4">
        {activeTab === TabView.ORIGINAL && segments.length > 0 ? (
          <div className="space-y-2">
            {segments.map((segment, index) => (
              <div key={index} className="flex items-start group text-sm bg-white p-2 rounded-md border border-transparent hover:border-gray-200">
                <span className="text-gray-500 w-16 flex-shrink-0 mt-1">[{formatTime(segment.start)}]</span>
                
                {editingSegmentId === segment.id ? (
                  <div className="flex-grow flex flex-col">
                    <textarea 
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      className="w-full p-1 border border-gray-300 rounded text-sm"
                      rows={3}
                    />
                    <div className="flex gap-2 mt-1 justify-end">
                      <button 
                        onClick={() => saveEdit(segment.id)}
                        className="px-2 py-1 bg-blue-100 text-blue-700 rounded-md text-xs hover:bg-blue-200"
                      >
                        Save
                      </button>
                      <button 
                        onClick={cancelEdit}
                        className="px-2 py-1 bg-gray-100 text-gray-700 rounded-md text-xs hover:bg-gray-200"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <span className="text-gray-900 flex-grow">{segment.text}</span>
                    <div className="hidden group-hover:flex gap-1">
                      <button 
                        onClick={() => startEditing(segment)}
                        className="p-1 text-blue-600 hover:bg-blue-50 rounded"
                        title="Edit segment"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                      <button 
                        onClick={() => handleRemoveSegment(segment.id)}
                        className="p-1 text-red-600 hover:bg-red-50 rounded"
                        title="Remove segment"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        ) : activeTab === TabView.ORIGINAL ? (
          <pre className="whitespace-pre-wrap text-sm text-gray-700">{transcript}</pre>
        ) : null}
        
        {activeTab === TabView.TRANSLITERATION && segments.length > 0 ? (
          <div className="space-y-2">
            {segments.map((segment, index) => (
              <div key={index} className="flex items-start group text-sm bg-white p-2 rounded-md border border-transparent hover:border-gray-200">
                <span className="text-gray-500 w-16 flex-shrink-0 mt-1">[{formatTime(segment.start)}]</span>
                
                {editingSegmentId === segment.id ? (
                  <div className="flex-grow flex flex-col">
                    <textarea 
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      className="w-full p-1 border border-gray-300 rounded text-sm"
                      rows={3}
                    />
                    <div className="flex gap-2 mt-1 justify-end">
                      <button 
                        onClick={() => saveEdit(segment.id)}
                        className="px-2 py-1 bg-blue-100 text-blue-700 rounded-md text-xs hover:bg-blue-200"
                      >
                        Save
                      </button>
                      <button 
                        onClick={cancelEdit}
                        className="px-2 py-1 bg-gray-100 text-gray-700 rounded-md text-xs hover:bg-gray-200"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <span className="text-gray-900 flex-grow">{segment.transliteration}</span>
                    <div className="hidden group-hover:flex gap-1">
                      <button 
                        onClick={() => startEditing(segment)}
                        className="p-1 text-blue-600 hover:bg-blue-50 rounded"
                        title="Edit segment"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                      <button 
                        onClick={() => handleRemoveSegment(segment.id)}
                        className="p-1 text-red-600 hover:bg-red-50 rounded"
                        title="Remove segment"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        ) : activeTab === TabView.TRANSLITERATION ? (
          <pre className="whitespace-pre-wrap text-sm text-gray-700">{transliteration}</pre>
        ) : null}
      </div>
    </section>
  );
};

export default ResultsSection; 