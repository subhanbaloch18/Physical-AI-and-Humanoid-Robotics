/**
 * QueryRequest model - Represents a request to the RAG agent
 */

/**
 * @typedef {Object} QueryRequest
 * @property {string} query - The user's query text
 * @property {string} [userId] - Optional user identifier
 * @property {Object} [metadata] - Additional metadata for the query
 * @property {Object} [selectedTextContext] - Context from selected text
 * @property {string} [selectedTextContext.content] - The selected text content
 * @property {string} [selectedTextContext.elementId] - ID of the element containing the selection
 * @property {string} [selectedTextContext.pageUrl] - URL of the page where text was selected
 * @property {string} [selectedTextContext.sectionTitle] - Title of the section containing the selection
 * @property {string} [selectedTextContext.precedingText] - Text before the selection
 * @property {string} [selectedTextContext.followingText] - Text after the selection
 * @property {string} [queryMode] - The query mode ('standard', 'contextual', 'full-book')
 */

class QueryRequest {
  /**
   * Create a new QueryRequest instance
   * @param {Object} params - Request parameters
   * @param {string} params.query - The user's query text
   * @param {string} [params.userId] - Optional user identifier
   * @param {Object} [params.metadata] - Additional metadata for the query
   * @param {Object} [params.selectedTextContext] - Context from selected text
   * @param {string} [params.sessionId] - Session identifier for conversation context
   * @param {string} [params.queryType] - Type of query (factual, conceptual, procedural, mixed)
   * @param {string} [params.queryMode] - The query mode ('standard', 'contextual', 'full-book')
   */
  constructor({ query, userId, metadata, selectedTextContext, sessionId, queryType = 'mixed', queryMode = 'standard' }) {
    if (!query || typeof query !== 'string' || query.trim().length === 0) {
      throw new Error('Query is required and must be a non-empty string');
    }

    if (query.length > 2000) {
      throw new Error('Query must not exceed 2000 characters');
    }

    this.query = query.trim();
    this.userId = userId || null;
    this.metadata = metadata || {};
    this.selectedTextContext = selectedTextContext || null;
    this.sessionId = sessionId || null;
    this.queryType = queryType;
    this.queryMode = queryMode;
  }

  /**
   * Create a QueryRequest instance from raw data
   * @param {Object} rawData - Raw request data
   * @returns {QueryRequest} New QueryRequest instance
   */
  static fromRawData(rawData) {
    return new QueryRequest({
      query: rawData.query,
      userId: rawData.userId,
      metadata: rawData.metadata,
      selectedTextContext: rawData.selectedTextContext,
      sessionId: rawData.sessionId,
      queryType: rawData.queryType,
      queryMode: rawData.queryMode || 'standard'
    });
  }

  /**
   * Convert the request to a plain object for API transmission
   * @returns {Object} Plain object representation
   */
  toObject() {
    return {
      query: this.query,
      user_id: this.userId,
      metadata: this.metadata,
      selected_text_context: this.selectedTextContext,
      session_id: this.sessionId,
      query_type: this.queryType,
      query_mode: this.queryMode
    };
  }

  /**
   * Check if the request has selected text context
   * @returns {boolean} True if the request has selected text context
   */
  hasSelectedTextContext() {
    return !!this.selectedTextContext && this.selectedTextContext.content && this.selectedTextContext.content.trim().length > 0;
  }

  /**
   * Get a preview of the selected text (truncated if too long)
   * @param {number} maxLength - Maximum length of the preview
   * @returns {string} Preview of the selected text
   */
  getSelectedTextPreview(maxLength = 100) {
    if (!this.hasSelectedTextContext()) {
      return '';
    }

    const content = this.selectedTextContext.content;
    if (content.length <= maxLength) {
      return content;
    }
    return content.substring(0, maxLength) + '...';
  }

  /**
   * Check if the query is likely a factual question
   * @returns {boolean} True if the query appears to be factual
   */
  isFactualQuery() {
    const factualIndicators = [
      'what is', 'what are', 'when', 'where', 'who', 'how many', 'define', 'explain', 'name', 'list', 'identify'
    ];

    const lowerQuery = this.query.toLowerCase();
    return factualIndicators.some(indicator => lowerQuery.includes(indicator));
  }

