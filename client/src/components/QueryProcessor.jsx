import React, { useState } from "react";
import axios from "axios";
import "./QueryProcessor.css"; // Import the CSS file for styling

const QueryProcessor = () => {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState(null);
  const [agent, setAgent] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isListening, setIsListening] = useState(false);

  const handleQuerySubmit = async (customQuery) => {
    const finalQuery = customQuery || query;
    if (!finalQuery.trim()) return;

    setIsProcessing(true);
    try {
      // Send the query to the backend router
      const res = await axios.post("http://localhost:5000/process_query", {
        query: finalQuery,
      });

      // Extract the routed agent and response
      setAgent(res.data.agent || "Unknown");
      setResponse(res.data.response || "No response received.");
    } catch (error) {
      console.error("Error processing query:", error);
      setResponse("An error occurred while processing your query.");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleVoiceInput = () => {
    if (!("webkitSpeechRecognition" in window)) {
      alert("Your browser does not support speech recognition. Please try Chrome.");
      return;
    }

    const recognition = new window.webkitSpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    setIsListening(true);

    recognition.onresult = async (event) => {
      const voiceQuery = event.results[0][0].transcript;
      setQuery(voiceQuery);

      setIsListening(false);

      // Immediately submit the voice query
      await handleQuerySubmit(voiceQuery);
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  return (
    <div className="query-processor">
      <header className="header">
        <h1>Healthcare AI Call Center</h1>
        <p>Ask your query, and our AI agents will assist you!</p>
      </header>

      <div className="query-section">
        <textarea
          className="query-input"
          placeholder="Type your query here or use the microphone..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={isProcessing || isListening}
        ></textarea>
        <div className="actions">
          <button className="voice-button" onClick={handleVoiceInput} disabled={isListening}>
            {isListening ? "🎙️ Listening..." : "🎤 Voice Input"}
          </button>
          <button
            className="submit-button"
            onClick={() => handleQuerySubmit()}
            disabled={isProcessing}
          >
            {isProcessing ? "Processing..." : "Submit Query"}
          </button>
        </div>
      </div>

      {response && (
        <div className="response-section">
          <h2>Agent Response</h2>
          <p>
            <strong>Routed to Agent:</strong> {agent}
          </p>
          <p>
            <strong>Response:</strong> {response}
          </p>
        </div>
      )}
    </div>
  );
};

export default QueryProcessor;
