import React from 'react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';

const AgentPerformanceTab = ({ agentPerformance }) => {
  return (
    <div className="space-y-6 w-full">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-medium text-gray-800">Agent Performance Metrics</h2>
        <div>
          <select className="bg-white border border-gray-300 rounded px-3 py-1 text-sm">
            <option>Last 24 Hours</option>
            <option>Last 7 Days</option>
            <option>Last 30 Days</option>
          </select>
        </div>
      </div>
      
      {/* Charts grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent load chart */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-sm font-medium text-gray-800 mb-4">Agent Load Over Time</h3>
          <div className="h-64">
            <Line 
              data={agentPerformance.load?.data} 
              options={{ 
                maintainAspectRatio: false,
                plugins: {
                  legend: { position: 'bottom' }
                },
                scales: {
                  y: {
                    title: {
                      display: true,
                      text: 'Number of Sessions'
                    }
                  }
                }
              }} 
            />
          </div>
        </div>
        
        {/* Response time chart */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-sm font-medium text-gray-800 mb-4">Average Response Time (seconds)</h3>
          <div className="h-64">
            <Bar 
              data={agentPerformance.responseTime?.data}
              options={{ 
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                  legend: { display: false }
                }
              }}
            />
          </div>
        </div>
        
        {/* Escalation count chart */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-sm font-medium text-gray-800 mb-4">Escalation Count by Agent</h3>
          <div className="h-64">
            <Bar 
              data={agentPerformance.escalation?.data}
              options={{ 
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: false }
                },
                scales: {
                  y: {
                    title: {
                      display: true,
                      text: 'Number of Escalations'
                    }
                  }
                }
              }}
            />
          </div>
        </div>
        
        {/* Agent distribution chart */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-sm font-medium text-gray-800 mb-4">Agent Usage Distribution</h3>
          <div className="h-64 flex items-center justify-center">
            <div className="w-3/4 h-full">
              <Doughnut 
                data={agentPerformance.distribution?.data}
                options={{ 
                  maintainAspectRatio: false,
                  plugins: {
                    legend: { position: 'right' }
                  }
                }}
              />
            </div>
          </div>
        </div>
      </div>
      
      {/* Performance metrics table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <h3 className="text-sm font-medium text-gray-800 p-4 bg-gray-50 border-b border-gray-200">Detailed Agent Metrics</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Agent Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Response Time</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Success Rate</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Queries Handled</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Escalation Rate</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">RAG</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">3.1s</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">87%</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">352</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">8%</td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">GraphRAG</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">4.0s</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">82%</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">285</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">15%</td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">SQL</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">2.0s</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">95%</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">143</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">3%</td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">General</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">1.1s</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">90%</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">423</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">7%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AgentPerformanceTab;