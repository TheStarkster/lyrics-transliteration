import { useState, useEffect, useRef } from 'react'
import './App.css'

interface TranscriptSegment {
  id: number;
  start: number;
  end: number;
  text: string;
  transliteration?: string;
}

// Tabs enum for better type safety
enum TabView {
  ORIGINAL = 'original',
  TRANSLITERATION = 'transliteration'
}

function App() {
  const [file, setFile] = useState<File | null>(null)
  const [transcript, setTranscript] = useState<string>('')
  const [transliteration, setTransliteration] = useState<string>('')
  const [segments, setSegments] = useState<TranscriptSegment[]>([])
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState<string[]>([])
  const [clientId, setClientId] = useState('')
  const [wsConnected, setWsConnected] = useState(false)
  const [language, setLanguage] = useState<string>('Telugu')
  const [activeTab, setActiveTab] = useState<TabView>(TabView.ORIGINAL)
  const wsRef = useRef<WebSocket | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

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
    const ws = new WebSocket(`ws://98.70.40.41:8000/ws/${clientId}`)
    
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

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0])
    }
  }

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setLanguage(e.target.value)
  }

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleUpload = async () => {
    if (!file || !clientId) return

    setLoading(true)
    setProgress([])
    setTranscript('')
    setTransliteration('')
    setSegments([])

    console.log('Uploading file with client ID:', clientId, 'language:', language)
    
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const response = await fetch(`http://98.70.40.41:8000/upload/?client_id=${clientId}&language=${language}&return_segments=true`, {
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

  // Function to generate SRT content
  const generateSRT = () => {
    if (!segments.length) return '';
    
    return segments.map((segment, i) => {
      const startTime = formatSRTTime(segment.start);
      const endTime = formatSRTTime(segment.end);
      const text = activeTab === TabView.ORIGINAL ? segment.text : segment.transliteration || '';
      
      return `${i + 1}\n${startTime} --> ${endTime}\n${text}\n`;
    }).join('\n');
  };
  
  // Format time for SRT (00:00:00,000)
  const formatSRTTime = (seconds: number): string => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds - Math.floor(seconds)) * 1000);
    
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')},${ms.toString().padStart(3, '0')}`;
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

  // Function to trigger file input click
  const triggerFileInput = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center">
            <h1 className="text-2xl font-bold text-primary">LyricAI</h1>
            <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full uppercase font-medium">Beta</span>
          </div>
          <div className="flex items-center space-x-1">
            <span className={`h-2 w-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`}></span>
            <span className="text-sm text-gray-500">{wsConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <section className="text-center mb-12">
          <h2 className="text-4xl font-extrabold text-gray-900 mb-4">AI-Powered Lyrics Extraction</h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Upload any song and get accurate lyrics with timestamps in seconds. Export as SRT for your videos or projects.
          </p>
        </section>

        {/* Upload Section */}
        <section className="bg-white rounded-xl shadow-md p-6 mb-8">
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Upload Your Audio</h3>
              
              <div 
                onClick={triggerFileInput}
                className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-primary transition-colors"
              >
                <input 
                  ref={fileInputRef}
                  type="file" 
                  accept="audio/*" 
                  onChange={handleFileChange} 
                  className="hidden"
                />
                
                {file ? (
                  <div className="space-y-2">
                    <div className="w-12 h-12 bg-blue-100 text-primary rounded-full flex items-center justify-center mx-auto">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                      </svg>
                    </div>
                    <p className="text-sm font-medium text-gray-900">{file.name}</p>
                    <p className="text-xs text-gray-500">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                    <button 
                      onClick={(e) => { e.stopPropagation(); setFile(null); }}
                      className="text-xs text-red-600 hover:text-red-800"
                    >
                      Remove
                    </button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                    </div>
                    <p className="text-sm font-medium text-gray-700">Drag and drop your audio file here</p>
                    <p className="text-xs text-gray-500">Or click to browse</p>
                    <p className="text-xs text-gray-400">Supports MP3, WAV, M4A, etc.</p>
                  </div>
                )}
              </div>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Configuration</h3>
              
              <div className="space-y-4">
                <div>
                  <label htmlFor="language-select" className="block text-sm font-medium text-gray-700 mb-1">
                    Language
                  </label>
                  <select 
                    id="language-select" 
                    value={language} 
                    onChange={handleLanguageChange}
                    className="w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
                  >
                    <option value="Telugu">Telugu</option>
                    <option value="Hindi">Hindi</option>
                  </select>
                  <p className="mt-1 text-xs text-gray-500">Select the language of your audio file</p>
                </div>
                
                <button 
                  onClick={handleUpload} 
                  disabled={!file || loading || !wsConnected || !clientId}
                  className={`w-full py-2 px-4 rounded-md text-white font-medium ${!file || loading || !wsConnected || !clientId 
                    ? 'bg-gray-400 cursor-not-allowed' 
                    : 'bg-primary hover:bg-primary/90'} transition-colors shadow-sm flex items-center justify-center`}
                >
                  {loading && (
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  )}
                  {!wsConnected ? 'Connecting to server...' : loading ? 'Processing...' : 'Extract Lyrics'}
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Progress Section */}
        {progress.length > 0 && (
          <section className="bg-white rounded-xl shadow-md p-6 mb-8">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Processing Status</h3>
              {loading && (
                <div className="flex items-center">
                  <div className="animate-pulse bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-xs font-medium">
                    Processing
                  </div>
                </div>
              )}
            </div>
            
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {progress.map((msg, index) => (
                <div 
                  key={index} 
                  className={`py-2 px-3 rounded-lg text-sm ${
                    msg.includes('Error') 
                      ? 'bg-red-50 text-red-700' 
                      : msg.includes('complete') 
                        ? 'bg-green-50 text-green-700'
                        : 'bg-gray-50 text-gray-700'
                  }`}
                >
                  {msg}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Results Section */}
        {(transcript || transliteration) && (
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
                    <div key={index} className="flex text-sm">
                      <span className="text-gray-500 w-16 flex-shrink-0">[{formatTime(segment.start)}]</span>
                      <span className="text-gray-900">{segment.text}</span>
                    </div>
                  ))}
                </div>
              ) : activeTab === TabView.ORIGINAL ? (
                <pre className="whitespace-pre-wrap text-sm text-gray-700">{transcript}</pre>
              ) : null}
              
              {activeTab === TabView.TRANSLITERATION && segments.length > 0 ? (
                <div className="space-y-2">
                  {segments.map((segment, index) => (
                    <div key={index} className="flex text-sm">
                      <span className="text-gray-500 w-16 flex-shrink-0">[{formatTime(segment.start)}]</span>
                      <span className="text-gray-900">{segment.transliteration}</span>
                    </div>
                  ))}
                </div>
              ) : activeTab === TabView.TRANSLITERATION ? (
                <pre className="whitespace-pre-wrap text-sm text-gray-700">{transliteration}</pre>
              ) : null}
            </div>
          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            LyricAI • AI-Powered Lyrics Extraction • © {new Date().getFullYear()}
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App
