import React, { useState } from 'react';
import { TabView } from './types';
import type { TranscriptSegment } from './types';
import { formatSRTTime } from './utils';

interface SegmentEditorProps {
  segment: TranscriptSegment;
  activeTab: TabView;
  onRemove: () => void;
  onUpdate: (field: 'text' | 'transliteration', value: string) => void;
}

const SegmentEditor: React.FC<SegmentEditorProps> = ({
  segment,
  activeTab,
  onRemove,
  onUpdate,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState('');

  const fieldToEdit = activeTab === TabView.ORIGINAL ? 'text' : 'transliteration';
  const textValue = activeTab === TabView.ORIGINAL ? segment.text : (segment.transliteration || '');

  const startEditing = () => {
    setEditValue(textValue);
    setIsEditing(true);
  };

  const saveEdit = () => {
    onUpdate(fieldToEdit, editValue);
    setIsEditing(false);
  };

  const cancelEdit = () => {
    setIsEditing(false);
  };

  return (
    <div className="flex flex-col border border-gray-200 rounded-md overflow-hidden">
      <div className="bg-gray-50 px-4 py-2 text-sm text-gray-500 flex items-center justify-between">
        <div>
          <span className="font-medium">{formatSRTTime(segment.start)}</span>
          <span className="mx-2">→</span>
          <span className="font-medium">{formatSRTTime(segment.end)}</span>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={startEditing}
            className="text-blue-600 hover:text-blue-800"
            title="Edit segment"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
          </button>
          <button
            onClick={onRemove}
            className="text-red-600 hover:text-red-800"
            title="Remove segment"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
      <div className="p-4">
        {isEditing ? (
          <div className="space-y-2">
            <textarea
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
              rows={3}
            />
            <div className="flex justify-end space-x-2">
              <button
                onClick={cancelEdit}
                className="px-3 py-1 text-sm text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
              >
                Cancel
              </button>
              <button
                onClick={saveEdit}
                className="px-3 py-1 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-md"
              >
                Save
              </button>
            </div>
          </div>
        ) : (
          <p className="text-gray-800 whitespace-pre-wrap">
            {textValue}
          </p>
        )}
      </div>
    </div>
  );
};

export default SegmentEditor; 