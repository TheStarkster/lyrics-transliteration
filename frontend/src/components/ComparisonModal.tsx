import React, { useState } from 'react';
import type { WERResponse, WordAlignment } from './types';

const API_SERVER_URL = 'http://162.243.223.158:8000';

interface ComparisonModalProps {
  isOpen: boolean;
  onClose: () => void;
  textToCompare: string;
  textType: 'original' | 'transliteration';
}

// CSS classes for word comparison
const cssStyles = `
.word-comparison .correct { color: green; }
.word-comparison .substitution { color: orange; background-color: rgba(255, 165, 0, 0.1); }
.word-comparison .deletion { color: red; text-decoration: line-through; background-color: rgba(255, 0, 0, 0.1); }
.word-comparison .insertion { color: violet; background-color: rgba(238, 130, 238, 0.1); }
`;

const ComparisonModal: React.FC<ComparisonModalProps> = ({ 
  isOpen, 
  onClose, 
  textToCompare,
  textType
}) => {
  const [referenceText, setReferenceText] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<WERResponse | null>(null);
  const [error, setError] = useState('');

  // Add CSS styles to document head on component mount
  React.useEffect(() => {
    if (isOpen) {
      // Add style tag to head
      const styleTag = document.createElement('style');
      styleTag.id = 'wer-comparison-styles';
      styleTag.innerHTML = cssStyles;
      document.head.appendChild(styleTag);
      
      // Clean up on unmount
      return () => {
        const existingStyle = document.getElementById('wer-comparison-styles');
        if (existingStyle) {
          document.head.removeChild(existingStyle);
        }
      };
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleCompare = async () => {
    if (!referenceText.trim()) {
      setError('Please enter reference text');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`${API_SERVER_URL}/calculate-wer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          reference: referenceText,
          hypothesis: textToCompare,
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        setResults(data);
      } else {
        setError(data.error || 'Failed to calculate WER');
      }
    } catch (err) {
      setError('Network error when calculating WER');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const formatPercentage = (value: number) => {
    return (value * 100).toFixed(2) + '%';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">
            Compare with Reference Text ({textType})
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Paste your reference text here:
          </label>
          <textarea
            value={referenceText}
            onChange={(e) => setReferenceText(e.target.value)}
            className="w-full h-32 p-2 border border-gray-300 rounded-md"
            placeholder="Enter reference text to compare with..."
          />
        </div>

        {error && (
          <div className="mb-4 p-2 bg-red-100 text-red-700 rounded-md">
            {error}
          </div>
        )}

        <div className="mb-4">
          <h3 className="font-medium text-gray-700 mb-2">Text to compare:</h3>
          <div className="p-2 bg-gray-100 rounded-md max-h-32 overflow-y-auto">
            {textToCompare || <em className="text-gray-500">No text available</em>}
          </div>
        </div>

        {results && (
          <>
            <div className="mb-4 p-3 bg-blue-50 rounded-md">
              <h3 className="font-medium text-blue-700 mb-2">Error Metrics:</h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <p className="text-sm text-gray-500">Word Error Rate</p>
                  <p className="text-lg font-bold">{formatPercentage(results.wer)}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-gray-500">Match Error Rate</p>
                  <p className="text-lg font-bold">{formatPercentage(results.mer)}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-gray-500">Word Information Lost</p>
                  <p className="text-lg font-bold">{formatPercentage(results.wil)}</p>
                </div>
              </div>
            </div>
            
            {results.substitutions !== undefined && (
              <div className="mb-4 p-3 bg-gray-50 rounded-md">
                <h3 className="font-medium text-gray-700 mb-2">Error Breakdown:</h3>
                <div className="grid grid-cols-4 gap-4">
                  <div className="text-center">
                    <p className="text-sm text-gray-500">Total Words</p>
                    <p className="text-lg font-bold">{results.total_words}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-500">Substitutions</p>
                    <p className="text-lg font-bold text-amber-500">{results.substitutions}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-500">Deletions</p>
                    <p className="text-lg font-bold text-red-500">{results.deletions}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-500">Insertions</p>
                    <p className="text-lg font-bold text-violet-500">{results.insertions}</p>
                  </div>
                </div>
              </div>
            )}
            
            <div className="mb-4">
              <h3 className="font-medium text-gray-700 mb-2">Color-Coded Comparison:</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-1">Reference:</p>
                  <div 
                    className="p-3 bg-white border border-gray-200 rounded-md overflow-auto word-comparison"
                    dangerouslySetInnerHTML={{ __html: results.reference_html || "" }}
                  />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-1">Hypothesis:</p>
                  <div 
                    className="p-3 bg-white border border-gray-200 rounded-md overflow-auto word-comparison"
                    dangerouslySetInnerHTML={{ __html: results.hypothesis_html || "" }}
                  />
                </div>
              </div>
            </div>
            
            <div className="mb-4">
              <h3 className="font-medium text-gray-700 mb-2">Legend:</h3>
              <div className="flex flex-wrap gap-3">
                <div className="flex items-center">
                  <span className="inline-block w-3 h-3 bg-green-500 rounded-full mr-1"></span>
                  <span className="text-sm">Correct</span>
                </div>
                <div className="flex items-center">
                  <span className="inline-block w-3 h-3 bg-amber-500 rounded-full mr-1"></span>
                  <span className="text-sm">Substitution</span>
                </div>
                <div className="flex items-center">
                  <span className="inline-block w-3 h-3 bg-red-500 rounded-full mr-1"></span>
                  <span className="text-sm">Deletion</span>
                </div>
                <div className="flex items-center">
                  <span className="inline-block w-3 h-3 bg-violet-500 rounded-full mr-1"></span>
                  <span className="text-sm">Insertion</span>
                </div>
              </div>
            </div>
          </>
        )}

        <div className="flex justify-end">
          <button
            onClick={onClose}
            className="mr-2 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Close
          </button>
          <button
            onClick={handleCompare}
            disabled={loading}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {loading ? 'Calculating...' : 'Compare'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ComparisonModal; 