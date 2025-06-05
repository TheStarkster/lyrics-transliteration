import { useState, useEffect, useRef } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

interface TranscriptSegment {
  id: number;
  start: number;
  end: number;
  text: string;
}

function App() {
  const [file, setFile] = useState<File | null>(null)
  const [transcript, setTranscript] = useState<string>('')
  const [segments, setSegments] = useState<TranscriptSegment[]>([])
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState<string[]>([])
  const [clientId, setClientId] = useState('')
  const [wsConnected, setWsConnected] = useState(false)
  const [language, setLanguage] = useState<string>('Telugu')
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
          } else if (resultData.transcript) {
            setTranscript(resultData.transcript);
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
      
      // Note: We don't set transcript or segments here anymore
      // They will be set when we receive the result via WebSocket
      // We also don't set loading=false here, as the process is still ongoing
      
    } catch (error) {
      console.error('Error uploading file:', error)
      setProgress(prev => [...prev, `Error: ${error}`])
      setLoading(false)
    }
  }

  return (
    <>
      <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Lyrics Transcription App</h1>
      
      <div className="card">
        <div style={{ marginBottom: '10px' }}>
          <small>Connection Status: {wsConnected ? '🟢 Connected' : '🔴 Disconnected'}</small>
          {clientId && <small style={{ marginLeft: '10px' }}>Client ID: {clientId}</small>}
        </div>
        
        <input type="file" accept="audio/*" onChange={handleFileChange} />
        
        <div style={{ marginTop: '10px', marginBottom: '10px' }}>
          <label htmlFor="language-select">Transcription Language: </label>
          <select 
            id="language-select" 
            value={language} 
            onChange={handleLanguageChange}
            style={{ marginLeft: '5px' }}
          >
            <option value="Telugu">Telugu</option>
            <option value="Hindi">Hindi</option>
          </select>
        </div>
        
        <button 
          onClick={handleUpload} 
          disabled={!file || loading || !wsConnected || !clientId}
          style={{ marginTop: '10px' }}
        >
          {!wsConnected ? 'Connecting...' : loading ? 'Processing...' : 'Upload and Transcribe'}
        </button>
        {!wsConnected && <p style={{ color: 'orange' }}>Waiting for connection to server...</p>}
      </div>
      
      {progress.length > 0 && (
        <div className="card">
          <h3>Progress: {loading && <span className="loading-spinner">⏳</span>}</h3>
          <ul>
            {progress.map((msg, index) => (
              <li key={index}>{msg}</li>
            ))}
          </ul>
        </div>
      )}
      
      {segments.length > 0 ? (
        <div className="card">
          <h3>Transcript with Timestamps ({language}):</h3>
          <div className="segments-container">
            {segments.map((segment, index) => (
              <div key={index} className="segment">
                <span className="timestamp">[{formatTime(segment.start)} - {formatTime(segment.end)}]</span>
                <span className="segment-text">{segment.text}</span>
              </div>
            ))}
          </div>
        </div>
      ) : transcript ? (
        <div className="card">
          <h3>Transcript ({language}):</h3>
          <pre>{transcript}</pre>
        </div>
      ) : null}
      
      <p className="read-the-docs">
        Upload an audio file to transcribe the lyrics
      </p>
    </>
  )
}

export default App
