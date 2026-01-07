/**
 * Chat Component.
 *
 * Provides an interface to chat with the AI using RAG.
 */

import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import { sendChatMessage } from '../services/api';
import './Chat.css';

function Chat() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const query = inputValue.trim();
    if (!query || isLoading) return;

    // Add user message to chat
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: query,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      // Send query to backend (k=5 after re-ranking)
      const response = await sendChatMessage(query, 5, true);

      // Add assistant message to chat
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.answer,
        timestamp: Date.now(),
        sources: response.context_used || [],
        hasContext: response.has_context,
        numChunks: response.num_chunks,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Focus input after response
      inputRef.current?.focus();
    } catch (err) {
      console.error('Chat error:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to get response';
      setError(errorMessage);

      // Add error message to chat
      const errorChatMessage = {
        id: Date.now() + 1,
        role: 'error',
        content: `❌ Error: ${errorMessage}`,
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, errorChatMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = () => {
    if (confirm('Clear all chat messages?')) {
      setMessages([]);
      setError(null);
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div>
          <h2>💬 Chat with Your Notes</h2>
          <p className="chat-subtitle">Ask questions about your uploaded notes</p>
        </div>
        {messages.length > 0 && (
          <button onClick={handleClearChat} className="clear-button" title="Clear chat">
            🗑️ Clear
          </button>
        )}
      </div>

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-chat">
            <div className="empty-chat-icon">💡</div>
            <h3>Start a conversation</h3>
            <p>Ask questions about your notes and get AI-powered answers</p>
            <div className="example-queries">
              <p className="example-title">Example questions:</p>
              <ul>
                <li>"What is machine learning?"</li>
                <li>"Summarize my Python notes"</li>
                <li>"What are the key concepts in my notes?"</li>
              </ul>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <div key={message.id} className={`message ${message.role}`}>
                <div className="message-header">
                  <span className="message-role">
                    {message.role === 'user' ? '👤 You' : message.role === 'error' ? '⚠️ Error' : '🤖 AI'}
                  </span>
                  <span className="message-time">{formatTimestamp(message.timestamp)}</span>
                </div>
                <div className="message-content">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm, remarkMath]}
                    rehypePlugins={[rehypeKatex]}
                  >
                    {message.content}
                  </ReactMarkdown>
                </div>

                {/* Display sources if available */}
                {message.sources && message.sources.length > 0 && (
                  <div className="message-sources">
                    <details>
                      <summary>
                        📚 Sources ({message.numChunks} chunk{message.numChunks !== 1 ? 's' : ''} used)
                      </summary>
                      <div className="sources-list">
                        {message.sources.map((source, idx) => {
                          const similarity = ((1 - source.distance) * 100).toFixed(1);
                          return (
                            <div key={idx} className="source-item">
                              <div className="source-header">
                                <strong className="source-note-title">
                                  {source.metadata?.title || 'Untitled Note'}
                                </strong>
                                <span className="source-similarity">{similarity}% match</span>
                              </div>
                              <div className="source-text">
                                {source.text.substring(0, 200)}
                                {source.text.length > 200 ? '...' : ''}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </details>
                  </div>
                )}

                {/* Show warning if no context was found */}
                {message.role === 'assistant' && message.hasContext === false && (
                  <div className="no-context-warning">
                    ℹ️ No relevant context found in your notes. Try adding more notes or rephrasing your question.
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="message assistant loading">
                <div className="message-header">
                  <span className="message-role">🤖 AI</span>
                </div>
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <span className="loading-text">Thinking...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      <div className="chat-input-container">
        <form onSubmit={handleSubmit} className="chat-form">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask a question about your notes..."
            className="chat-input"
            disabled={isLoading}
            autoFocus
          />
          <button
            type="submit"
            className="send-button"
            disabled={isLoading || !inputValue.trim()}
          >
            {isLoading ? '⏳' : '📤'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default Chat;
