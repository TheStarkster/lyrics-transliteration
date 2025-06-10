import React from 'react';
import { TabView } from './types';
import type { TranscriptSegment } from './types';
// import { formatTime } from './utils';
import SegmentEditor from './SegmentEditor';

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
  openComparisonModal: () => void;
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
  handleUpdateSegment,
  openComparisonModal,
}) => {
  // const [editingSegmentId, setEditingSegmentId] = useState<number | null>(null);
  // const [editValue, setEditValue] = useState<string>('');

  if (!transcript && !transliteration) return null;
  
  // const startEditing = (segment: TranscriptSegment) => {
  //   setEditingSegmentId(segment.id);
  //   setEditValue(activeTab === TabView.ORIGINAL ? segment.text : segment.transliteration || '');
  // };

  // const saveEdit = (segmentId: number) => {
  //   handleUpdateSegment(
  //     segmentId, 
  //     activeTab === TabView.ORIGINAL ? 'text' : 'transliteration', 
  //     editValue
  //   );
  //   setEditingSegmentId(null);
  // };

  // const cancelEdit = () => {
  //   setEditingSegmentId(null);
  // };
  
  return (
    <div className="mt-8 bg-white shadow overflow-hidden rounded-lg">
      <div className="px-4 py-5 sm:px-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900">Results</h3>
        <p className="mt-1 max-w-2xl text-sm text-gray-500">
          View and edit the transcription results below.
        </p>
      </div>
      
      <div className="border-t border-gray-200">
        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <div className="sm:flex sm:items-center">
              <div className="border border-gray-300 rounded-md inline-flex">
                <button
                  type="button"
                  className={`px-4 py-2 text-sm font-medium rounded-l-md ${
                    activeTab === TabView.ORIGINAL
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-700 hover:bg-gray-50'
                  }`}
                  onClick={() => handleTabChange(TabView.ORIGINAL)}
                >
                  Original
                </button>
                <button
                  type="button"
                  className={`px-4 py-2 text-sm font-medium rounded-r-md ${
                    activeTab === TabView.TRANSLITERATION
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-700 hover:bg-gray-50'
                  }`}
                  onClick={() => handleTabChange(TabView.TRANSLITERATION)}
                  disabled={!transliteration}
                >
                  Transliteration
                </button>
              </div>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={openComparisonModal}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                Compare with Reference
              </button>
              <button
                onClick={downloadSRT}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download SRT
              </button>
            </div>
          </div>
        </div>
        
        <div className="p-4">
          {activeTab === TabView.ORIGINAL ? (
            <div>
              <h4 className="text-md font-medium text-gray-900 mb-2">
                Original Text ({language})
              </h4>
              <p className="whitespace-pre-wrap text-gray-800">{transcript}</p>
            </div>
          ) : (
            <div>
              <h4 className="text-md font-medium text-gray-900 mb-2">
                Transliteration
              </h4>
              <p className="whitespace-pre-wrap text-gray-800">
                {transliteration || 'No transliteration available'}
              </p>
            </div>
          )}
        </div>
        
        <div className="border-t border-gray-200 p-4">
          <h4 className="text-md font-medium text-gray-900 mb-4">
            Segments
          </h4>
          <div className="space-y-4">
            {segments.map((segment) => (
              <SegmentEditor
                key={segment.id}
                segment={segment}
                activeTab={activeTab}
                onRemove={() => handleRemoveSegment(segment.id)}
                onUpdate={(field, value) => handleUpdateSegment(segment.id, field, value)}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResultsSection; 