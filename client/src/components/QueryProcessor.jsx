import React, { useState, useEffect } from 'react';

const QueryProcessor = () => {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [queryStatus, setQueryStatus] = useState('inactive');
  const [currentAgent, setCurrentAgent] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const res = await fetch('http://localhost:8000/process-query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query,
          currentAgent,
          queryStatus
        }),
      });
      
      if (!res.ok) throw new Error('Server error');
      const data = await res.json();
      
      setResponse(data.response || '');
      setQueryStatus(data.status);
      setCurrentAgent(data.agent);
      
      // If the query is resolved, reset the state for the next query
      if (data.status === 'resolved') {
        setQuery('');
        setCurrentAgent(null);
        setQueryStatus('inactive');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 500, margin: '2rem auto', padding: 24, border: '1px solid #eee', borderRadius: 8, background: '#fafbfc' }}>
      <h2>Query Processor</h2>
      <div style={{ marginBottom: 12 }}>
        {queryStatus === 'active' && (
          <div style={{ color: '#0066cc', marginBottom: 8 }}>
            Currently processing with {currentAgent} agent. Please provide any additional information or type 'done' to finish.
          </div>
        )}
      </div>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Enter your query..."
          required
          style={{ padding: 8, fontSize: 16 }}
        />
        <button type="submit" disabled={loading} style={{ padding: 8, fontSize: 16 }}>
          {loading ? 'Processing...' : 'Submit'}
        </button>
      </form>
      {error && <div style={{ color: 'red', marginTop: 12 }}>{error}</div>}
      {response && <div style={{ marginTop: 12, whiteSpace: 'pre-wrap', background: '#f4f4f4', padding: 12, borderRadius: 4 }}>{response}</div>}
    </div>
  );
};

export default QueryProcessor;
