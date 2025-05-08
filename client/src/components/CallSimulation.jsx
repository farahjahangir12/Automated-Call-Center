import { useState, useEffect, useCallback, useRef } from 'react';
import Waveform from './WaveForm';

const CallControls = ({ isRecording, setIsRecording, onNewMessage, onAgentChange }) => {
  const [audioLevel, setAudioLevel] = useState(0);
  const [transcription, setTranscription] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  
  // References for audio recording
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const sessionIdRef = useRef(null);
  
  // Handle audio recording toggle (same implementation as before)
  const toggleRecording = useCallback(async () => {
    const newRecordingState = !isRecording;
    setIsRecording(newRecordingState);
    
    if (newRecordingState) {
      // Implementation unchanged - start recording
      try {
        setError(null);
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
        analyserRef.current = audioContextRef.current.createAnalyser();
        analyserRef.current.fftSize = 256;
        
        const source = audioContextRef.current.createMediaStreamSource(stream);
        source.connect(analyserRef.current);
        
        const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
        
        const updateVisualization = () => {
          analyserRef.current.getByteFrequencyData(dataArray);
          const sum = Array.from(dataArray).reduce((a, b) => a + b, 0);
          const avg = sum / dataArray.length / 255;
          setAudioLevel(avg);
          
          animationFrameRef.current = requestAnimationFrame(updateVisualization);
        };
        
        updateVisualization();
        
        audioChunksRef.current = [];
        mediaRecorderRef.current = new MediaRecorder(stream);
        
        mediaRecorderRef.current.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };
        
        mediaRecorderRef.current.start();
        console.log("Recording started");
      } catch (err) {
        console.error("Error accessing microphone:", err);
        setError("Could not access microphone. Please ensure you've granted permission.");
        setIsRecording(false);
      }
    } else {
      // Implementation unchanged - stop recording
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        console.log("Stopping recording and processing audio...");
        mediaRecorderRef.current.stop();
        
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
          setAudioLevel(0);
        }
        
        if (audioContextRef.current) {
          audioContextRef.current.close();
          audioContextRef.current = null;
        }
        
        mediaRecorderRef.current.onstop = async () => {
          setIsProcessing(true);
          
          try {
            const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');
            
            if (sessionIdRef.current) {
              formData.append('session_id', sessionIdRef.current);
            }
            
            const response = await fetch('http://localhost:5000/api/process-audio', {
              method: 'POST',
              body: formData,
            });
            
            if (!response.ok) {
              throw new Error(`Server error: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.session_id) {
              sessionIdRef.current = result.session_id;
              setSessionId(result.session_id);
            }
            
            if (result.transcription) {
              setTranscription(result.transcription);
              onNewMessage({
                text: result.transcription,
                sender: 'user',
                timestamp: new Date().toISOString()
              });
            }
            
            if (result.response) {
              onNewMessage({
                text: result.response,
                sender: 'agent',
                agentType: result.agent_type || 'RAG',
                timestamp: new Date().toISOString()
              });
              
              if (result.agent_type) {
                onAgentChange(result.agent_type);
              }
            }
          } catch (err) {
            console.error("Error processing audio:", err);
            setError("Error processing your message. Please try again.");
          } finally {
            setIsProcessing(false);
          }
        };
      }
      
      if (mediaRecorderRef.current && mediaRecorderRef.current.stream) {
        mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      }
    }
  }, [isRecording, setIsRecording, onNewMessage, onAgentChange]);
  
  // Cleanup (unchanged)
  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      
      if (mediaRecorderRef.current && mediaRecorderRef.current.stream) {
        mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      }
      
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);
  
  // Updated UI with hospital theming
  return (
    <div className="flex flex-col space-y-6">
      {/* Error display */}
      {error && (
        <div className="mb-2 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg flex items-center">
          <svg className="w-5 h-5 mr-2 text-red-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <p>{error}</p>
        </div>
      )}
      
      {/* Recording status and medical session info */}
      <div className="bg-blue-50 rounded-lg p-4 border border-blue-100 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
            isRecording 
              ? 'bg-red-100 text-red-600 animate-pulse' 
              : isProcessing
                ? 'bg-amber-100 text-amber-600'
                : 'bg-green-100 text-green-600'
          }`}>
            {isProcessing ? (
              <svg className="w-6 h-6 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : isRecording ? (
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
              </svg>
            )}
          </div>
          
          <div>
            <h3 className="font-medium text-gray-800">
              {isRecording ? 'Recording in Progress' : isProcessing ? 'Processing Audio' : 'Ready to Record'}
            </h3>
            <p className="text-sm text-gray-600">
              {isRecording ? 'Speak clearly into your microphone' : isProcessing ? 'Please wait...' : 'Click the button below to begin'}
            </p>
          </div>
        </div>
        
        {sessionId && (
          <div className="flex flex-col items-end">
            <div className="text-xs bg-white px-2 py-1 rounded text-blue-800 font-medium border border-blue-200">
              Patient Session
            </div>
            <div className="text-xs text-gray-500 mt-0.5">ID: {sessionId.substring(0, 8)}...</div>
          </div>
        )}
      </div>
      
      {/* Audio waveform visualization */}
      <div>
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <Waveform audioLevel={audioLevel} />
        </div>
        <div className="text-xs text-center mt-2 text-gray-500">
          Audio levels are monitored for optimal voice recognition
        </div>
      </div>
      
      {/* Record button */}
      <div className="flex justify-center">
        <button 
          onClick={toggleRecording}
          disabled={isProcessing}
          className={`group relative flex items-center justify-center space-x-2 px-6 py-3 rounded-full transition-all duration-200 ${
            isRecording 
              ? 'bg-red-600 text-white shadow-lg hover:bg-red-700'
              : isProcessing
                ? 'bg-amber-400 text-white cursor-wait'
                : 'bg-blue-600 text-white hover:bg-blue-700 hover:shadow'
          }`}
          aria-label={isRecording ? 'Stop Recording' : 'Start Recording'}
        >
          {/* Pulse animation for recording state */}
          {isRecording && (
            <span className="absolute w-full h-full rounded-full animate-ping bg-red-600 opacity-30"></span>
          )}
          
          {/* Button icon */}
          <span className={`flex items-center justify-center w-6 h-6 ${isProcessing ? 'animate-spin' : ''}`}>
            {isProcessing ? (
              <svg className="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : isRecording ? (
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M5.25 3A2.25 2.25 0 003 5.25v9.5A2.25 2.25 0 005.25 17h9.5A2.25 2.25 0 0017 14.75v-9.5A2.25 2.25 0 0014.75 3h-9.5z" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
              </svg>
            )}
          </span>
          
          {/* Button text */}
          <span className="font-medium">
            {isRecording ? 'Stop Recording' : isProcessing ? 'Processing...' : 'Start Recording'}
          </span>
        </button>
      </div>
      
      {/* Transcription display */}
      {transcription && (
        <div className="mt-1 bg-white border border-slate-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
            </svg>
            <h3 className="text-sm font-semibold text-gray-700">Last Transcription</h3>
          </div>
          <div className="bg-slate-50 border border-slate-100 rounded-lg p-3">
            <p className="text-gray-800">{transcription}</p>
          </div>
        </div>
      )}
      
      {/* Help text */}
      <div className="text-center text-gray-500 text-sm border-t border-gray-100 pt-4">
        <p className="flex items-center justify-center">
          <svg className="w-4 h-4 mr-2 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2h-1V9a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          Click the record button and speak clearly for best results
        </p>
      </div>
    </div>
  );
};

const CallSimulation = (props) => {
  return (
    <CallControls 
      isRecording={props.isRecording} 
      setIsRecording={props.setIsRecording}
      onNewMessage={props.onNewMessage}
      onAgentChange={props.onAgentChange}
    />
  );
};

export default CallSimulation;