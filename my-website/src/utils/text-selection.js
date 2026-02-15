/**
 * Utility functions for text selection handling
 */

/**
 * Get the currently selected text in the document
 * @returns {Object|null} Object containing selected text and context, or null if no selection
 */
export function getSelectedText() {
  const selection = window.getSelection();

  if (!selection || selection.toString().trim() === '') {
    return null;
  }

  const selectedText = selection.toString().trim();

  if (selectedText.length === 0) {
    return null;
  }

  // Get the selected range
  const range = selection.getRangeAt(0);
  const selectedElement = range.commonAncestorContainer.parentElement;

  return {
    content: selectedText,
    elementId: selectedElement.id || null,
    elementClass: selectedElement.className || null,
    elementTag: selectedElement.tagName || null,
    rect: range.getBoundingClientRect(), // Position information
    startOffset: range.startOffset,
    endOffset: range.endOffset,
    containerElement: selectedElement
  };
}

/**
 * Get the context around the selected text (surrounding text)
 * @param {string} selectedText - The selected text
 * @param {Element} containerElement - The element containing the selection
 * @param {number} contextLength - Number of characters before and after selection
 * @returns {Object} Object containing preceding and following context
 */
export function getTextContext(selectedText, containerElement, contextLength = 100) {
  if (!containerElement || !selectedText) {
    return {
      precedingText: '',
      followingText: ''
    };
  }

  const fullText = containerElement.textContent || '';
  const selectedIndex = fullText.indexOf(selectedText);

  if (selectedIndex === -1) {
    return {
      precedingText: '',
      followingText: ''
    };
  }

  const start = Math.max(0, selectedIndex - contextLength);
  const end = Math.min(fullText.length, selectedIndex + selectedText.length + contextLength);

  return {
    precedingText: fullText.substring(start, selectedIndex).trim(),
    followingText: fullText.substring(selectedIndex + selectedText.length, end).trim()
  };
}

/**
 * Create a text selection context object with all relevant information
 * @param {Object} selectionInfo - Information from getSelectedText()
 * @returns {Object} Complete text selection context
 */
export function createSelectionContext(selectionInfo) {
  if (!selectionInfo) {
    return null;
  }

  const { precedingText, followingText } = getTextContext(
    selectionInfo.content,
    selectionInfo.containerElement
  );

  return {
    content: selectionInfo.content,
    elementId: selectionInfo.elementId,
    elementClass: selectionInfo.elementClass,
    elementTag: selectionInfo.elementTag,
    rect: selectionInfo.rect,
    precedingText,
    followingText,
    timestamp: new Date().toISOString(),
    url: window.location.href,
    title: document.title,
    sectionTitle: getSectionTitle(selectionInfo.containerElement)
  };
}

/**
 * Get the section title based on the selected element
 * @param {Element} element - The element containing the selection
 * @returns {string} The section title
 */
function getSectionTitle(element) {
  if (!element) {
    return '';
  }

  // Look for heading elements in the ancestor chain
  let current = element;
  while (current && current !== document.body) {
    if (current.tagName && /^H[1-6]$/.test(current.tagName)) {
      return current.textContent.trim();
    }
    current = current.parentElement;
  }

  // If no heading found, try to get closest section title
  current = element;
  while (current && current !== document.body) {
    // Check for common section title patterns
    if (current.getAttribute('aria-label')) {
      return current.getAttribute('aria-label');
    }

    if (current.classList.contains('section-title') ||
        current.classList.contains('heading') ||
        current.classList.contains('title')) {
      return current.textContent.trim();
    }

    current = current.parentElement;
  }

  return '';
}

/**
 * Highlight selected text with a temporary visual indicator
 * @param {Object} selectionInfo - Information from getSelectedText()
 * @param {string} highlightColor - Color for the highlight (default: yellow)
 */
