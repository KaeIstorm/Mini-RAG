"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const API_URL = process.env.NEXT_PUBLIC_API_URL;
// These icons were causing a compilation error.
// They have been replaced with text-based alternatives.
const IngestIcon = () => <span>[UPLOAD]</span>;
const QueryIcon = () => <span>[SEARCH]</span>;
const SpinnerIcon = () => <span>[LOADING]</span>;

// This is the main component for the home page of your Next.js app.
// It contains all the logic and UI for the RAG application.
export default function HomePage() {
  // State for managing UI interactions and data
  const [inputText, setInputText] = useState("");
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState(null);
  const [sources, setSources] = useState(null);
  const [responseTime, setResponseTime] = useState(null);
  const [tokenEstimate, setTokenEstimate] = useState(null);
  const [loadingQuery, setLoadingQuery] = useState(false);
  const [loadingIngest, setLoadingIngest] = useState(false);

  // Function to handle the document ingestion
const handleIngest = async () => {
  try {
    let response;

    if (file && file.type !== "text/plain") {
      // PDF / DOCX case
      const formData = new FormData();
      formData.append("file", file);
      response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/ingest`, {
        method: "POST",
        body: formData,
      });
    } else {
      // Plain text case
      response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text_content: text }),
      });
    }

    const data = await response.json();
    alert(data.message || "Document ingestion successful!");
  } catch (err) {
    console.error("Ingestion failed:", err);
    alert("Failed to ingest document.");
  }
};


  // Function to handle file upload
const handleFileUpload = (e) => {
  const file = e.target.files[0];
  if (file) {
    if (file.type === "text/plain") {
      const reader = new FileReader();
      reader.onload = (event) => {
        setText(event.target.result); // Put actual text in textarea
      };
      reader.readAsText(file);
    } else {
      setText(""); // Clear textarea for non-text files
      setFile(file); // Keep file separately for PDF/Docx
    }
  }
};

  // Function to handle the user's query
  const handleQuery = async (e) => {
    e.preventDefault();
    if (!query) return;

    setLoadingQuery(true);
    setAnswer(null); // Clear previous results
    setSources(null);
    setResponseTime(null);
    setTokenEstimate(null);

    const startTime = performance.now();
    try {
      // NOTE: Replace with your actual FastAPI endpoint for querying.
      const response = await fetch(`${API_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: query }),
      });

      if (!response.ok) {
        throw new Error("Query failed. Please check the backend.");
      }

      const data = await response.json();
      const endTime = performance.now();

      // Check for a 'no-answer' case.
      if (data.answer.toLowerCase().includes("i don't know")) {
        setAnswer("I'm sorry, I couldn't find an answer to that question in the provided documents.");
        setSources(null);
      } else {
        // Parse citations from the answer string
        const citationRegex = /\[Source ID: (\d+)]/g;
        const formattedAnswer = data.answer.replace(citationRegex, (match, id) => {
          // You can create a hyperlink or a tooltip here for a better UI
          return `<sup>[${id}]</sup>`;
        });
        setAnswer(formattedAnswer);
        setSources(data.sources); // Assumes backend returns sources in a 'sources' key
      }
      
      setResponseTime((endTime - startTime).toFixed(2));
      // NOTE: These are mock estimates for now. Your backend can return real ones.
      setTokenEstimate(Math.floor(data.answer.length / 4));

    } catch (error) {
      console.error(error);
      setAnswer("An error occurred. Please try again.");
    } finally {
      setLoadingQuery(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-gray-200 p-8 flex flex-col items-center">
      {/* Title */}
      <motion.div initial={{ y: -50, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ duration: 0.5 }}>
        <h1 className="text-4xl md:text-5xl font-extrabold text-center mb-2 leading-tight tracking-tight">
          Mini RAG 
        </h1>
        <p className="text-lg md:text-xl font-medium text-center text-blue-300 mb-8">
          Chat with your documents in real-time.
        </p>
      </motion.div>

      <div className="w-full max-w-3xl space-y-8">
        {/* Document Ingestion Panel */}
        <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ duration: 0.5, delay: 0.2 }}>
          <div className="bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-700">
            <h2 className="text-2xl font-bold mb-4 text-white">1. Index a Document</h2>
            <p className="text-sm text-gray-400 mb-4">Paste or upload a text file. This will update the knowledge base for your RAG.</p>
            <textarea
              className="w-full h-40 p-4 rounded-lg bg-gray-700 border border-gray-600 text-white placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
              placeholder="Paste your text here..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
            />
            
            <div className="flex items-center space-x-4 mt-4">
              <label htmlFor="file-upload" className="w-1/2 flex items-center justify-center space-x-2 bg-gray-700 text-white font-semibold py-3 px-6 rounded-lg shadow-md hover:bg-gray-600 transition-colors cursor-pointer">
                <IngestIcon />
                <span>Upload File</span>
              </label>
              <input
                id="file-upload"
                type="file"
                accept=".txt,.pdf"
                onChange={handleFileUpload}
                className="hidden"
              />
              <button
                onClick={handleIngest}
                disabled={loadingIngest || !inputText}
                className="w-1/2 flex items-center justify-center space-x-2 bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg shadow-md hover:bg-blue-700 transition-colors disabled:bg-gray-500 disabled:cursor-not-allowed"
              >
                {loadingIngest ? (
                  <>
                    <SpinnerIcon />
                    <span>Indexing...</span>
                  </>
                ) : (
                  <>
                    <IngestIcon />
                    <span>Index Document</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </motion.div>

        {/* Query Panel */}
        <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ duration: 0.5, delay: 0.4 }}>
          <div className="bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-700">
            <h2 className="text-2xl font-bold mb-4 text-white">2. Ask a Question</h2>
            <form onSubmit={handleQuery} className="flex flex-col space-y-4">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Type your question here..."
                className="w-full p-4 rounded-lg bg-gray-700 border border-gray-600 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors"
              />
              <button
                type="submit"
                disabled={loadingQuery || !query}
                className="w-full flex items-center justify-center space-x-2 bg-green-600 text-white font-semibold py-3 px-6 rounded-lg shadow-md hover:bg-green-700 transition-colors disabled:bg-gray-500 disabled:cursor-not-allowed"
              >
                {loadingQuery ? (
                  <>
                    <SpinnerIcon />
                    <span>Searching...</span>
                  </>
                ) : (
                  <>
                    <QueryIcon />
                    <span>Search</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </motion.div>

        {/* Answer Panel */}
        <AnimatePresence>
          {answer && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-700"
            >
              <h2 className="text-2xl font-bold mb-4 text-white">Answer</h2>
              <div
                className="text-gray-300 leading-relaxed"
                dangerouslySetInnerHTML={{ __html: answer }}
              />

              {sources && sources.length > 0 && (
                <div className="mt-6 border-t border-gray-700 pt-4">
                  <h3 className="text-lg font-bold text-gray-400 mb-2">Sources</h3>
                  <ul className="list-disc list-inside text-sm text-gray-400 space-y-1">
                    {sources.map((source, index) => (
                      <li key={index}>
                        <a href={source} target="_blank" rel="noopener noreferrer" className="hover:underline text-blue-400">{source}</a>
                        <sup>[{index + 1}]</sup>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
        
        {/* Metrics Panel */}
        <AnimatePresence>
          {(responseTime || tokenEstimate) && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="text-center text-sm text-gray-400 mt-8"
            >
              <p>Response Time: {responseTime}ms</p>
              {tokenEstimate && <p>Estimated Tokens: {tokenEstimate}</p>}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}