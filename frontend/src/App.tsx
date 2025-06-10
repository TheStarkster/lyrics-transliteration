import { useState, useEffect, useRef } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
// import './App.css'
import { TabView } from './components/types'
import type { TranscriptSegment } from './components/types'
import Header from './components/Header'
import HeroSection from './components/HeroSection'
import UploadSection from './components/UploadSection'
import ProgressSection from './components/ProgressSection'
import ResultsSection from './components/ResultsSection'
import Footer from './components/Footer'
import PrivacyPolicy from './components/PrivacyPolicy'
import TermsOfService from './components/TermsOfService'
import ContactUs from './components/ContactUs'
import DarkModeToggle from './components/DarkModeToggle'
import ComparisonModal from './components/ComparisonModal'
import { formatSRTTime } from './components/utils'

// List of languages that may have encoding or display issues
const NON_LATIN_LANGUAGES = ['hindi', 'telugu', 'tamil', 'bengali', 'marathi', 'gujarati', 'kannada', 'malayalam', 'odia', 'punjabi', 
  'arabic', 'urdu', 'persian', 'chinese', 'japanese', 'korean', 'thai', 'khmer', 'lao', 'burmese', 'tibetan'];

// Helper function to ensure text is available for comparison
const ensureTextAvailability = (text: string, isNonLatinScript: boolean): string => {
  if (!text) return '';
  
  // For non-Latin scripts, ensure the text is properly encoded
  if (isNonLatinScript) {
    // Check if the text appears to be empty or just whitespace when it shouldn't be
    if (text.trim().length === 0 && text.length > 0) {
      // Return the raw text even if it might have encoding issues
      return text;
    }
  }
  
  return text;
};

// Constants
const WS_SERVER_URL = 'ws://162.243.223.158:8000';
const API_SERVER_URL = 'http://162.243.223.158:8000';
const CLIENT_ID_STORAGE_KEY = 'lyrics_transliteration_client_id';

