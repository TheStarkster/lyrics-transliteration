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