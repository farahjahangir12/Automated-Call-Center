import React from 'react';

const SystemLogsTab = ({ logs, formatTimestamp }) => {
  return (
    <div className="space-y-6 w-full">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-medium text-gray-800">System Logs</h2>
        <div className="flex gap-2">
          <select className="bg-white border border-gray-300 rounded px-3 py-1 text-sm">
            <option>All Levels</option>
            <option>INFO</option>
            <option>WARNING</option>
            <option>ERROR</option>
          </select>
          <button className="bg-white text-gray-600 border border-gray-300 rounded px-3 py-1 text-sm hover:bg-gray-50">
            Download Logs
          </button>
        </div>
      </div>
      
      {/* Logs table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Level</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Service</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Message</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {logs.map(log => (
                <tr key={log.id}>
                  <td className="px-4 py-2 whitespace-nowrap text-xs text-gray-500">
                    {formatTimestamp(log.timestamp)}
                  </td>
                  <td className="px-4 py-2 whitespace-nowrap">
                    <span className={`inline-flex text-xs px-2 py-0.5 rounded-full font-medium ${
                      log.level === 'INFO' ? 'bg-blue-100 text-blue-800' : 
                      log.level === 'WARNING' ? 'bg-yellow-100 text-yellow-800' : 
                      'bg-red-100 text-red-800'
                    }`}>
                      {log.level}
                    </span>
                  </td>
                  <td className="px-4 py-2 whitespace-nowrap text-xs font-medium text-gray-900">
                    {log.service}
                  </td>
                  <td className="px-4 py-2 text-xs text-gray-500">
                    {log.message}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="bg-gray-50 px-4 py-3 border-t border-gray-200 flex items-center justify-between">
          <div className="text-sm text-gray-700">
            Showing <span className="font-medium">1</span> to <span className="font-medium">10</span> of <span className="font-medium">156</span> logs
          </div>
          <div className="flex-1 flex justify-end gap-2">
            <button className="relative inline-flex items-center px-2 py-1 border border-gray-300 bg-white text-sm font-medium rounded-md text-gray-500 hover:bg-gray-50">
              Previous
            </button>
            <button className="relative inline-flex items-center px-2 py-1 border border-gray-300 bg-white text-sm font-medium rounded-md text-gray-500 hover:bg-gray-50">
              Next
            </button>
          </div>
        </div>
      </div>
      
      {/* Log stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500">Total Logs (24h)</p>
          <p className="text-2xl font-semibold text-gray-800">156</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500">Warnings</p>
          <p className="text-2xl font-semibold text-yellow-500">23</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500">Errors</p>
          <p className="text-2xl font-semibold text-red-500">8</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500">System Health</p>
          <p className="text-2xl font-semibold text-green-500">Good</p>
        </div>
      </div>
    </div>
  );
};

export default SystemLogsTab;