function MainApp() {
  const [file, setFile] = useState<File | null>(null)
  const [transcript, setTranscript] = useState<string>('')
  const [transliteration, setTransliteration] = useState<string>('')
  const [segments, setSegments] = useState<TranscriptSegment[]>([])
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState<string[]>([])
  const [clientId, setClientId] = useState('')
  const [wsConnected, setWsConnected] = useState(false)
  const [language, setLanguage] = useState<string>('')
  const [activeTab, setActiveTab] = useState<TabView>(TabView.ORIGINAL)
  const [model, setModel] = useState<string>('large-v3')
  const [beamSize, setBeamSize] = useState<number>(20)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)
  const [isComparisonModalOpen, setIsComparisonModalOpen] = useState(false)

  // Generate or retrieve client ID from localStorage
  useEffect(() => {
    const storedClientId = localStorage.getItem(CLIENT_ID_STORAGE_KEY);
    
    if (storedClientId) {
      console.log('Retrieved client ID from storage:', storedClientId);
      setClientId(storedClientId);
    } else {
      const newClientId = Math.random().toString(36).substring(2, 15);
      console.log('Generated new client ID:', newClientId);
      localStorage.setItem(CLIENT_ID_STORAGE_KEY, newClientId);
      setClientId(newClientId);
    }
  }, []);

  // Set up WebSocket connection with reconnection logic
  useEffect(() => {
    if (!clientId) return;

    // Function to set up WebSocket connection
    const setupWebSocket = () => {
      console.log('Setting up WebSocket with client ID:', clientId);
      
      // Close any existing connection
      if (wsRef.current) {
        wsRef.current.close();
      }
      
      // Create a new WebSocket connection
      const ws = new WebSocket(`${WS_SERVER_URL}/ws/${clientId}`);
      
      ws.onopen = () => {
        console.log('WebSocket connected with client ID:', clientId);
        setWsConnected(true);
        
        // Clear any reconnection timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
        
        // Start sending heartbeats every 30 seconds
        const heartbeatInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping'); // Use lowercase to match backend
            console.log('Sent heartbeat ping');
          }
        }, 30000);
        
        // Store the interval ID for cleanup
        return () => clearInterval(heartbeatInterval);
      };
      
      ws.onmessage = (event) => {
        console.log('WebSocket message received:', event.data);
        
        // Handle simple pong response
        if (event.data === 'pong') {
          console.log('Received heartbeat pong');
          return;
        }
        
        // Process all other messages as regular status updates or JSON data
        try {
          // Check if this is JSON data (result)
          const jsonData = JSON.parse(event.data);
          console.log('Parsed JSON data:', jsonData);
          
          if (jsonData.status === 'complete') {
            if (jsonData.segments) {
              // Process original segments
              const originalSegments = jsonData.segments.map((segment: any, index: number) => ({
                ...segment,
                id: segment.id || index,
                transliteration: '' // Add empty transliteration if not present
              }));
              
              // Process transliterated segments if available
              if (jsonData.transliterated_segments && jsonData.transliterated_segments.length > 0) {
                // Merge transliterated text into the original segments
                originalSegments.forEach((segment: TranscriptSegment, i: number) => {
                  if (i < jsonData.transliterated_segments.length) {
                    segment.transliteration = jsonData.transliterated_segments[i].text || '';
                  }
                });
                
                // Build the full transliteration text
                const fullTransliteration = jsonData.transliterated_segments
                  .map((segment: any) => segment.text || '')
                  .join(' ')
                  .trim();
                
                setTransliteration(fullTransliteration);
              }
              
              setSegments(originalSegments);
              
              // Set the full transcript text - ensure proper handling of text
              const isNonLatin = NON_LATIN_LANGUAGES.includes(language.toLowerCase());
              const fullText = jsonData.full_text || jsonData.text || '';
              
              // Log the text details for debugging
              console.log('Language:', language, 'Is non-Latin:', isNonLatin);
              console.log('Full text length:', fullText.length);
              console.log('Sample of text:', fullText.substring(0, 50));
              
              setTranscript(fullText);
            }
            
            // Add a friendly message to progress
            setProgress(prev => [...prev, "✨ Processing complete! Results displayed below."]);
            setLoading(false);
          }
        } catch (error) {
          // Not JSON, treat as regular progress message
          setProgress(prev => [...prev, event.data]);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setWsConnected(false);
      };
      
      ws.onclose = (event) => {
        console.log(`WebSocket closed with code ${event.code}, reason: ${event.reason}`);
        setWsConnected(false);
        
        // Attempt to reconnect after 3 seconds
        reconnectTimeoutRef.current = window.setTimeout(() => {
          console.log('Attempting to reconnect WebSocket...');
          setupWebSocket();
        }, 3000);
      };
      
      wsRef.current = ws;
    };
    
    // Initial setup
    setupWebSocket();
    
    // Cleanup function
    return () => {
      console.log('Cleaning up WebSocket connection');
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [clientId]);

  // Add window beforeunload event to notify server when page is closed
  useEffect(() => {
    const handleBeforeUnload = () => {
      // Try to close WebSocket gracefully if it's open
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        // We can't send a message here as the page is unloading
        // The server will detect the disconnect on its own
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setLanguage(e.target.value)
  }
  
  const handleModelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setModel(e.target.value)
  }
  
  const handleBeamSizeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setBeamSize(parseInt(e.target.value))
  }

  const handleUpload = async () => {
    if (!file || !clientId) return;

    setLoading(true);
    setProgress([]);
    setTranscript('');
    setTransliteration('');
    setSegments([]);

    console.log('Uploading file with client ID:', clientId);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      // Add language, model and beam size parameters to the request
      const response = await fetch(
        `${API_SERVER_URL}/upload?client_id=${clientId}&language=${language}&model=${model}&beam_size=${beamSize}`, 
        {
          method: 'POST',
          body: formData,
        }
      );
      
      if (!response.ok) {
        throw new Error(`Upload failed with status ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Upload response:', data);
      setProgress(prev => [
        ...prev, 
        `${data.message} for ${data.language} language using ${data.model} model`
      ]);
      
    } catch (error) {
      console.error('Error uploading file:', error);
      setProgress(prev => [...prev, `Error: ${error}`]);
      setLoading(false);
    }
  };

  // Replace queue status check with a simple status display
  // const checkQueueStatus = async () => {
  //   if (!clientId) return;
    
  //   setProgress(prev => [
  //     ...prev, 
  //     `WebSocket connection is active with client ID: ${clientId}`
  //   ]);
  // };

  // Tab switching handler
  const handleTabChange = (tab: TabView) => {
    setActiveTab(tab);
  }

  // Handler for opening comparison modal
  const openComparisonModal = () => {
    setIsComparisonModalOpen(true);
  }

  // Handler for closing comparison modal
  const closeComparisonModal = () => {
    setIsComparisonModalOpen(false);
  }

  // Get the current text based on active tab
  const getCurrentText = () => {
    const isNonLatin = NON_LATIN_LANGUAGES.includes(language.toLowerCase());
    
    if (activeTab === TabView.ORIGINAL) {
      // For non-Latin scripts in original tab, ensure we have content even if display issues occur
      return ensureTextAvailability(transcript, isNonLatin);
    } else {
      return ensureTextAvailability(transliteration, isNonLatin);
    }
  }

  // Handler for removing a segment
  const handleRemoveSegment = (segmentId: number) => {
    setSegments(prev => prev.filter(segment => segment.id !== segmentId));
  }

  // Handler for updating a segment
  const handleUpdateSegment = (segmentId: number, field: 'text' | 'transliteration', value: string) => {
    setSegments(prev => 
      prev.map(segment => 
        segment.id === segmentId 
          ? { ...segment, [field]: value } 
          : segment
      )
    );
  }

  // Function to generate SRT content
  const generateSRT = () => {
    if (!segments.length) return '';
    
    return segments.map((segment, i) => {
      const startTime = formatSRTTime(segment.start);
      const endTime = formatSRTTime(segment.end);
      const text = activeTab === TabView.ORIGINAL ? segment.text : segment.transliteration || '';
      
      // Trim any leading or trailing whitespace from the text
      const trimmedText = text.trim();
      
      return `${i + 1}\n${startTime} --> ${endTime}\n${trimmedText}\n`;
    }).join('\n');
  };
  
  // Download SRT file
  const downloadSRT = () => {
    if (!segments.length) return;
    
    const srtContent = generateSRT();
    const blob = new Blob([srtContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    
    a.href = url;
    a.download = `lyrics_${activeTab === TabView.ORIGINAL ? language : 'transliteration'}.srt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <Header wsConnected={wsConnected} />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <HeroSection />
        
        <UploadSection 
          file={file}
          setFile={setFile}
          language={language}
          handleLanguageChange={handleLanguageChange}
          handleUpload={handleUpload}
          loading={loading}
          wsConnected={wsConnected}
          clientId={clientId}
          model={model}
          handleModelChange={handleModelChange}
          beamSize={beamSize}
          handleBeamSizeChange={handleBeamSizeChange}
        />
        
        <ProgressSection progress={progress} loading={loading} />
        
        <ResultsSection 
          transcript={transcript}
          transliteration={transliteration}
          segments={segments}
          activeTab={activeTab}
          handleTabChange={handleTabChange}
          language={language}
          downloadSRT={downloadSRT}
          handleRemoveSegment={handleRemoveSegment}
          handleUpdateSegment={handleUpdateSegment}
          openComparisonModal={openComparisonModal}
        />

        {/* Comparison Modal */}
        <ComparisonModal
          isOpen={isComparisonModalOpen}
          onClose={closeComparisonModal}
          textToCompare={getCurrentText()}
          textType={activeTab === TabView.ORIGINAL ? 'original' : 'transliteration'}
          isNonLatinLanguage={NON_LATIN_LANGUAGES.includes(language.toLowerCase())}
        />
      </main>
      
      <Footer />
    </div>
  )
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainApp />} />
        <Route path="/privacy-policy" element={<PrivacyPolicy />} />
        <Route path="/terms-of-service" element={<TermsOfService />} />
        <Route path="/contact" element={<ContactUs />} />
        <Route path="/brand" element={<BrandPage />} />
      </Routes>
    </Router>
  )
}

