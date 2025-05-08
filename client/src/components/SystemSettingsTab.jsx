import React from 'react';

const SystemSettingsTab = ({ settings, handleSettingChange, handleAgentSettingChange }) => {
  return (
    <div className="space-y-6 w-full">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-medium text-gray-800">System Settings</h2>
        <div className="flex gap-2">
          <button className="bg-white text-gray-600 border border-gray-300 rounded px-3 py-1 text-sm hover:bg-gray-50">
            Reset Defaults
          </button>
          <button className="bg-blue-600 text-white rounded px-3 py-1 text-sm hover:bg-blue-700">
            Save Changes
          </button>
        </div>
      </div>
      
      {/* Hospital Policies */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <h3 className="text-sm font-medium text-gray-800 p-4 bg-gray-50 border-b border-gray-200">Hospital Policies</h3>
        <div className="p-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Escalation Threshold (seconds)</label>
              <input 
                type="number" 
                className="w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={settings.hospitalPolicies.escalationThreshold}
                onChange={(e) => handleSettingChange('hospitalPolicies', 'escalationThreshold', parseInt(e.target.value))}
              />
              <p className="mt-1 text-xs text-gray-500">Automatically escalate to human if response time exceeds threshold</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Maximum Session Time (minutes)</label>
              <input 
                type="number" 
                className="w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={settings.hospitalPolicies.maxSessionTime}
                onChange={(e) => handleSettingChange('hospitalPolicies', 'maxSessionTime', parseInt(e.target.value))}
              />
              <p className="mt-1 text-xs text-gray-500">Maximum allowed duration for a single session</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Operating Hours</label>
              <input 
                type="text" 
                className="w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={settings.hospitalPolicies.operatingHours}
                onChange={(e) => handleSettingChange('hospitalPolicies', 'operatingHours', e.target.value)}
              />
              <p className="mt-1 text-xs text-gray-500">Hours when full service is available</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Emergency Redirect</label>
              <input 
                type="text" 
                className="w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={settings.hospitalPolicies.emergencyRedirect}
                onChange={(e) => handleSettingChange('hospitalPolicies', 'emergencyRedirect', e.target.value)}
              />
              <p className="mt-1 text-xs text-gray-500">Where to direct emergency cases</p>
            </div>
          </div>
          <div>
            <div className="flex items-center">
              <input 
                id="recording-consent" 
                type="checkbox" 
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                checked={settings.hospitalPolicies.recordingConsent}
                onChange={(e) => handleSettingChange('hospitalPolicies', 'recordingConsent', e.target.checked)}
              />
              <label htmlFor="recording-consent" className="ml-2 block text-sm text-gray-700">
                Require recording consent
              </label>
            </div>
            <p className="mt-1 text-xs text-gray-500">Ask for consent before recording patient conversations</p>
          </div>
        </div>
      </div>
      
      {/* Agent Settings */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <h3 className="text-sm font-medium text-gray-800 p-4 bg-gray-50 border-b border-gray-200">Agent Settings</h3>
        <div className="p-4">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Agent</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Response Time Limit</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {Object.entries(settings.agentSettings).map(([agent, config]) => (
                <tr key={agent}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center ${
                        agent === 'RAG' ? 'bg-blue-100 text-blue-600' : 
                        agent === 'GraphRAG' ? 'bg-purple-100 text-purple-600' : 
                        agent === 'SQL' ? 'bg-green-100 text-green-600' : 
                        'bg-orange-100 text-orange-600'
                      }`}>
                        {agent.charAt(0)}
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{agent}</div>
                        <div className="text-xs text-gray-500">
                          {agent === 'RAG' ? 'Knowledge Base Retrieval' : 
                           agent === 'GraphRAG' ? 'Knowledge Graph' : 
                           agent === 'SQL' ? 'Database Access' : 'General Assistance'}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <label className="inline-flex relative items-center cursor-pointer">
                        <input 
                          type="checkbox" 
                          className="sr-only peer"
                          checked={config.enabled}
                          onChange={(e) => handleAgentSettingChange(agent, 'enabled', e.target.checked)}
                        />
                        <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-100 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                        <span className="ml-3 text-sm font-medium text-gray-700">
                          {config.enabled ? 'Enabled' : 'Disabled'}
                        </span>
                      </label>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <input 
                        type="number" 
                        className="w-20 border border-gray-300 rounded-md shadow-sm px-2 py-1 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        value={config.responseTime}
                        min="1"
                        max="10"
                        onChange={(e) => handleAgentSettingChange(agent, 'responseTime', parseFloat(e.target.value))}
                      />
                      <span className="ml-2 text-sm text-gray-500">seconds</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default SystemSettingsTab;