  /**
   * Check if the query is likely a conceptual question
   * @returns {boolean} True if the query appears to be conceptual
   */
  isConceptualQuery() {
    const conceptualIndicators = [
      'why', 'how does', 'what causes', 'what means', 'what represents',
      'what constitutes', 'what defines', 'what characterizes', 'what principle'
    ];

    const lowerQuery = this.query.toLowerCase();
    return conceptualIndicators.some(indicator => lowerQuery.includes(indicator));
  }

  /**
   * Check if the query is likely a procedural question
   * @returns {boolean} True if the query appears to be procedural
   */
  isProceduralQuery() {
    const proceduralIndicators = [
      'how to', 'how do', 'steps to', 'process for', 'method for',
      'way to', 'technique for', 'approach for', 'implement', 'create',
      'build', 'develop', 'design', 'construct', 'execute', 'procedure'
    ];

    const lowerQuery = this.query.toLowerCase();
    return proceduralIndicators.some(indicator => lowerQuery.includes(indicator));
  }

  /**
   * Detect the likely type of query based on content
   * @returns {string} Query type ('factual', 'conceptual', 'procedural', or 'mixed')
   */
  detectQueryType() {
    const isFactual = this.isFactualQuery();
    const isConceptual = this.isConceptualQuery();
    const isProcedural = this.isProceduralQuery();

    // Count matches
    const matches = [isFactual, isConceptual, isProcedural].filter(Boolean).length;

    if (matches === 0) {
      return 'mixed'; // No clear indicators, assume mixed
    } else if (matches === 1) {
      if (isFactual) return 'factual';
      if (isConceptual) return 'conceptual';
      if (isProcedural) return 'procedural';
    } else {
      // Multiple indicators, return mixed
      return 'mixed';
    }
  }

  /**
   * Validate the query request
   * @returns {Array<string>} Array of validation errors (empty if valid)
   */
  validate() {
    const errors = [];

    if (!this.query || typeof this.query !== 'string' || this.query.trim().length === 0) {
      errors.push('Query is required and must be a non-empty string');
    }

    if (this.query.length > 2000) {
      errors.push('Query must not exceed 2000 characters');
    }

    if (this.selectedTextContext) {
      if (typeof this.selectedTextContext !== 'object') {
        errors.push('Selected text context must be an object');
      } else {
        if (this.selectedTextContext.content && typeof this.selectedTextContext.content !== 'string') {
          errors.push('Selected text content must be a string');
        }
        if (this.selectedTextContext.elementId && typeof this.selectedTextContext.elementId !== 'string') {
          errors.push('Selected text elementId must be a string');
        }
        if (this.selectedTextContext.pageUrl && typeof this.selectedTextContext.pageUrl !== 'string') {
          errors.push('Selected text pageUrl must be a string');
        }
        if (this.selectedTextContext.sectionTitle && typeof this.selectedTextContext.sectionTitle !== 'string') {
          errors.push('Selected text sectionTitle must be a string');
        }
      }
    }

    if (this.userId && typeof this.userId !== 'string') {
      errors.push('User ID must be a string');
    }

    if (this.metadata && typeof this.metadata !== 'object') {
      errors.push('Metadata must be an object');
    }

    if (this.sessionId && typeof this.sessionId !== 'string') {
      errors.push('Session ID must be a string');
    }

    if (this.queryType && typeof this.queryType !== 'string') {
      errors.push('Query type must be a string');
    }

    if (this.queryMode && typeof this.queryMode !== 'string') {
      errors.push('Query mode must be a string');
    }

    // Validate query mode values
    const validQueryModes = ['standard', 'contextual', 'full-book'];
    if (this.queryMode && !validQueryModes.includes(this.queryMode)) {
      errors.push(`Query mode must be one of: ${validQueryModes.join(', ')}`);
    }

    return errors;
  }
}

export default QueryRequest;