// Brand page for logo preview
function BrandPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <Header wsConnected={true} />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <Link to="/" className="inline-flex items-center text-blue-600 hover:text-blue-800">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
            </svg>
            Back to Home
          </Link>
        </div>
        
        <h1 className="text-3xl font-bold mb-6">DestinPQ Brand</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <DarkModeToggle />
          
          <div className="p-6 bg-white rounded-lg shadow-md">
            <h2 className="text-lg font-semibold mb-4">Brand Guidelines</h2>
            <p className="text-sm text-gray-600 mb-4">
              The DestinPQ logo uses an inverted color scheme, with a light background and dark text for standard usage, and a dark background with light text for dark mode interfaces.
            </p>
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Primary Colors</h3>
                <div className="flex space-x-2">
                  <div className="w-12 h-12 bg-blue-600 rounded-md"></div>
                  <div className="w-12 h-12 bg-blue-800 rounded-md"></div>
                  <div className="w-12 h-12 bg-white border border-gray-200 rounded-md"></div>
                  <div className="w-12 h-12 bg-gray-800 rounded-md"></div>
                </div>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Font</h3>
                <p className="text-sm text-gray-600">
                  DestinPQ uses a modern sans-serif font for all branding materials.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
      
      <Footer />
    </div>
  );
}

export default App
