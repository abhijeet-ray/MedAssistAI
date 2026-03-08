import React, { useRef, useState, useEffect } from 'react';
import { sendChatMessage } from '../utils/api';
import { formatChatResponse, isDuplicateResponse } from '../utils/chatResponseFormatter';
import { ChatResponseDisplay } from './ChatResponseDisplay';

export interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  content: string;
  timestamp: Date;
}

export interface ChatHistoryEntry {
  user: string;
  ai: string;
}

interface ChatInterfaceProps {
  sessionId: string;
  role: string;
  onSendMessage?: (message: string) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  sessionId,
  role,
  onSendMessage,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatHistory, setChatHistory] = useState<ChatHistoryEntry[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showDisclaimer, setShowDisclaimer] = useState(true);
  const [chatError, setChatError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    // Validate message length
    if (inputValue.length > 1000) {
      setChatError('Message exceeds 1000 character limit');
      return;
    }

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentQuestion = inputValue;
    setInputValue('');
    setShowDisclaimer(false);
    setChatError(null);
    setIsLoading(true);
    onSendMessage?.(currentQuestion);

    try {
      // Send chat history along with the question
      const result = await sendChatMessage(sessionId, role, currentQuestion, chatHistory);

      if (result.error) {
        setChatError(result.error.message);
        const errorMessage: ChatMessage = {
          id: `msg-${Date.now()}`,
          sender: 'ai',
          content: `Sorry, I encountered an error: ${result.error.message}. Please try again.`,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      } else if (result.data?.answer) {
        // Check if this response is a duplicate of the last AI message
        const lastAIMessage = messages.filter((m) => m.sender === 'ai').pop();
        
        if (lastAIMessage && isDuplicateResponse(result.data.answer, lastAIMessage.content)) {
          // Skip adding duplicate response
          console.warn('Duplicate response detected, skipping');
        } else {
          const aiMessage: ChatMessage = {
            id: `msg-${Date.now()}`,
            sender: 'ai',
            content: result.data.answer,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, aiMessage]);
        }
        
        // Update chat history from backend response
        if (result.data.chatHistory) {
          setChatHistory(result.data.chatHistory);
        }
      }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to send message';
      setChatError(errorMsg);
      const errorMessage: ChatMessage = {
        id: `msg-${Date.now()}`,
        sender: 'ai',
        content: `Sorry, I encountered an error processing your message. Please try again.`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {showDisclaimer && messages.length === 0 && (
          <div
            style={{
              padding: '16px',
              background: 'rgba(99, 102, 241, 0.1)',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              borderRadius: '8px',
              marginBottom: '16px',
              fontSize: '13px',
              color: 'var(--text-secondary)',
            }}
          >
            ℹ️ This AI system provides informational insights only and does not provide medical
            diagnosis. Always consult a licensed healthcare professional.
          </div>
        )}

        {chatError && (
          <div
            style={{
              padding: '12px',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '8px',
              marginBottom: '16px',
              fontSize: '13px',
              color: '#fca5a5',
            }}
          >
            ❌ {chatError}
          </div>
        )}

        {messages.length === 0 && !showDisclaimer && (
          <p className="placeholder-text">Start a conversation about your medical documents</p>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            style={{
              marginBottom: '20px',
              display: 'flex',
              justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            <div
              style={{
                maxWidth: '75%',
                padding: message.sender === 'user' ? '12px 16px' : '16px',
                borderRadius: '12px',
                background:
                  message.sender === 'user'
                    ? 'var(--accent-primary)'
                    : 'var(--bg-secondary)',
                color: message.sender === 'user' ? 'white' : 'var(--text-primary)',
                fontSize: '14px',
                lineHeight: '1.5',
                wordWrap: 'break-word',
              }}
            >
              {message.sender === 'ai' ? (
                <ChatResponseDisplay response={formatChatResponse(message.content)} />
              ) : (
                message.content
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div style={{ display: 'flex', gap: '4px', padding: '12px' }}>
            <div
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: 'var(--accent-primary)',
                animation: 'pulse 1.4s infinite',
              }}
            />
            <div
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: 'var(--accent-primary)',
                animation: 'pulse 1.4s infinite 0.2s',
              }}
            />
            <div
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: 'var(--accent-primary)',
                animation: 'pulse 1.4s infinite 0.4s',
              }}
            />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <input
          type="text"
          placeholder="Type your question here (max 1000 characters)..."
          maxLength={1000}
          className="chat-input"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
        />
        <button
          className="send-button"
          onClick={handleSendMessage}
          disabled={isLoading || !inputValue.trim()}
          style={{
            opacity: isLoading || !inputValue.trim() ? 0.5 : 1,
            cursor: isLoading || !inputValue.trim() ? 'not-allowed' : 'pointer',
          }}
        >
          {isLoading ? '⏳' : '📤'}
        </button>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 60%, 100% {
            opacity: 0.3;
          }
          30% {
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
};
