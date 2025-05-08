const AgentCard = ({ agent }) => {
  // Agent type configuration with colors and medical descriptions
  const agentConfig = {
    RAG: {
      color: 'bg-emerald-100 text-emerald-800 border-emerald-200',
      icon: '📚',
      title: 'Medical Knowledge Base',
      description: 'Provides information from hospital protocols, medical references, and treatment guidelines'
    },
    SQL: {
      color: 'bg-blue-100 text-blue-800 border-blue-200',
      icon: '🗃️',
      title: 'Hospital Records System',
      description: 'Securely accesses patient records, appointments, and hospital resource information'
    },
    GraphRAG: {
      color: 'bg-violet-100 text-violet-800 border-violet-200',
      icon: '🔗',
      title: 'Medical Knowledge Graph',
      description: 'Maps relationships between symptoms, conditions, treatments, and hospital departments'
    },
    General: {
      color: 'bg-amber-100 text-amber-800 border-amber-200',
      icon: '🏥',
      title: 'General Hospital Assistant',
      description: 'Provides basic information about hospital services, visiting hours, and policies'
    }
  };
  
  const config = agentConfig[agent] || {
    color: 'bg-slate-100 text-slate-800 border-slate-200',
    icon: '⚕️',
    title: 'Medical AI System',
    description: 'Specialized healthcare assistant'
  };
  
  return (
    <div className="border rounded-xl overflow-hidden shadow-sm transition-all duration-300 hover:shadow-md">
      {/* Agent header */}
      <div className={`${config.color.split(' ')[0]} ${config.color.split(' ')[1]} px-5 py-4`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl bg-white rounded-lg w-10 h-10 flex items-center justify-center shadow-sm">
              {config.icon}
            </span>
            <div>
              <h3 className="font-semibold">{config.title}</h3>
              <div className="text-xs font-medium mt-0.5 flex items-center">
                <span className="bg-white bg-opacity-50 px-2 py-0.5 rounded-full">
                  {agent} Engine
                </span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-1.5 bg-white bg-opacity-60 px-2 py-1 rounded-full text-xs">
            <span className={`inline-block w-2.5 h-2.5 rounded-full ${config.color.split(' ')[0]} animate-pulse`}></span>
            <span className="font-medium">Active</span>
          </div>
        </div>
      </div>
      
      {/* Agent body */}
      <div className="bg-white px-5 py-4">
        <p className="text-gray-600 text-sm leading-relaxed">{config.description}</p>
        
        <div className="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between">
          <div className="text-xs text-gray-500 flex items-center gap-2">
            <svg className="w-4 h-4 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2h-1V9a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <span>AI-powered healthcare assistance</span>
          </div>
          
          <div className="text-xs bg-slate-100 text-slate-700 px-2 py-1 rounded-full">
            {agent === 'RAG' ? 'High Precision' : 
             agent === 'GraphRAG' ? 'High Relation' : 
             agent === 'SQL' ? 'Data Access' : 'General Purpose'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentCard;