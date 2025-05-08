import React from 'react';

const LiveSessionsTab = ({ sessions, formatDuration }) => {
  return (
    <div className="space-y-6 w-full">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-medium text-gray-800">Active Sessions ({sessions.filter(s => s.status === 'active').length})</h2>
        <div className="flex gap-2">
          <button className="bg-white text-gray-600 border border-gray-300 rounded px-3 py-1 text-sm hover:bg-gray-50">
            Refresh
          </button>
          <button className="bg-blue-50 text-blue-700 border border-blue-200 rounded px-3 py-1 text-sm hover:bg-blue-100">
            Export Data
          </button>
        </div>
      </div>
      
      {/* Session cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {sessions.map(session => (
          <div 
            key={session.id} 
            className={`bg-white rounded-lg shadow p-4 border-l-4 ${
              session.status === 'active' ? 'border-green-500' : 
              session.status === 'idle' ? 'border-yellow-500' : 'border-red-500'
            }`}
          >
            <div className="flex justify-between items-start mb-2">
              <div>
                <h3 className="font-medium text-gray-800">Session {session.id}</h3>
                <p className="text-sm text-gray-600">Patient ID: {session.patientId}</p>
              </div>
              <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                session.status === 'active' ? 'bg-green-100 text-green-800' : 
                session.status === 'idle' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
              }`}>
                {session.status.charAt(0).toUpperCase() + session.status.slice(1)}
              </span>
            </div>
            
            <div className="grid grid-cols-2 gap-2 text-sm mb-3">
              <div>
                <p className="text-gray-500">Started</p>
                <p className="font-medium">{session.startTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
              </div>
              <div>
                <p className="text-gray-500">Duration</p>
                <p className="font-medium">{formatDuration(session.startTime)}</p>
              </div>
              <div>
                <p className="text-gray-500">Agent</p>
                <p className="font-medium">{session.agent}</p>
              </div>
              <div>
                <p className="text-gray-500">Queries</p>
                <p className="font-medium">{session.queries}</p>
              </div>
            </div>
            
            <div className="flex justify-between text-xs text-gray-500 border-t border-gray-100 pt-2">
              <p>Avg response: {(session.responseTimes.reduce((a, b) => a + b, 0) / session.responseTimes.length).toFixed(1)}s</p>
              <button className="text-blue-600 hover:text-blue-800">View details</button>
            </div>
          </div>
        ))}
      </div>
      
      {/* Summary statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500">Total Active Sessions</p>
          <p className="text-2xl font-semibold text-gray-800">{sessions.filter(s => s.status === 'active').length}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500">Avg Session Duration</p>
          <p className="text-2xl font-semibold text-gray-800">14m 23s</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500">Most Active Agent</p>
          <p className="text-2xl font-semibold text-gray-800">RAG</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500">Escalation Rate</p>
          <p className="text-2xl font-semibold text-gray-800">12%</p>
        </div>
      </div>
    </div>
  );
};

export default LiveSessionsTab;