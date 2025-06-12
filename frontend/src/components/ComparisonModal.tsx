import React, { useState, useEffect } from 'react';

const API_SERVER_URL = 'http://162.243.223.158:8000';

interface ComparisonModalProps {
  isOpen: boolean;
  onClose: () => void;
  textToCompare: string;
  textType: 'original' | 'transliteration';
  // isNonLatinLanguage?: boolean;
}

interface AlignmentEntry {
  ref: string | null;
  hyp: string | null;
  type: 'match' | 'substitution' | 'insertion' | 'deletion';
  cost: number;
}

interface WERResponse {
  wer_details: {
    semantic_wer_percentage: number;
    total_words: number;
    total_cost: number;
    alignment: AlignmentEntry[];
  };
  success: boolean;
}

/* --- Highlight colours for each alignment type --- */
const cssStyles = `
.word-comparison .match { color: green; }
.word-comparison .substitution { color: orange; background-color: rgba(255, 165, 0, 0.1); }
.word-comparison .deletion { color: red; text-decoration: line-through; background-color: rgba(255, 0, 0, 0.1); }
.word-comparison .insertion { color: violet; background-color: rgba(238, 130, 238, 0.1); }
`;

const ComparisonModal: React.FC<ComparisonModalProps> = ({
  isOpen,
  onClose,
  textToCompare,
  textType,
  // isNonLatinLanguage = false,
}) => {
  const [referenceText, setReferenceText] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<WERResponse | null>(null);
  const [error, setError] = useState('');

  /* Inject / clean up the colour-coding CSS only while the modal is open */
  useEffect(() => {
    if (isOpen) {
      if (!document.getElementById('wer-comparison-styles')) {
        const styleTag = document.createElement('style');
        styleTag.id = 'wer-comparison-styles';
        styleTag.innerHTML = cssStyles;
        document.head.appendChild(styleTag);
      }
    }
    return () => {
      const existingStyle = document.getElementById('wer-comparison-styles');
      if (existingStyle) document.head.removeChild(existingStyle);
    };
  }, [isOpen]);

  if (!isOpen) return null;

  /* Call your backend to calculate WER */
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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reference: referenceText, hypothesis: textToCompare }),
      });
      const data = await response.json();
      if (data.success) setResults(data);
      else setError(data.error || 'Failed to calculate WER');
    } catch (err) {
      setError('Network error when calculating WER');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  /* Render every aligned word as a coloured <span> */
  const formatWords = (entries: AlignmentEntry[], field: 'ref' | 'hyp') =>
    entries.map((entry, index) =>
      entry[field] ? (
        <span key={index} className={`${entry.type} mr-1 mb-1 inline-block`}>
          {entry[field]}
        </span>
      ) : null,
    );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">
            Compare with Reference Text ({textType})
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Reference text input */}
        <textarea
          value={referenceText}
          onChange={(e) => setReferenceText(e.target.value)}
          className="w-full h-32 p-2 border border-gray-300 rounded-md mb-4"
          placeholder="Enter reference text to compare with..."
        />

        {error && (
          <div className="mb-4 p-2 bg-red-100 text-red-700 rounded-md">{error}</div>
        )}

        {/* The text that will be compared */}
        <div className="mb-4">
          <h3 className="font-medium text-gray-700 mb-2">Text to compare:</h3>
          <div className="p-2 bg-gray-100 rounded-md max-h-32 overflow-y-auto">
            {textToCompare || <em className="text-gray-500">No text provided.</em>}
          </div>
        </div>

        {/* Results section */}
        {results && (
          <>
            {/* Metrics */}
            <div className="mb-4 p-3 bg-blue-50 rounded-md">
              <h3 className="font-medium text-blue-700 mb-2">Error Metrics:</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  <p className="text-sm text-gray-500">Semantic Word Error Rate</p>
                  <p className="text-lg font-bold">
                    {results.wer_details.semantic_wer_percentage.toFixed(2)}%
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-gray-500">Total Words</p>
                  <p className="text-lg font-bold">
                    {results.wer_details.total_words}
                  </p>
                </div>
              </div>
            </div>

            {/* Colour-coded comparison */}
            <div className="mb-4">
              <h3 className="font-medium text-gray-700 mb-2">Color-Coded Comparison:</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 word-comparison">
                {/* Reference */}
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-1">Reference:</p>
                  <div className="p-3 bg-white border border-gray-200 rounded-md flex flex-wrap gap-1 max-h-64 overflow-y-auto">
                    {formatWords(results.wer_details.alignment, 'ref')}
                  </div>
                </div>

                {/* Hypothesis */}
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-1">
                    Hypothesis:
                  </p>
                  <div className="p-3 bg-white border border-gray-200 rounded-md flex flex-wrap gap-1 max-h-64 overflow-y-auto">
                    {formatWords(results.wer_details.alignment, 'hyp')}
                  </div>
                </div>
              </div>
            </div>

            {/* Legend */}
            <div className="mb-4">
              <h3 className="font-medium text-gray-700 mb-2">Legend:</h3>
              <div className="flex flex-wrap gap-3">
                <span className="text-sm">
                  <span className="inline-block w-3 h-3 bg-green-500 rounded-full mr-1"></span>
                  Correct
                </span>
                <span className="text-sm">
                  <span className="inline-block w-3 h-3 bg-amber-500 rounded-full mr-1"></span>
                  Substitution
                </span>
                <span className="text-sm">
                  <span className="inline-block w-3 h-3 bg-red-500 rounded-full mr-1"></span>
                  Deletion
                </span>
                <span className="text-sm">
                  <span className="inline-block w-3 h-3 bg-violet-500 rounded-full mr-1"></span>
                  Insertion
                </span>
              </div>
            </div>
          </>
        )}

        {/* Footer buttons */}
        <div className="flex justify-end">
          <button
            onClick={onClose}
            className="mr-2 px-4 py-2 border border-gray-300 rounded-md text-sm text-gray-700 hover:bg-gray-50"
          >
            Close
          </button>
          <button
            onClick={handleCompare}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Calculating...' : 'Compare'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ComparisonModal;
