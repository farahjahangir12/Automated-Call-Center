import { useState, useEffect } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend, ArcElement } from 'chart.js';
import LiveSessionsTab from './LiveSessionTab';
import AgentPerformanceTab from './AgentPerformanceTab';
import SystemLogsTab from './SystemLogsTab';
import SystemSettingsTab from './SystemSettingsTab';

// Register ChartJS components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend, ArcElement);

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('liveSessions');
  const [sessions, setSessions] = useState([]);
  const [agentPerformance, setAgentPerformance] = useState({});
  const [logs, setLogs] = useState([]);
  const [settings, setSettings] = useState({
    hospitalPolicies: {
      escalationThreshold: 60, // seconds
      maxSessionTime: 30, // minutes
      operatingHours: '8:00 AM - 8:00 PM',
      emergencyRedirect: 'Emergency Services (555-123-4567)',
      recordingConsent: true,
    },
    agentSettings: {
      RAG: { enabled: true, responseTime: 3 },
      GraphRAG: { enabled: true, responseTime: 4 },
      SQL: { enabled: true, responseTime: 2 },
      General: { enabled: true, responseTime: 1 },
    }
  });

  // Generate dummy data on component mount
  useEffect(() => {
    generateDummyData();
  }, []);

  const generateDummyData = () => {
    // Generate 5 dummy live sessions
    const dummySessions = [
      { id: 'sess_1', patientId: 'P12345', startTime: new Date(Date.now() - 1000 * 60 * 5), agent: 'RAG', status: 'active', queries: 3, responseTimes: [2.4, 3.1, 1.9] },
      { id: 'sess_2', patientId: 'P67890', startTime: new Date(Date.now() - 1000 * 60 * 12), agent: 'GraphRAG', status: 'active', queries: 8, responseTimes: [3.5, 4.2, 3.8, 4.0, 3.7, 4.1, 3.9, 4.3] },
      { id: 'sess_3', patientId: 'P24680', startTime: new Date(Date.now() - 1000 * 60 * 3), agent: 'SQL', status: 'active', queries: 2, responseTimes: [1.8, 2.2] },
      { id: 'sess_4', patientId: 'P13579', startTime: new Date(Date.now() - 1000 * 60 * 18), agent: 'General', status: 'idle', queries: 5, responseTimes: [1.1, 0.9, 1.3, 1.0, 1.2] },
      { id: 'sess_5', patientId: 'P97531', startTime: new Date(Date.now() - 1000 * 60 * 27), agent: 'RAG', status: 'escalated', queries: 7, responseTimes: [2.8, 3.2, 3.5, 2.9, 4.5, 5.2, 6.7] },
    ];
    setSessions(dummySessions);

    // Generate agent performance data
    const dummyPerformance = {
      labels: ['RAG', 'GraphRAG', 'SQL', 'General'],
      responseTime: {
        average: [3.1, 4.0, 2.0, 1.1],
        data: {
          labels: ['Last 24 Hours'],
          datasets: [
            {
              label: 'Average Response Time (seconds)',
              data: [3.1, 4.0, 2.0, 1.1],
              backgroundColor: ['rgba(54, 162, 235, 0.6)', 'rgba(153, 102, 255, 0.6)', 'rgba(75, 192, 192, 0.6)', 'rgba(255, 159, 64, 0.6)'],
            }
          ]
        }
      },
      load: {
        data: {
          labels: ['8 AM', '10 AM', '12 PM', '2 PM', '4 PM', '6 PM', '8 PM'],
          datasets: [
            {
              label: 'RAG',
              data: [12, 19, 25, 31, 28, 22, 14],
              borderColor: 'rgba(54, 162, 235, 1)',
              backgroundColor: 'rgba(54, 162, 235, 0.2)',
              tension: 0.4,
            },
            {
              label: 'GraphRAG',
              data: [8, 15, 29, 18, 22, 16, 7],
              borderColor: 'rgba(153, 102, 255, 1)',
              backgroundColor: 'rgba(153, 102, 255, 0.2)',
              tension: 0.4,
            },
            {
              label: 'SQL',
              data: [5, 12, 18, 23, 19, 15, 8],
              borderColor: 'rgba(75, 192, 192, 1)',
              backgroundColor: 'rgba(75, 192, 192, 0.2)',
              tension: 0.4,
            },
            {
              label: 'General',
              data: [15, 23, 35, 42, 38, 27, 18],
              borderColor: 'rgba(255, 159, 64, 1)',
              backgroundColor: 'rgba(255, 159, 64, 0.2)',
              tension: 0.4,
            }
          ]
        }
      },
      escalation: {
        counts: [5, 12, 3, 8],
        data: {
          labels: ['RAG', 'GraphRAG', 'SQL', 'General'],
          datasets: [
            {
              label: 'Escalation Count (Last 7 Days)',
              data: [5, 12, 3, 8],
              backgroundColor: [
                'rgba(54, 162, 235, 0.6)',
                'rgba(153, 102, 255, 0.6)',
                'rgba(75, 192, 192, 0.6)',
                'rgba(255, 159, 64, 0.6)',
              ],
              borderColor: [
                'rgba(54, 162, 235, 1)',
                'rgba(153, 102, 255, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(255, 159, 64, 1)',
              ],
              borderWidth: 1,
            },
          ],
        }
      },
      distribution: {
        data: {
          labels: ['RAG', 'GraphRAG', 'SQL', 'General'],
          datasets: [
            {
              data: [35, 25, 15, 25],
              backgroundColor: [
                'rgba(54, 162, 235, 0.6)',
                'rgba(153, 102, 255, 0.6)',
                'rgba(75, 192, 192, 0.6)',
                'rgba(255, 159, 64, 0.6)',
              ],
              borderColor: [
                'rgba(54, 162, 235, 1)',
                'rgba(153, 102, 255, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(255, 159, 64, 1)',
              ],
            },
          ],
        }
      }
    };
    setAgentPerformance(dummyPerformance);

    // Generate system logs
    const dummyLogs = [
      { id: 'log_1', timestamp: new Date(Date.now() - 1000 * 60 * 2), level: 'INFO', message: 'Patient P12345 session started', service: 'SessionManager' },
      { id: 'log_2', timestamp: new Date(Date.now() - 1000 * 60 * 5), level: 'WARNING', message: 'High response time detected for GraphRAG agent', service: 'PerformanceMonitor' },
      { id: 'log_3', timestamp: new Date(Date.now() - 1000 * 60 * 8), level: 'INFO', message: 'Agent switch: General → RAG for session sess_1', service: 'RouterService' },
      { id: 'log_4', timestamp: new Date(Date.now() - 1000 * 60 * 15), level: 'ERROR', message: 'Failed to connect to medical records database', service: 'SQLAgent' },
      { id: 'log_5', timestamp: new Date(Date.now() - 1000 * 60 * 22), level: 'INFO', message: 'System backup completed successfully', service: 'MaintenanceService' },
      { id: 'log_6', timestamp: new Date(Date.now() - 1000 * 60 * 35), level: 'WARNING', message: 'Session sess_5 approaching maximum duration', service: 'SessionManager' },
      { id: 'log_7', timestamp: new Date(Date.now() - 1000 * 60 * 45), level: 'INFO', message: 'Daily analytics report generated', service: 'ReportGenerator' },
      { id: 'log_8', timestamp: new Date(Date.now() - 1000 * 60 * 55), level: 'ERROR', message: 'Knowledge base synchronization failed', service: 'RAGAgent' },
      { id: 'log_9', timestamp: new Date(Date.now() - 1000 * 60 * 67), level: 'INFO', message: 'Agent settings updated by administrator', service: 'AdminPanel' },
      { id: 'log_10', timestamp: new Date(Date.now() - 1000 * 60 * 85), level: 'INFO', message: 'System started successfully', service: 'SystemBootstrap' },
    ];
    setLogs(dummyLogs);
  };

  // Helper function to format time duration
  const formatDuration = (startTime) => {
    const durationMs = Date.now() - new Date(startTime).getTime();
    const minutes = Math.floor(durationMs / (1000 * 60));
    const seconds = Math.floor((durationMs % (1000 * 60)) / 1000);
    return `${minutes}m ${seconds}s`;
  };

  // Helper function to format timestamp
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  // Handle settings change
  const handleSettingChange = (category, setting, value) => {
    setSettings(prevSettings => ({
      ...prevSettings,
      [category]: {
        ...prevSettings[category],
        [setting]: value
      }
    }));
  };

  // Handle agent setting change
  const handleAgentSettingChange = (agent, setting, value) => {
    setSettings(prevSettings => ({
      ...prevSettings,
      agentSettings: {
        ...prevSettings.agentSettings,
        [agent]: {
          ...prevSettings.agentSettings[agent],
          [setting]: value
        }
      }
    }));
  };

  // Render appropriate tab content
  const renderTabContent = () => {
    switch (activeTab) {
      case 'liveSessions':
        return <LiveSessionsTab 
          sessions={sessions} 
          formatDuration={formatDuration} 
        />;
      case 'agentPerformance':
        return <AgentPerformanceTab 
          agentPerformance={agentPerformance} 
        />;
      case 'logs':
        return <SystemLogsTab 
          logs={logs} 
          formatTimestamp={formatTimestamp} 
        />;
      case 'settings':
        return <SystemSettingsTab 
          settings={settings} 
          handleSettingChange={handleSettingChange} 
          handleAgentSettingChange={handleAgentSettingChange} 
        />;
      default:
        return <LiveSessionsTab 
          sessions={sessions} 
          formatDuration={formatDuration} 
        />;
    }
  };

  return (
    <div className="grid grid-rows-2 h-full gap-2">
      {/* Dashboard header */}
      <div className="bg-white px-6 py-4 border-b border-gray-200 w-full grid grid-cols-1">
        <h1 className="text-2xl font-bold text-gray-800">Admin Dashboard</h1>
        <p className="text-sm text-gray-500">Monitor system performance and manage settings</p>
      </div>

      {/* Tab navigation */}
      <div className="bg-white border-b border-gray-200 w-full">
        <nav className="flex overflow-x-auto">
          <button
            onClick={() => setActiveTab('liveSessions')}
            className={`px-4 py-3 text-sm font-medium whitespace-nowrap ${
              activeTab === 'liveSessions'
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
            }`}
          >
            Live Sessions
          </button>
          <button
            onClick={() => setActiveTab('agentPerformance')}
            className={`px-4 py-3 text-sm font-medium whitespace-nowrap ${
              activeTab === 'agentPerformance'
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
            }`}
          >
            Agent Performance
          </button>
          <button
            onClick={() => setActiveTab('logs')}
            className={`px-4 py-3 text-sm font-medium whitespace-nowrap ${
              activeTab === 'logs'
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
            }`}
          >
            System Logs
          </button>
          <button
            onClick={() => setActiveTab('settings')}
            className={`px-4 py-3 text-sm font-medium whitespace-nowrap ${
              activeTab === 'settings'
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
            }`}
          >
            Settings
          </button>
        </nav>
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-auto p-6 bg-gray-50 w-full">
        {renderTabContent()}
      </div>
    </div>
  );
};

export default Dashboard;