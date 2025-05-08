import { useRef, useEffect } from 'react';

const ChatTranscript = ({ messages = [] }) => {
  const messagesEndRef = useRef(null);
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  // Agent type icon mapping
  const agentIcons = {
    'RAG': '📄',
    'GraphRAG': '🔗',
    'SQL': '🗃️',
    'General': '🏥',
    'default': '🤖'
  };
  
  return (
    <div className="flex flex-col h-full">
      <div className="bg-slate-50 border-b border-slate-200">
        <div className="px-6 py-4 flex items-center justify-between">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-blue-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
            </svg>
            <h2 className="text-base font-semibold text-gray-800">Medical Consultation Transcript</h2>
          </div>
          <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
            {messages.length === 0 ? 'No interactions' : `${messages.length} messages`}
          </span>
        </div>
      </div>
      
      <div className="flex-1 p-5 overflow-y-auto flex flex-col gap-5 bg-gradient-to-br from-slate-50 to-white">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center p-8">
            <div className="bg-blue-50 rounded-full p-4 mb-4">
              <svg className="w-12 h-12 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-700 mb-2">No conversation yet</h3>
            <p className="text-gray-500 max-w-sm">
              Start by clicking the microphone button to speak with our hospital virtual assistant.
            </p>
          </div>
        )}
        
        {messages.map((message, index) => (
          <div 
            key={index} 
            className={`max-w-[85%] ${
              message.sender === 'user' 
                ? 'self-end' 
                : 'self-start'
            }`}
          >
            {/* Message author indicator */}
            <div className="flex items-center gap-2 mb-1.5">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                message.sender === 'user' 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'bg-teal-100 text-teal-700'
              }`}>
                {message.sender === 'user' ? '👤' : agentIcons[message.agentType || 'default']}
              </div>
              
              <span className="text-sm font-medium text-gray-700">
                {message.sender === 'user' ? 'You' : 'Hospital Assistant'}
                
                {message.agentType && message.sender === 'agent' && (
                  <span className="ml-2 text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md font-normal">
                    {message.agentType}
                  </span>
                )}
              </span>
            </div>
            
            {/* Message bubble */}
            <div className={`px-5 py-4 rounded-2xl shadow-sm ${
              message.sender === 'user' 
                ? 'bg-blue-500 text-white' 
                : 'bg-white border border-slate-200 text-gray-800'
            }`}>              
              <p className="whitespace-pre-wrap">{message.text}</p>
              
              <div className={`text-right text-xs mt-2 ${
                message.sender === 'user' ? 'text-blue-200' : 'text-gray-400'
              }`}>
                {formatTime(message.timestamp)}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default ChatTranscript;