export function highlightSelection(selectionInfo, highlightColor = '#ffff0040') {
  if (!selectionInfo) {
    return;
  }

  // Create a temporary overlay to highlight the selection area
  const overlay = document.createElement('div');
  const rect = selectionInfo.rect;

  overlay.style.position = 'fixed';
  overlay.style.left = `${rect.left + window.scrollX}px`;
  overlay.style.top = `${rect.top + window.scrollY}px`;
  overlay.style.width = `${rect.width}px`;
  overlay.style.height = `${rect.height}px`;
  overlay.style.backgroundColor = highlightColor;
  overlay.style.pointerEvents = 'none';
  overlay.style.zIndex = '9999';
  overlay.style.borderRadius = '2px';

  document.body.appendChild(overlay);

  // Remove the highlight after a short delay
  setTimeout(() => {
    if (document.body.contains(overlay)) {
      document.body.removeChild(overlay);
    }
  }, 1000);

  return overlay;
}

/**
 * Add event listener for text selection
 * @param {Function} callback - Function to call when text is selected
 * @returns {Function} Function to remove the event listener
 */
export function addTextSelectionListener(callback) {
  let selectionTimeout = null;

  const handler = () => {
    // Clear any existing timeout
    if (selectionTimeout) {
      clearTimeout(selectionTimeout);
    }

    // Set a new timeout to debounce the selection event
    selectionTimeout = setTimeout(() => {
      const selected = getSelectedText();
      if (selected && selected.content.trim().length > 0) {
        const context = createSelectionContext(selected);
        callback(context);
      }
    }, 150); // Debounce by 150ms
  };

  document.addEventListener('mouseup', handler);
  document.addEventListener('keyup', handler);

  // Return a function to remove the event listener
  return () => {
    document.removeEventListener('mouseup', handler);
    document.removeEventListener('keyup', handler);
    if (selectionTimeout) {
      clearTimeout(selectionTimeout);
    }
  };
}

/**
 * Check if the selected text is likely to be relevant for context
 * @param {string} text - The selected text
 * @param {number} minLength - Minimum length for relevance (default: 10)
 * @param {number} maxLength - Maximum length for relevance (default: 1000)
 * @returns {boolean} True if the text is likely to be relevant
 */
export function isRelevantSelection(text, minLength = 10, maxLength = 1000) {
  if (!text) {
    return false;
  }

  const trimmedText = text.trim();

  // Check length constraints
  if (trimmedText.length < minLength || trimmedText.length > maxLength) {
    return false;
  }

  // Check if text contains mostly whitespace or special characters
  const wordCount = trimmedText.split(/\s+/).filter(word => word.length > 0).length;
  if (wordCount < 2) {
    return false;
  }

  // Check if text looks like a URL or email (probably not relevant as context)
  const urlPattern = /https?:\/\/|www\.|@\w+\./;
  if (urlPattern.test(trimmedText)) {
    return false;
  }

  return true;
}

/**
 * Get all relevant selections on the page
 * @param {number} minSelectionLength - Minimum length for a selection to be considered
 * @returns {Array} Array of selection context objects
 */
export function getAllRelevantSelections(minSelectionLength = 10) {
  const selections = [];

  // In a real implementation, you might want to look for pre-highlighted or marked text
  // For now, we'll just return the current selection if it's relevant
  const currentSelection = getSelectedText();

  if (currentSelection && isRelevantSelection(currentSelection.content, minSelectionLength)) {
    selections.push(createSelectionContext(currentSelection));
  }

  return selections;
}

// Export utility functions
export {
  getSelectedText as getTextSelection,
  createSelectionContext as buildSelectionContext,
  isRelevantSelection as isValidSelection,
  getAllRelevantSelections as getValidSelections
};

// Default export
export default {
  getTextSelection,
  createSelectionContext,
  isRelevantSelection,
  addTextSelectionListener,
  highlightSelection,
  getTextContext,
  getValidSelections: getAllRelevantSelections
};