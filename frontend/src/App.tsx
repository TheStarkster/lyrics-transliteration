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
import { formatSRTTime } from './components/utils'

function MainApp() {
  const [file, setFile] = useState<File | null>(null)
  const [transcript, setTranscript] = useState<string>('')
  const [transliteration, setTransliteration] = useState<string>('')
  const [segments, setSegments] = useState<TranscriptSegment[]>([])
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState<string[]>([])
  const [clientId, setClientId] = useState('')
  const [wsConnected, setWsConnected] = useState(false)
  const [language, setLanguage] = useState<string>('te')
  const [activeTab, setActiveTab] = useState<TabView>(TabView.ORIGINAL)
  const [model, setModel] = useState<string>('large-v3')
  const [beamSize, setBeamSize] = useState<number>(20)
  const wsRef = useRef<WebSocket | null>(null)

  // Generate a client ID on component mount only
  useEffect(() => {
    const id = Math.random().toString(36).substring(2, 15)
    console.log('Generated client ID:', id)
    setClientId(id)
  }, [])

  // Set up WebSocket connection after client ID is set
  useEffect(() => {
    if (!clientId) return

    console.log('Setting up WebSocket with client ID:', clientId)
    
    // Close any existing connection
    if (wsRef.current) {
      wsRef.current.close()
    }
    
    // Create a new WebSocket connection
    const ws = new WebSocket(`ws://162.243.223.158:8000/ws/${clientId}`)
    
    ws.onopen = () => {
      console.log('WebSocket connected with client ID:', clientId)
      setWsConnected(true)
    }
    
    ws.onmessage = (event) => {
      console.log('WebSocket message received:', event.data)
      
      // Check if this is a result message
      if (event.data.startsWith('RESULT:')) {
        try {
          // Extract and parse the JSON result
          const resultData = JSON.parse(event.data.substring(7));
          console.log('Parsed result data:', resultData);
          
          if (resultData.segments) {
            setSegments(resultData.segments);
            setTranscript(resultData.text || '');
            setTransliteration(resultData.transliteration || '');
          } else {
            setTranscript(resultData.text || '');
            setTransliteration(resultData.transliteration || '');
          }
          
          // Add a friendly message to progress
          setProgress(prev => [...prev, "✨ Processing complete! Results displayed below."]);
          setLoading(false);
        } catch (error) {
          console.error('Error parsing result data:', error);
          setProgress(prev => [...prev, `Error parsing result: ${error}`]);
          setLoading(false);
        }
      } else {
        // Regular progress message
        setProgress(prev => [...prev, event.data]);
      }
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setWsConnected(false)
    }
    
    ws.onclose = () => {
      console.log('WebSocket closed')
      setWsConnected(false)
    }
    
    wsRef.current = ws
    
    // Cleanup function
    return () => {
      console.log('Cleaning up WebSocket connection')
      ws.close()
    }
  }, [clientId])

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
    if (!file || !clientId) return

    setLoading(true)
    setProgress([])
    setTranscript('')
    setTransliteration('')
    setSegments([])

    console.log('Uploading file with client ID:', clientId, 'language:', language, 'model:', model, 'beam size:', beamSize)
    
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const response = await fetch(`http://162.243.223.158:8000/upload/?client_id=${clientId}&language=${language}&model=${model}&beam_size=${beamSize}&return_segments=true`, {
        method: 'POST',
        body: formData,
      })
      
      if (!response.ok) {
        throw new Error(`Upload failed with status ${response.status}`)
      }
      
      const data = await response.json()
      console.log('Upload response:', data)
      setProgress(prev => [...prev, `${data.message}`])
      
    } catch (error) {
      console.error('Error uploading file:', error)
      setProgress(prev => [...prev, `Error: ${error}`])
      setLoading(false)
    }
  }

  // Tab switching handler
  const handleTabChange = (tab: TabView) => {
    setActiveTab(tab);
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
