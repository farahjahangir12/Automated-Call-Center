import { useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client - replace with your actual env variables
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || process.env.REACT_APP_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY || process.env.REACT_APP_SUPABASE_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

const KnowledgeBase = () => {
  const [activeAgent, setActiveAgent] = useState(null);
  const [collections, setCollections] = useState({});
  const [sqlTables, setSqlTables] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Collection details from main.py
  const collectionConfig = {
    "Department_Details": {
      "chunk_size": 500,
      "service": "department",
      "fallback": "Department information is available at the information desk."
    },
    "General_Consulting": {
      "chunk_size": 300,
      "service": "outpatient",
      "fallback": "General consulting hours are 9AM-5PM weekdays."
    },
    "Patient_Safety_Policy": {
      "chunk_size": 500,
      "service": "patient care",
      "fallback": "Patient safety is our top priority. Please ask staff for specific policies."
    },
    "Outpatients_Policies": {
      "chunk_size": 400,
      "service": "outpatient",
      "fallback": "Standard outpatient visiting hours are 9AM-5PM."
    },
    "Admission_Discharge": {
      "chunk_size": 350,
      "service": "hospital_admission",
      "fallback": "Admission requires ID and insurance information. Please contact the admissions desk for assistance."
    },
    "Principles_Policies": {
      "chunk_size": 300,
      "service": "principles",
      "fallback": "Our hospital follows international healthcare principles."
    }
  };

  // Fetch collection statistics when RAG agent is selected
  useEffect(() => {
    if (activeAgent === 'RAG') {
      fetchCollectionStats();
    } else if (activeAgent === 'SQL') {
      fetchTableStats();
    }
  }, [activeAgent]);

  // Fetch vector counts for each collection from Supabase
  const fetchCollectionStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const collectionStats = {};
      
      // For each collection in our config, query the document count
      for (const [collection, config] of Object.entries(collectionConfig)) {
        const { data, error, count } = await supabase
          .from('hospital_documents')
          .select('*', { count: 'exact' })
          .contains('metadata', { service: config.service });
          
        if (error) throw error;
        
        collectionStats[collection] = {
          ...config,
          documentCount: count || 0,
          // Calculate approximate vector count based on chunk size
          vectorCount: Math.ceil((count || 0) * (500 / config.chunk_size)),
          service: config.service
        };
      }
      
      setCollections(collectionStats);
    } catch (err) {
      console.error('Error fetching collection stats:', err);
      setError('Failed to load knowledge base collections. Please try again later.');
      
      // Set dummy data for display when connection fails
      setCollections(Object.entries(collectionConfig).reduce((acc, [key, value]) => {
        acc[key] = { 
          ...value,
          documentCount: Math.floor(Math.random() * 100) + 20,
          vectorCount: Math.floor(Math.random() * 500) + 100
        };
        return acc;
      }, {}));
    } finally {
      setLoading(false);
    }
  };

  // For fetching SQL table information using the RPC function
  const fetchTableStats = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Call the RPC function to get table counts and last updated timestamps
      const { data, error } = await supabase.rpc('get_table_counts_with_last_updated');
      
      if (error) throw error;
      
      // Skip the hospital_documents table as it's used by the RAG system
      const filteredTables = data.filter(table => table.table_name !== 'hospital_documents');
      
      // Add data type information to each table (this would typically come from schema)
      const dataTypeMapping = {
        'patients': 'patient_id, name, dob, contact_info',
        'appointments': 'appointment_id, doctor_id, patient_id, datetime',
        'doctors': 'doctor_id, name, specialty, department',
        'medications': 'med_id, name, dosage, manufacturer',
        'billing': 'invoice_id, patient_id, amount, status',
        'insurance': 'policy_id, patient_id, provider, coverage',
        'departments': 'dept_id, name, location, head_doctor_id',
        'staff': 'staff_id, name, role, contact_info',
        'inventory': 'item_id, name, quantity, category',
        'patient_records': 'record_id, patient_id, visit_date, diagnosis'
      };
      
      // Add data type info and format timestamps
      const enhancedTableData = filteredTables.map(table => {
        // Format the timestamp or provide a default
        let updateStatus = 'Unknown';
        if (table.last_updated) {
          const lastUpdate = new Date(table.last_updated);
          const now = new Date();
          const diffHours = (now - lastUpdate) / (1000 * 60 * 60);
          
          if (diffHours < 1) updateStatus = 'Live';
          else if (diffHours < 24) updateStatus = 'Hourly';
          else if (diffHours < 168) updateStatus = 'Daily';
          else updateStatus = 'Weekly';
        }
        
        return {
          ...table,
          dataTypes: dataTypeMapping[table.table_name] || 'Various fields',
          updateStatus
        };
      });
      
      setSqlTables(enhancedTableData);
    } catch (err) {
      console.error('Error fetching SQL table stats:', err);
      setError('Failed to load database tables. Please try again later.');
      
      // Set dummy data for SQL tables as fallback
      setSqlTables([
        { table_name: 'patients', row_count: 5280, dataTypes: 'patient_id, name, dob, contact_info', updateStatus: 'Live' },
        { table_name: 'appointments', row_count: 8463, dataTypes: 'appointment_id, doctor_id, patient_id, datetime', updateStatus: 'Live' },
        { table_name: 'doctors', row_count: 142, dataTypes: 'doctor_id, name, specialty, department', updateStatus: 'Daily' },
        { table_name: 'medications', row_count: 1892, dataTypes: 'med_id, name, dosage, manufacturer', updateStatus: 'Weekly' },
        { table_name: 'billing', row_count: 12653, dataTypes: 'invoice_id, patient_id, amount, status', updateStatus: 'Hourly' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Agent cards configuration
  const agents = [
    { 
      id: 'RAG', 
      name: 'Retrieval Augmented Generation',
      description: 'Uses vector embeddings to retrieve relevant documents from the hospital knowledge base.',
      icon: '📑',
      color: 'bg-blue-100 border-blue-300 text-blue-800'
    },
    { 
      id: 'GraphRAG', 
      name: 'Graph-based RAG',
      description: 'Enhances RAG with knowledge graphs to improve contextual understanding and relationships.',
      icon: '🔄',
      color: 'bg-purple-100 border-purple-300 text-purple-800'
    },
    { 
      id: 'SQL', 
      name: 'SQL Database Agent',
      description: 'Directly queries structured hospital databases for precise information retrieval.',
      icon: '💾',
      color: 'bg-green-100 border-green-300 text-green-800'
    }
  ];

  return (
    <div className="flex flex-col h-full w-full">
      <div className="bg-white px-6 py-4 border-b border-gray-200 w-full">
        <h1 className="text-2xl font-bold text-gray-800">Knowledge Base</h1>
        <p className="text-sm text-gray-500">Explore the hospital's AI knowledge infrastructure</p>
      </div>

      <div className="flex-1 overflow-auto p-6 bg-gray-50 w-full">
        {/* Agent cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {agents.map(agent => (
            <div 
              key={agent.id}
              onClick={() => setActiveAgent(agent.id)}
              className={`cursor-pointer p-6 rounded-lg border-2 transition-all ${
                activeAgent === agent.id 
                  ? `${agent.color} border-2` 
                  : 'bg-white border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="text-3xl mb-3">{agent.icon}</div>
                {activeAgent === agent.id && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    Active
                  </span>
                )}
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-1">{agent.name}</h3>
              <p className="text-sm text-gray-500">{agent.description}</p>
            </div>
          ))}
        </div>

        {/* Collection details section - shown when RAG is selected */}
        {activeAgent === 'RAG' && (
          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">RAG Collections</h2>
              <button 
                onClick={fetchCollectionStats}
                className="flex items-center px-3 py-1.5 bg-blue-50 text-blue-600 rounded border border-blue-200 text-sm hover:bg-blue-100"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Refreshing...
                  </>
                ) : "Refresh Data"}
              </button>
            </div>

            {error && (
              <div className="bg-red-50 text-red-700 p-4 rounded-md mb-4">
                {error}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {Object.entries(collections).map(([name, details]) => (
                <div key={name} className="bg-white rounded-lg shadow p-5 border-l-4 border-blue-500">
                  <h3 className="text-lg font-medium text-gray-800 mb-2">
                    {name.replace(/_/g, ' ')}
                  </h3>
                  
                  <div className="grid grid-cols-2 gap-2 text-sm mb-4">
                    <div>
                      <p className="text-gray-500">Service</p>
                      <p className="font-medium capitalize">{details.service}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Chunk Size</p>
                      <p className="font-medium">{details.chunk_size} tokens</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Documents</p>
                      <p className="font-medium">{details.documentCount}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Vector Count</p>
                      <p className="font-medium">{details.vectorCount}</p>
                    </div>
                  </div>
                  
                  <div className="mt-3 pt-3 border-t border-gray-100">
                    <p className="text-xs text-gray-500">Fallback Response:</p>
                    <p className="text-sm">{details.fallback}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeAgent === 'GraphRAG' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Graph-based RAG</h2>
            <p className="text-gray-600 mb-6">
              GraphRAG enhances traditional RAG by organizing knowledge in a graph structure, capturing relationships between medical concepts, departments, and procedures.
            </p>
            
            <div className="border rounded-lg p-5 bg-purple-50 mb-6">
              <h3 className="text-lg font-medium mb-2">Graph Knowledge Structure</h3>
              <div className="mb-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="w-3 h-3 rounded-full bg-purple-500"></span>
                  <span className="font-medium">Nodes</span>
                  <span className="text-gray-500 text-sm">Entities like departments, doctors, procedures</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-6 h-0.5 bg-purple-500"></span>
                  <span className="font-medium">Edges</span>
                  <span className="text-gray-500 text-sm">Relationships like "treats", "located in", "requires"</span>
                </div>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="border rounded-lg p-4">
                <h4 className="font-medium mb-2">Connected Entities</h4>
                <p className="text-4xl font-bold text-purple-600">1,453</p>
              </div>
              <div className="border rounded-lg p-4">
                <h4 className="font-medium mb-2">Relationships</h4>
                <p className="text-4xl font-bold text-purple-600">3,892</p>
              </div>
              <div className="border rounded-lg p-4">
                <h4 className="font-medium mb-2">Knowledge Domains</h4>
                <p className="text-4xl font-bold text-purple-600">12</p>
              </div>
            </div>
          </div>
        )}

        {activeAgent === 'SQL' && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">SQL Database Tables</h2>
              <button 
                onClick={fetchTableStats}
                className="flex items-center px-3 py-1.5 bg-green-50 text-green-600 rounded border border-green-200 text-sm hover:bg-green-100"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-green-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Refreshing...
                  </>
                ) : "Refresh Data"}
              </button>
            </div>

            <p className="text-gray-600 mb-6">
              The SQL agent provides precise answers by executing structured database queries against hospital information systems.
            </p>
            
            {error && (
              <div className="bg-red-50 text-red-700 p-4 rounded-md mb-4">
                {error}
              </div>
            )}
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Table Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Record Count</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data Fields</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Update Frequency</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {sqlTables.map((table, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {table.table_name ? table.table_name.replace(/_/g, ' ') : 'Unknown Table'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {typeof table.row_count === 'number' ? table.row_count.toLocaleString() : '0'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {table.dataTypes}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {table.updateStatus}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {sqlTables.length === 0 && !loading && (
              <div className="text-center py-10 text-gray-500">
                No tables found or connection to database failed.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default KnowledgeBase;