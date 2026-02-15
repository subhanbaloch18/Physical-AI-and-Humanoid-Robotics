import React, { useState } from 'react';

const Message = ({ message, showSourceCitations = true }) => {
  const isUser = message.sender === 'user';
  const isAgent = message.sender === 'agent';
  const isError = message.isError;
  const [showSources, setShowSources] = useState(false);

  const formatDate = (date) => {
    if (date instanceof Date) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    if (typeof date === 'number') {
      return new Date(date * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    return '';
  };

  const getConfidenceLevel = (score) => {
    if (score >= 0.8) return { label: 'High', className: 'high' };
    if (score >= 0.5) return { label: 'Medium', className: 'medium' };
    return { label: 'Low', className: 'low' };
  };

  return (
    <div className={`cb-msg ${isUser ? 'cb-msg--user' : 'cb-msg--agent'} ${isError ? 'cb-msg--error' : ''}`}>
      {/* Avatar */}
      <div className={`cb-msg-avatar ${isUser ? 'cb-msg-avatar--user' : 'cb-msg-avatar--agent'}`}>
        {isUser ? '\uD83D\uDC64' : isError ? '\u26A0\uFE0F' : '\u2728'}
      </div>

      <div className="cb-msg-body">
        {/* Header */}
        <div className="cb-msg-header">
          <span className="cb-msg-sender">{isUser ? 'You' : 'AI Assistant'}</span>
          {message.timestamp && (
            <span className="cb-msg-time">{formatDate(message.timestamp)}</span>
          )}
        </div>

        {/* Content */}
        <div className="cb-msg-content">
          {message.content}
        </div>

        {/* Selected text context */}
        {message.context && message.context.content && (
          <div className="cb-msg-context">
            <span className="cb-msg-context-icon">\uD83D\uDCCE</span>
            <span>
              &quot;{message.context.content.substring(0, 100)}
              {message.context.content.length > 100 ? '...' : ''}&quot;
            </span>
          </div>
        )}

        {/* Metadata bar for agent messages */}
        {isAgent && !isError && (
          <div className="cb-msg-meta">
            {/* Confidence */}
            {message.confidenceScore !== undefined && message.confidenceScore > 0 && (
              <div className="cb-meta-item">
                <div className={`cb-confidence-badge cb-confidence--${getConfidenceLevel(message.confidenceScore).className}`}>
                  <div
                    className="cb-confidence-fill"
                    style={{ width: `${Math.round(message.confidenceScore * 100)}%` }}
                  />
                  <span className="cb-confidence-text">
                    {Math.round(message.confidenceScore * 100)}% confidence
                  </span>
                </div>
              </div>
            )}

            {/* Processing time */}
            {message.processingTime > 0 && (
              <span className="cb-meta-tag">
                \u26A1 {(message.processingTime * 1000).toFixed(0)}ms
              </span>
            )}

            {/* Sources toggle */}
            {showSourceCitations && message.sources && message.sources.length > 0 && (
              <button
                className="cb-meta-tag cb-meta-tag--clickable"
                onClick={() => setShowSources(!showSources)}
              >
                \uD83D\uDCC4 {message.sources.length} source{message.sources.length !== 1 ? 's' : ''}
                <span className="cb-sources-chevron">{showSources ? '\u25B2' : '\u25BC'}</span>
              </button>
            )}
          </div>
        )}

        {/* Expandable Sources */}
        {isAgent && showSources && message.sources && message.sources.length > 0 && (
          <div className="cb-sources">
            {message.sources.slice(0, 5).map((source, index) => (
              <div key={index} className="cb-source-item">
                <div className="cb-source-header">
                  <span className="cb-source-num">{index + 1}</span>
                  {source.source_url ? (
                    <a href={source.source_url} target="_blank" rel="noopener noreferrer" className="cb-source-link">
                      {source.document_title || `Source ${index + 1}`}
                    </a>
                  ) : (
                    <span className="cb-source-title">{source.document_title || `Source ${index + 1}`}</span>
                  )}
                </div>
                {source.similarity_score > 0 && (
                  <div className="cb-source-score">
                    <div className="cb-source-score-bar">
                      <div
                        className="cb-source-score-fill"
                        style={{ width: `${Math.round(source.similarity_score * 100)}%` }}
                      />
                    </div>
                    <span className="cb-source-score-text">
                      {(source.similarity_score * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Message;
