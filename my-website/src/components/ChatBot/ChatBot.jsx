import React, { useState, useRef, useEffect } from 'react';
import Message from './Message';
import QueryRequest from '../../models/query-request';

const API_URL =
  typeof window !== 'undefined' && window.location.hostname === 'localhost'
    ? 'http://localhost:8000/v1/query'
    : '/api/query';

const QUERY_TYPES = [
  { key: 'factual', label: 'Factual', icon: '\uD83D\uDCCB' },
  { key: 'conceptual', label: 'Conceptual', icon: '\uD83E\uDDE0' },
  { key: 'procedural', label: 'Procedural', icon: '\u2699\uFE0F' },
  { key: 'mixed', label: 'Mixed', icon: '\uD83D\uDD00' },
];

const QUERY_MODES = [
  { key: 'standard', label: 'Standard', icon: '\uD83D\uDD0D', desc: 'Quick, focused answers' },
  { key: 'contextual', label: 'Contextual', icon: '\uD83C\uDFAF', desc: 'Selected text context' },
  { key: 'full-book', label: 'Full Book', icon: '\uD83D\uDCDA', desc: 'Comprehensive analysis' },
];

const SUGGESTIONS = [
  { icon: '\uD83E\uDD16', text: 'What is physical AI?' },
  { icon: '\uD83E\uDDE0', text: 'Explain humanoid robotics' },
  { icon: '\u2699\uFE0F', text: 'How do robots learn from their environment?' },
  { icon: '\uD83D\uDE80', text: 'What is the future of robotics?' },
];

const ChatBot = ({
  initialQueryType = 'mixed',
  initialQueryMode = 'standard',
  enableTextSelection = false,
  showSourceCitations = true,
}) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [queryType, setQueryType] = useState(initialQueryType);
  const [queryMode, setQueryMode] = useState(initialQueryMode);
  const [selectedText, setSelectedText] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    setSessionId(`sess_${Date.now()}_${Math.floor(Math.random() * 10000)}`);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (!enableTextSelection) return;
    const handleSelection = () => {
      const selection = window.getSelection();
      if (selection && selection.toString().trim().length >= 10) {
        setSelectedText({
          content: selection.toString().trim(),
          pageUrl: window.location.href,
          sectionTitle: '',
        });
      }
    };
    document.addEventListener('mouseup', handleSelection);
    return () => document.removeEventListener('mouseup', handleSelection);
  }, [enableTextSelection]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleClearChat = () => {
    setMessages([]);
    setSessionId(`sess_${Date.now()}_${Math.floor(Math.random() * 10000)}`);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const query = inputValue.trim();
    if (!query || isLoading) return;

    const userMessage = {
      sender: 'user',
      content: query,
      timestamp: new Date(),
      context: selectedText,
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const queryRequest = new QueryRequest({
        query,
        sessionId,
        queryType,
        queryMode,
        selectedTextContext: selectedText || undefined,
      });

      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(queryRequest.toObject()),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.error || `Server error: ${response.status}`);
      }

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          sender: 'agent',
          content: data.answer || data.response || 'No response received.',
          timestamp: new Date(),
          sources: data.sources || [],
          confidenceScore: data.confidence_score || 0,
          processingTime: data.processing_time || 0,
          isError: false,
        },
      ]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'agent',
          content: `Sorry, I encountered an error: ${error.message}. Please try again.`,
          timestamp: new Date(),
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
      setSelectedText(null);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleSuggestionClick = (text) => {
    setInputValue(text);
    inputRef.current?.focus();
  };

  return (
    <div className="cb-container">
      {/* Header */}
      <div className="cb-header">
        <div className="cb-header-left">
          <div className="cb-avatar-sm">
            <span>{'\u2728'}</span>
          </div>
          <div>
            <h3 className="cb-header-title">RAG Agent Assistant</h3>
            <span className="cb-header-status">
              <span className="cb-status-dot" />
              Online
            </span>
          </div>
        </div>
        <div className="cb-header-right">
          <button
            className="cb-clear-btn"
            onClick={handleClearChat}
            title="Clear chat"
          >
            Clear Chat
          </button>
        </div>
      </div>

      {/* Query Type & Mode Selectors */}
      <div className="cb-controls">
        <div className="cb-control-group">
          <span className="cb-control-label">Query Type:</span>
          <div className="cb-btn-group">
            {QUERY_TYPES.map((qt) => (
              <button
                key={qt.key}
                className={`cb-type-btn ${queryType === qt.key ? 'active' : ''}`}
                onClick={() => setQueryType(qt.key)}
                title={qt.label}
              >
                <span className="cb-type-icon">{qt.icon}</span>
                <span className="cb-type-label">{qt.label}</span>
              </button>
            ))}
          </div>
        </div>
        <div className="cb-control-group">
          <span className="cb-control-label">Mode:</span>
          <div className="cb-btn-group">
            {QUERY_MODES.map((qm) => (
              <button
                key={qm.key}
                className={`cb-type-btn ${queryMode === qm.key ? 'active' : ''}`}
                onClick={() => setQueryMode(qm.key)}
                title={qm.desc}
              >
                <span className="cb-type-icon">{qm.icon}</span>
                <span className="cb-type-label">{qm.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="cb-messages">
        {messages.length === 0 && (
          <div className="cb-empty">
            <div className="cb-empty-icon">{'\uD83E\uDD16'}</div>
            <h3 className="cb-empty-title">Hello! I'm your RAG Agent assistant.</h3>
            <p className="cb-empty-desc">
              How can I help you with the book content today? Select a query type
              and mode above, then ask me anything about Physical AI & Humanoid Robotics.
            </p>
            <div className="cb-suggestions">
              {SUGGESTIONS.map((s, idx) => (
                <button
                  key={idx}
                  className="cb-suggestion"
                  onClick={() => handleSuggestionClick(s.text)}
                >
                  <span className="cb-suggestion-icon">{s.icon}</span>
                  <span>{s.text}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, index) => (
          <Message key={index} message={msg} showSourceCitations={showSourceCitations} />
        ))}

        {isLoading && (
          <div className="cb-loading">
            <div className="cb-loading-avatar">{'\u2728'}</div>
            <div className="cb-loading-bubble">
              <div className="cb-typing-dots">
                <span /><span /><span />
              </div>
              <span className="cb-loading-text">Thinking...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Selected text banner */}
      {selectedText && (
        <div className="cb-selected-banner">
          <div className="cb-selected-content">
            <span className="cb-selected-icon">{'\uD83D\uDCCE'}</span>
            <span className="cb-selected-text">
              &quot;{selectedText.content.substring(0, 80)}
              {selectedText.content.length > 80 ? '...' : ''}&quot;
            </span>
          </div>
          <button onClick={() => setSelectedText(null)} className="cb-selected-clear">
            {'\u2715'}
          </button>
        </div>
      )}

      {/* Input */}
      <form className="cb-input-area" onSubmit={handleSubmit}>
        <div className="cb-input-wrapper">
          <textarea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about the book..."
            disabled={isLoading}
            rows={1}
            className="cb-input"
          />
          <button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            className="cb-send-btn"
            title="Send message"
          >
            {isLoading ? (
              <span className="cb-send-loading" />
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            )}
          </button>
        </div>
        <div className="cb-input-footer">
          <span className="cb-input-hint">Press Enter to send, Shift+Enter for new line</span>
          <span className="cb-char-count">{inputValue.length}/2000</span>
        </div>
      </form>
    </div>
  );
};

export default ChatBot;
