import { useState } from 'react';
import CallSimulation from './components/CallSimulation';
import ChatTranscript from './components/ChatTranscript';
import AgentCard from './components/AgentCard';
import Dashboard from './components/Dashboard';
import KnowledgeBase from './components/KnowledgeBase';

const Layout = () => {
  const [transcript, setTranscript] = useState([]);
  const [activeAgent, setActiveAgent] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [activePage, setActivePage] = useState('assistant');

  const handleNewMessage = (message) => {
    setTranscript(prev => [...prev, message]);
  };

  const handleAgentChange = (agent) => {
    setActiveAgent(agent);
  };

  // Navigation items for the sidebar
  const navItems = [
    { id: 'assistant', icon: 'M9 6a3 3 0 11-6 0 3 3 0 016 0zM6.5 9a2.5 2.5 0 100-5 2.5 2.5 0 000 5z M18 7.5v3c0 .818-.393 1.544-1 2v2a2 2 0 01-2 2h-2.035a4.001 4.001 0 01-7.93 0H3a2 2 0 01-2-2v-2a2.497 2.497 0 01-1-2v-3a2.5 2.5 0 012.5-2.5h1V3a1 1 0 011-1h2a1 1 0 011 1v2h5V3a1 1 0 011-1h2a1 1 0 011 1v2h1A2.5 2.5 0 0118 7.5z', label: 'Assistant' },
    { id: 'dashboard', icon: 'M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z', label: 'Dashboard' },
    { id: 'appointments', icon: 'M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z', label: 'Appointments' },
    { id: 'records', icon: 'M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z', label: 'Records' },
    { id: 'results', icon: 'M9 2a1 1 0 000 2h2a1 1 0 100-2H9z M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z', label: 'Test Results' },
    { id: 'knowledge', icon: 'M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804V12a1 1 0 11-2 0V4.804z', label: 'Knowledge Base' },
  ];

  // Render the appropriate page content based on activePage
  const renderPageContent = () => {
    switch (activePage) {
      case 'dashboard':
        return (
        
            <Dashboard />
          
        );
        case 'knowledge':
          return (
              <KnowledgeBase />
          
          );
      case 'assistant':
      default:
        return (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 w-full">
            {/* Left panel */}
            <div className="flex flex-col gap-6">
              <div className="bg-white rounded-xl shadow-md overflow-hidden border border-gray-200 flex-1">
                <div className="bg-slate-50 px-5 py-4 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                      </svg>
                      <h2 className="font-semibold text-gray-800">Voice Interaction</h2>
                    </div>
                    
                    <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full font-medium">
                      Secure Connection
                    </span>
                  </div>
                </div>
                
                <div className="p-5">
                  <CallSimulation 
                    isRecording={isRecording} 
                    setIsRecording={setIsRecording}
                    onNewMessage={handleNewMessage}
                    onAgentChange={handleAgentChange}
                  />
                </div>
              </div>
              
              {activeAgent && (
                <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden mb-4">
                  <div className="px-5 py-3 bg-slate-50 border-b border-gray-200">
                    <div className="flex items-center gap-2">
                      <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                      <h2 className="font-semibold text-gray-800">Active System</h2>
                    </div>
                  </div>
                  <div className="p-5">
                    <AgentCard agent={activeAgent} />
                  </div>
                </div>
              )}
            </div>
            
            {/* Right panel: Conversation */}
            <div className="bg-white rounded-xl shadow-md overflow-hidden border border-gray-200 flex flex-col h-full">
              <ChatTranscript messages={transcript} />
            </div>
          </div>
        );
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left sidebar navigation */}
      <aside className="w-20 lg:w-64 bg-white border-r border-gray-200 flex flex-col">
        {/* Hospital logo area */}
        <div className="h-16 flex items-center justify-center lg:justify-start px-3 border-b border-gray-200">
          <div className="bg-blue-600 text-white p-2 rounded-lg flex-shrink-0">
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10.5 2.75a.75.75 0 00-1.5 0v4h-4a.75.75 0 000 1.5h4v4a.75.75 0 001.5 0v-4h4a.75.75 0 000-1.5h-4v-4z" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-gray-800 ml-3 hidden lg:block">Hospital Hub</h2>
        </div>
        
        {/* Navigation items */}
        <nav className="flex-1 pt-5 pb-4">
          <div className="px-3">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3 hidden lg:block">
              Main Menu
            </p>
            <ul className="space-y-2">
              {navItems.map((item) => (
                <li key={item.id}>
                  <button 
                    onClick={() => setActivePage(item.id)}
                    className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg w-full transition-colors ${
                      activePage === item.id 
                        ? 'bg-blue-50 text-blue-700' 
                        : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    <svg className={`w-6 h-6 ${activePage === item.id ? 'text-blue-500' : 'text-gray-500'}`} fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d={item.icon} clipRule="evenodd" />
                    </svg>
                    <span className="ml-3 hidden lg:block">{item.label}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </nav>
        
        {/* User/settings section */}
        <div className="border-t border-gray-200 p-4">
          <div className="flex items-center">
            <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-700">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-6-3a2 2 0 11-4 0 2 2 0 014 0zm-2 4a5 5 0 00-4.546 2.916A5.986 5.986 0 0010 16a5.986 5.986 0 004.546-2.084A5 5 0 0010 11z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3 hidden lg:block">
              <p className="text-sm font-medium text-gray-700">Medical Staff</p>
              <p className="text-xs text-gray-500">View profile</p>
            </div>
          </div>
        </div>
      </aside>
      
      {/* Main content area */}
      <div className="flex-1 flex flex-col overflow-hidden w-full">
        {/* Header with hospital branding */}
        <header className="bg-white border-b border-gray-200 shadow-sm">
          <div className="px-6 py-3">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-xl font-semibold text-gray-800">
                  Hospital Assistant Hub
                </h1>
                <p className="text-xs text-gray-500">
                  AI-Powered Call Center
                </p>
              </div>
              
              <div className="flex items-center gap-3">
                <div className={`px-3 py-1.5 rounded-full text-sm flex items-center gap-2 ${
                  isRecording ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-700'
                }`}>
                  <span className={`w-2 h-2 rounded-full ${
                    isRecording ? 'bg-red-500 animate-pulse' : 'bg-green-500'
                  }`}></span>
                  <span className="font-medium">
                    {isRecording ? 'Recording Active' : 'System Ready'}
                  </span>
                </div>
                
                <div className="bg-slate-800 text-white text-xs px-3 py-2 rounded-full font-medium">
                  Healthcare AI v1.3
                </div>
              </div>
            </div>
          </div>
        </header>
        
        {/* Main content */}
        <main className="flex-1 overflow-auto w-full">
          {activePage === 'dashboard' ? (
            // No padding for dashboard for full width
            <div className="w-full">
              {renderPageContent()}
            </div>
          ) : (
            // Keep padding for other pages
            <div className="px-6 py-8">
              {renderPageContent()}
            </div>
          )}
        </main>
        
        {/* Footer */}
        <footer className="bg-white border-t border-gray-200">
          <div className="px-6 py-3">
            <div className="flex justify-between items-center">
              <p className="text-sm text-gray-600">
                © 2025 Hospital Multi-Agent AI System
              </p>
              
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <span className="px-2 py-1 bg-slate-100 rounded-full">HIPAA Compliant</span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default Layout;