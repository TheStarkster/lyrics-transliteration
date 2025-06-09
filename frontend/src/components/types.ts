export interface TranscriptSegment {
  id: number;
  start: number;
  end: number;
  text: string;
  transliteration?: string;
}

// Tabs enum for better type safety
export enum TabView {
  ORIGINAL = 'original',
  TRANSLITERATION = 'transliteration'
}

export interface WordAlignment {
  word?: string;
  reference_word?: string;
  hypothesis_word?: string;
  type: 'correct' | 'substitution' | 'deletion' | 'insertion';
  reference_index?: number;
  hypothesis_index?: number;
}

export interface WERResponse {
  wer: number;
  mer: number;
  wil: number;
  substitutions?: number;
  deletions?: number;
  insertions?: number;
  total_words?: number;
  reference_html?: string;
  hypothesis_html?: string;
  word_alignments?: WordAlignment[];
  success: boolean;
  error?: string;
} 