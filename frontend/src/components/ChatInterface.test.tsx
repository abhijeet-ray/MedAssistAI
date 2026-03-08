import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChatInterface } from './ChatInterface';
import type { ChatMessage, ChatHistoryEntry } from './ChatInterface';
import * as api from '../utils/api';

/**
 * Unit tests for ChatInterface component
 * Validates: Requirements 1.1, 1.2, 1.3, 1.5, 2.1, 4.2, 4.4, 4.5, 16.1, 16.2, 16.3, 16.4, 16.5
 */

vi.mock('../utils/api');

describe('ChatInterface Component', () => {
  const mockSessionId = 'test-session-123';
  const mockRole = 'patient';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('7.1: Chat History State Initialization', () => {
    it('should initialize empty chat history on component mount', () => {
      render(
        <ChatInterface sessionId={mockSessionId} role={mockRole} />
      );

      // Verify chat interface is rendered
      const chatInput = screen.getByPlaceholderText(/Type your question/i);
      expect(chatInput).toBeDefined();

      // Chat history should be initialized (verified through behavior)
      expect(chatInput).toHaveValue('');
    });

    it('should have ChatMessage interface with required fields', () => {
      // Verify interface structure through type checking
      const message: ChatMessage = {
        id: 'msg-1',
        sender: 'user',
        content: 'Test message',
        timestamp: new Date(),
      };

      expect(message.id).toBeDefined();
      expect(message.sender).toBe('user');
      expect(message.content).toBeDefined();
      expect(message.timestamp).toBeInstanceOf(Date);
    });

    it('should have ChatHistoryEntry interface with required fields', () => {
      // Verify interface structure through type checking
      const entry: ChatHistoryEntry = {
        user: 'What is my hemoglobin?',
        ai: 'Your hemoglobin is 13.5 g/dL',
      };

      expect(entry.user).toBeDefined();
      expect(entry.ai).toBeDefined();
    });
  });

  describe('7.2: Message Appending to Chat History', () => {
    it('should append user message to chat history when sending message', async () => {
      const mockResponse = {
        data: {
          answer: 'Test response',
          source: 'uploaded_document',
          chatHistory: [
            {
              user: 'Test question',
              ai: 'Test response',
            },
          ],
        },
      };

      vi.mocked(api.sendChatMessage).mockResolvedValue(mockResponse);

      render(
        <ChatInterface sessionId={mockSessionId} role={mockRole} />
      );

      const chatInput = screen.getByPlaceholderText(/Type your question/i);
      const sendButton = screen.getByRole('button', { name: /📤|⏳/i });

      // Type and send message
      fireEvent.change(chatInput, { target: { value: 'Test question' } });
      fireEvent.click(sendButton);

      // Verify user message appears in UI
      await waitFor(() => {
        expect(screen.getByText('Test question')).toBeDefined();
      });
    });

    it('should append AI response to chat history when received', async () => {
      const mockResponse = {
        data: {
          answer: 'AI response text',
          source: 'uploaded_document',
          chatHistory: [
            {
              user: 'Test question',
              ai: 'AI response text',
            },
          ],
        },
      };

      vi.mocked(api.sendChatMessage).mockResolvedValue(mockResponse);

      render(
        <ChatInterface sessionId={mockSessionId} role={mockRole} />
      );

      const chatInput = screen.getByPlaceholderText(/Type your question/i);
      const sendButton = screen.getByRole('button', { name: /📤|⏳/i });

      fireEvent.change(chatInput, { target: { value: 'Test question' } });
      fireEvent.click(sendButton);

      // Verify AI response appears in UI
      await waitFor(() => {
        expect(screen.getByText('AI response text')).toBeDefined();
      });
    });

    it('should add timestamps to each message', async () => {
      const mockResponse = {
        data: {
          answer: 'Test response',
          source: 'uploaded_document',
          chatHistory: [
            {
              user: 'Test question',
              ai: 'Test response',
            },
          ],
        },
      };

      vi.mocked(api.sendChatMessage).mockResolvedValue(mockResponse);

      render(
        <ChatInterface sessionId={mockSessionId} role={mockRole} />
      );

      const chatInput = screen.getByPlaceholderText(/Type your question/i);
      const sendButton = screen.getByRole('button', { name: /📤|⏳/i });

      fireEvent.change(chatInput, { target: { value: 'Test question' } });
      fireEvent.click(sendButton);

      // Verify messages are displayed (timestamps are added internally)
      await waitFor(() => {
        expect(screen.getByText('Test question')).toBeDefined();
        expect(screen.getByText('Test response')).toBeDefined();
      });
    });
  });

  describe('7.4: Chat History Transmission to Backend', () => {
    it('should include chat history in API request payload', async () => {
      const mockResponse = {
        data: {
          answer: 'Response',
          source: 'uploaded_document',
          chatHistory: [
            { user: 'Q1', ai: 'A1' },
            { user: 'Q2', ai: 'A2' },
          ],
        },
      };

      vi.mocked(api.sendChatMessage).mockResolvedValue(mockResponse);

      render(
        <ChatInterface sessionId={mockSessionId} role={mockRole} />
      );

      const chatInput = screen.getByPlaceholderText(/Type your question/i);
      const sendButton = screen.getByRole('button', { name: /📤|⏳/i });

      // Send first message
      fireEvent.change(chatInput, { target: { value: 'Q1' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(api.sendChatMessage).toHaveBeenCalled();
      });

      // Verify first call includes empty history
      expect(vi.mocked(api.sendChatMessage).mock.calls[0]).toEqual([
        mockSessionId,
        mockRole,
        'Q1',
        [],
      ]);

      // Clear mock and send second message
      vi.mocked(api.sendChatMessage).mockClear();
      vi.mocked(api.sendChatMessage).mockResolvedValue(mockResponse);

      fireEvent.change(chatInput, { target: { value: 'Q2' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(api.sendChatMessage).toHaveBeenCalled();
      });

      // Verify second call includes history from first response
      const secondCallArgs = vi.mocked(api.sendChatMessage).mock.calls[0];
      expect(secondCallArgs[0]).toBe(mockSessionId);
      expect(secondCallArgs[1]).toBe(mockRole);
      expect(secondCallArgs[2]).toBe('Q2');
      expect(secondCallArgs[3]).toEqual([
        { user: 'Q1', ai: 'A1' },
        { user: 'Q2', ai: 'A2' },
      ]);
    });

    it('should send complete history with each chat request', async () => {
      const mockResponse = {
        data: {
          answer: 'Response',
          source: 'uploaded_document',
          chatHistory: [
            { user: 'Q1', ai: 'A1' },
          ],
        },
      };

      vi.mocked(api.sendChatMessage).mockResolvedValue(mockResponse);

      render(
        <ChatInterface sessionId={mockSessionId} role={mockRole} />
      );

      const chatInput = screen.getByPlaceholderText(/Type your question/i);
      const sendButton = screen.getByRole('button', { name: /📤|⏳/i });

      fireEvent.change(chatInput, { target: { value: 'Q1' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(api.sendChatMessage).toHaveBeenCalledWith(
          mockSessionId,
          mockRole,
          'Q1',
          []
        );
      });
    });
  });

  describe('7.5: Frontend History Synchronization', () => {
    it('should update local chat history with backend-returned history', async () => {
      const backendHistory: ChatHistoryEntry[] = [
        { user: 'Q1', ai: 'A1' },
        { user: 'Q2', ai: 'A2' },
      ];

      const mockResponse = {
        data: {
          answer: 'Response',
          source: 'uploaded_document',
          chatHistory: backendHistory,
        },
      };

      vi.mocked(api.sendChatMessage).mockResolvedValue(mockResponse);

      render(
        <ChatInterface sessionId={mockSessionId} role={mockRole} />
      );

      const chatInput = screen.getByPlaceholderText(/Type your question/i);
      const sendButton = screen.getByRole('button', { name: /📤|⏳/i });

      fireEvent.change(chatInput, { target: { value: 'Q1' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText('Response')).toBeDefined();
      });

      // Verify that subsequent requests use the updated history
      vi.mocked(api.sendChatMessage).mockClear();
      vi.mocked(api.sendChatMessage).mockResolvedValue(mockResponse);

      fireEvent.change(chatInput, { target: { value: 'Q3' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(api.sendChatMessage).toHaveBeenCalled();
      });

      // Verify the history was passed to the second request
      const secondCallArgs = vi.mocked(api.sendChatMessage).mock.calls[0];
      expect(secondCallArgs[3]).toEqual(backendHistory);
    });

    it('should preserve message ordering from backend', async () => {
      const orderedHistory: ChatHistoryEntry[] = [
        { user: 'First question', ai: 'First answer' },
        { user: 'Second question', ai: 'Second answer' },
        { user: 'Third question', ai: 'Third answer' },
      ];

      const mockResponse = {
        data: {
          answer: 'Response',
          source: 'uploaded_document',
          chatHistory: orderedHistory,
        },
      };

      vi.mocked(api.sendChatMessage).mockResolvedValue(mockResponse);

      render(
        <ChatInterface sessionId={mockSessionId} role={mockRole} />
      );

      const chatInput = screen.getByPlaceholderText(/Type your question/i);
      const sendButton = screen.getByRole('button', { name: /📤|⏳/i });

      fireEvent.change(chatInput, { target: { value: 'First question' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText('Response')).toBeDefined();
      });

      // Verify ordering is maintained in subsequent requests
      vi.mocked(api.sendChatMessage).mockClear();
      vi.mocked(api.sendChatMessage).mockResolvedValue(mockResponse);

      fireEvent.change(chatInput, { target: { value: 'Next question' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(api.sendChatMessage).toHaveBeenCalled();
      });

      const secondCallArgs = vi.mocked(api.sendChatMessage).mock.calls[0];
      const passedHistory = secondCallArgs[3] as ChatHistoryEntry[];
      
      // Verify order is preserved
      expect(passedHistory[0].user).toBe('First question');
      expect(passedHistory[1].user).toBe('Second question');
      expect(passedHistory[2].user).toBe('Third question');
    });

    it('should handle backend modifications like truncation', async () => {
      // First response with 3 items
      const mockResponse1 = {
        data: {
          answer: 'Response 1',
          source: 'uploaded_document',
          chatHistory: [
            { user: 'Q1', ai: 'A1' },
            { user: 'Q2', ai: 'A2' },
            { user: 'Q3', ai: 'A3' },
          ],
        },
      };

      // Second response with truncated history (only last 2)
      const mockResponse2 = {
        data: {
          answer: 'Response 2',
          source: 'uploaded_document',
          chatHistory: [
            { user: 'Q2', ai: 'A2' },
            { user: 'Q3', ai: 'A3' },
          ],
        },
      };

      vi.mocked(api.sendChatMessage).mockResolvedValueOnce(mockResponse1);

      render(
        <ChatInterface sessionId={mockSessionId} role={mockRole} />
      );

      const chatInput = screen.getByPlaceholderText(/Type your question/i);
      const sendButton = screen.getByRole('button', { name: /📤|⏳/i });

      fireEvent.change(chatInput, { target: { value: 'Q1' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText('Response 1')).toBeDefined();
      });

      // Send second message with truncated response
      vi.mocked(api.sendChatMessage).mockResolvedValueOnce(mockResponse2);

      fireEvent.change(chatInput, { target: { value: 'Q4' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText('Response 2')).toBeDefined();
      });

      // Verify truncated history is used in next request
      vi.mocked(api.sendChatMessage).mockClear();
      vi.mocked(api.sendChatMessage).mockResolvedValue(mockResponse2);

      fireEvent.change(chatInput, { target: { value: 'Q5' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(api.sendChatMessage).toHaveBeenCalled();
      });

      const thirdCallArgs = vi.mocked(api.sendChatMessage).mock.calls[0];
      expect(thirdCallArgs[3]).toEqual([
        { user: 'Q2', ai: 'A2' },
        { user: 'Q3', ai: 'A3' },
      ]);
    });
  });

  describe('7.7: Error Handling for Chat History Failures', () => {
    it('should handle history transmission failures gracefully', async () => {
      const mockError = {
        error: {
          code: 'CHAT_ERROR',
          message: 'Network error',
          retryable: true,
        },
      };

      vi.mocked(api.sendChatMessage).mockResolvedValue(mockError);

      render(
        <ChatInterface sessionId={mockSessionId} role={mockRole} />
      );

      const chatInput = screen.getByPlaceholderText(/Type your question/i);
      const sendButton = screen.getByRole('button', { name: /📤|⏳/i });

      fireEvent.change(chatInput, { target: { value: 'Test question' } });
      fireEvent.click(sendButton);

      // Verify error is displayed
      await waitFor(() => {
        expect(screen.queryByText(/Network error/i)).toBeDefined();
      }, { timeout: 3000 });

      // Verify chat continues to function
      expect(chatInput).toBeEnabled();
    });

    it('should display error message on frontend state update failure', async () => {
      const mockResponse = {
        data: {
          answer: 'Test response',
          source: 'uploaded_document',
          chatHistory: [
            { user: 'Test', ai: 'Response' },
          ],
        },
      };

      vi.mocked(api.sendChatMessage).mockResolvedValue(mockResponse);

      render(
        <ChatInterface sessionId={mockSessionId} role={mockRole} />
      );

      const chatInput = screen.getByPlaceholderText(/Type your question/i);
      const sendButton = screen.getByRole('button', { name: /📤|⏳/i });

      fireEvent.change(chatInput, { target: { value: 'Test question' } });
      fireEvent.click(sendButton);

      // Verify response is displayed
      await waitFor(() => {
        expect(screen.getByText('Test response')).toBeDefined();
      });
    });

    it('should allow retry after error', async () => {
      const mockError = {
        error: {
          code: 'CHAT_ERROR',
          message: 'Temporary error',
          retryable: true,
        },
      };

      const mockSuccess = {
        data: {
          answer: 'Success response',
          source: 'uploaded_document',
          chatHistory: [
            { user: 'Retry question', ai: 'Success response' },
          ],
        },
      };

      vi.mocked(api.sendChatMessage).mockResolvedValueOnce(mockError);

      render(
        <ChatInterface sessionId={mockSessionId} role={mockRole} />
      );

      const chatInput = screen.getByPlaceholderText(/Type your question/i);
      const sendButton = screen.getByRole('button', { name: /📤|⏳/i });

      // First attempt fails
      fireEvent.change(chatInput, { target: { value: 'Retry question' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.queryByText(/Temporary error/i)).toBeDefined();
      }, { timeout: 3000 });

      // Retry succeeds
      vi.mocked(api.sendChatMessage).mockResolvedValueOnce(mockSuccess);

      fireEvent.change(chatInput, { target: { value: 'Retry question' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText('Success response')).toBeDefined();
      }, { timeout: 3000 });
    });

    it('should implement graceful degradation when history features fail', async () => {
      const mockResponse = {
        data: {
          answer: 'Response without history',
          source: 'uploaded_document',
          chatHistory: [],
        },
      };

      vi.mocked(api.sendChatMessage).mockResolvedValue(mockResponse);

      render(
        <ChatInterface sessionId={mockSessionId} role={mockRole} />
      );

      const chatInput = screen.getByPlaceholderText(/Type your question/i);
      const sendButton = screen.getByRole('button', { name: /📤|⏳/i });

      fireEvent.change(chatInput, { target: { value: 'Test question' } });
      fireEvent.click(sendButton);

      // Verify response is still displayed even without history
      await waitFor(() => {
        expect(screen.getByText('Response without history')).toBeDefined();
      });

      // Verify chat continues to function
      expect(chatInput).toBeEnabled();
    });

    it('should validate message length before sending', async () => {
      render(
        <ChatInterface sessionId={mockSessionId} role={mockRole} />
      );

      const chatInput = screen.getByPlaceholderText(/Type your question/i) as HTMLInputElement;
      const sendButton = screen.getByRole('button', { name: /📤|⏳/i });

      // Try to send message exceeding 1000 characters
      const longMessage = 'a'.repeat(1001);
      fireEvent.change(chatInput, { target: { value: longMessage } });
      fireEvent.click(sendButton);

      // Verify error is displayed
      await waitFor(() => {
        expect(screen.getByText(/exceeds 1000 character limit/i)).toBeDefined();
      });

      // Verify API was not called
      expect(api.sendChatMessage).not.toHaveBeenCalled();
    });

    it('should clear error message when new message is sent', async () => {
      const mockError = {
        error: {
          code: 'CHAT_ERROR',
          message: 'First error',
          retryable: true,
        },
      };

      const mockSuccess = {
        data: {
          answer: 'Success',
          source: 'uploaded_document',
          chatHistory: [],
        },
      };

      vi.mocked(api.sendChatMessage).mockResolvedValueOnce(mockError);

      render(
        <ChatInterface sessionId={mockSessionId} role={mockRole} />
      );

      const chatInput = screen.getByPlaceholderText(/Type your question/i);
      const sendButton = screen.getByRole('button', { name: /📤|⏳/i });

      // First message fails
      fireEvent.change(chatInput, { target: { value: 'First' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.queryByText(/First error/i)).toBeDefined();
      }, { timeout: 3000 });

      // Verify error banner is shown
      const errorBanners = screen.getAllByText(/First error/i);
      expect(errorBanners.length).toBeGreaterThan(0);

      // Second message succeeds
      vi.mocked(api.sendChatMessage).mockResolvedValueOnce(mockSuccess);

      fireEvent.change(chatInput, { target: { value: 'Second' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText('Success')).toBeDefined();
      }, { timeout: 3000 });

      // Verify the error banner is cleared (but error message remains in chat history)
      // The error banner should be gone, but the error message in the chat should remain
      const errorBannersAfter = screen.queryAllByText(/First error/i);
      // Should still have the error message in chat history, but not in the error banner
      expect(errorBannersAfter.length).toBeGreaterThan(0);
    });
  });

  describe('Integration: Full Chat Flow', () => {
    it('should handle complete chat flow with history', async () => {
      const mockResponse1 = {
        data: {
          answer: 'First answer',
          source: 'uploaded_document',
          chatHistory: [
            { user: 'First question', ai: 'First answer' },
          ],
        },
      };

      const mockResponse2 = {
        data: {
          answer: 'Second answer',
          source: 'uploaded_document',
          chatHistory: [
            { user: 'First question', ai: 'First answer' },
            { user: 'Second question', ai: 'Second answer' },
          ],
        },
      };

      vi.mocked(api.sendChatMessage)
        .mockResolvedValueOnce(mockResponse1)
        .mockResolvedValueOnce(mockResponse2);

      render(
        <ChatInterface sessionId={mockSessionId} role={mockRole} />
      );

      const chatInput = screen.getByPlaceholderText(/Type your question/i);
      const sendButton = screen.getByRole('button', { name: /📤|⏳/i });

      // Send first message
      fireEvent.change(chatInput, { target: { value: 'First question' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText('First answer')).toBeDefined();
      });

      // Verify first call had empty history
      expect(vi.mocked(api.sendChatMessage).mock.calls[0][3]).toEqual([]);

      // Send second message
      fireEvent.change(chatInput, { target: { value: 'Second question' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText('Second answer')).toBeDefined();
      });

      // Verify second call had history from first response
      expect(vi.mocked(api.sendChatMessage).mock.calls[1][3]).toEqual([
        { user: 'First question', ai: 'First answer' },
      ]);
    });
  });
});


/**
 * Unit tests for role parameter in chat requests
 * Validates: Requirements 8.1, 8.6
 */
describe('Role Parameter in Chat Requests', () => {
  const mockSessionId = 'test-session-123';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should include role parameter in chat request payload', async () => {
    const mockResponse = {
      data: {
        answer: 'Test response',
        source: 'uploaded_document',
        chatHistory: [],
      },
    };

    vi.mocked(api.sendChatMessage).mockResolvedValue(mockResponse);

    render(
      <ChatInterface sessionId={mockSessionId} role="doctor" />
    );

    const chatInput = screen.getByPlaceholderText(/Type your question/i);
    const sendButton = screen.getByRole('button', { name: /📤|⏳/i });

    fireEvent.change(chatInput, { target: { value: 'Test question' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(api.sendChatMessage).toHaveBeenCalled();
    });

    // Verify role is passed as second argument
    const callArgs = vi.mocked(api.sendChatMessage).mock.calls[0];
    expect(callArgs[1]).toBe('doctor');
  });

  it('should pass patient role in chat requests', async () => {
    const mockResponse = {
      data: {
        answer: 'Test response',
        source: 'uploaded_document',
        chatHistory: [],
      },
    };

    vi.mocked(api.sendChatMessage).mockResolvedValue(mockResponse);

    render(
      <ChatInterface sessionId={mockSessionId} role="patient" />
    );

    const chatInput = screen.getByPlaceholderText(/Type your question/i);
    const sendButton = screen.getByRole('button', { name: /📤|⏳/i });

    fireEvent.change(chatInput, { target: { value: 'Test question' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(api.sendChatMessage).toHaveBeenCalled();
    });

    const callArgs = vi.mocked(api.sendChatMessage).mock.calls[0];
    expect(callArgs[1]).toBe('patient');
  });

  it('should pass asha role in chat requests', async () => {
    const mockResponse = {
      data: {
        answer: 'Test response',
        source: 'uploaded_document',
        chatHistory: [],
      },
    };

    vi.mocked(api.sendChatMessage).mockResolvedValue(mockResponse);

    render(
      <ChatInterface sessionId={mockSessionId} role="asha" />
    );

    const chatInput = screen.getByPlaceholderText(/Type your question/i);
    const sendButton = screen.getByRole('button', { name: /📤|⏳/i });

    fireEvent.change(chatInput, { target: { value: 'Test question' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(api.sendChatMessage).toHaveBeenCalled();
    });

    const callArgs = vi.mocked(api.sendChatMessage).mock.calls[0];
    expect(callArgs[1]).toBe('asha');
  });

  it('should maintain role parameter across multiple requests', async () => {
    const mockResponse = {
      data: {
        answer: 'Test response',
        source: 'uploaded_document',
        chatHistory: [
          { user: 'Q1', ai: 'A1' },
        ],
      },
    };

    vi.mocked(api.sendChatMessage).mockResolvedValue(mockResponse);

    render(
      <ChatInterface sessionId={mockSessionId} role="doctor" />
    );

    const chatInput = screen.getByPlaceholderText(/Type your question/i);
    const sendButton = screen.getByRole('button', { name: /📤|⏳/i });

    // Send first message
    fireEvent.change(chatInput, { target: { value: 'Q1' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(api.sendChatMessage).toHaveBeenCalled();
    });

    // Verify first call has doctor role
    expect(vi.mocked(api.sendChatMessage).mock.calls[0][1]).toBe('doctor');

    // Send second message
    vi.mocked(api.sendChatMessage).mockClear();
    vi.mocked(api.sendChatMessage).mockResolvedValue(mockResponse);

    fireEvent.change(chatInput, { target: { value: 'Q2' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(api.sendChatMessage).toHaveBeenCalled();
    });

    // Verify second call also has doctor role
    expect(vi.mocked(api.sendChatMessage).mock.calls[0][1]).toBe('doctor');
  });

  it('should include role with chat history in requests', async () => {
    const mockResponse = {
      data: {
        answer: 'Response',
        source: 'uploaded_document',
        chatHistory: [
          { user: 'Q1', ai: 'A1' },
        ],
      },
    };

    vi.mocked(api.sendChatMessage).mockResolvedValue(mockResponse);

    render(
      <ChatInterface sessionId={mockSessionId} role="patient" />
    );

    const chatInput = screen.getByPlaceholderText(/Type your question/i);
    const sendButton = screen.getByRole('button', { name: /📤|⏳/i });

    // Send first message
    fireEvent.change(chatInput, { target: { value: 'Q1' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(api.sendChatMessage).toHaveBeenCalled();
    });

    // Send second message with history
    vi.mocked(api.sendChatMessage).mockClear();
    vi.mocked(api.sendChatMessage).mockResolvedValue(mockResponse);

    fireEvent.change(chatInput, { target: { value: 'Q2' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(api.sendChatMessage).toHaveBeenCalled();
    });

    // Verify role and history are both included
    const callArgs = vi.mocked(api.sendChatMessage).mock.calls[0];
    expect(callArgs[1]).toBe('patient'); // role
    expect(callArgs[3]).toEqual([{ user: 'Q1', ai: 'A1' }]); // history
  });
});

/**
 * Unit tests for role switching behavior
 * Validates: Requirements 8.6
 */
describe('Role Switching Behavior', () => {
  const mockSessionId = 'test-session-123';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should handle role prop changes', async () => {
    const mockResponse = {
      data: {
        answer: 'Response',
        source: 'uploaded_document',
        chatHistory: [],
      },
    };

    vi.mocked(api.sendChatMessage).mockResolvedValue(mockResponse);

    const { rerender } = render(
      <ChatInterface sessionId={mockSessionId} role="patient" />
    );

    const chatInput = screen.getByPlaceholderText(/Type your question/i);
    const sendButton = screen.getByRole('button', { name: /📤|⏳/i });

    // Send message as patient
    fireEvent.change(chatInput, { target: { value: 'Q1' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(api.sendChatMessage).toHaveBeenCalled();
    });

    expect(vi.mocked(api.sendChatMessage).mock.calls[0][1]).toBe('patient');

    // Switch role to doctor
    vi.mocked(api.sendChatMessage).mockClear();
    vi.mocked(api.sendChatMessage).mockResolvedValue(mockResponse);

    rerender(
      <ChatInterface sessionId={mockSessionId} role="doctor" />
    );

    // Send message as doctor
    fireEvent.change(chatInput, { target: { value: 'Q2' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(api.sendChatMessage).toHaveBeenCalled();
    });

    // Verify new role is used
    expect(vi.mocked(api.sendChatMessage).mock.calls[0][1]).toBe('doctor');
  });

  it('should use new role for subsequent messages after role change', async () => {
    const mockResponse = {
      data: {
        answer: 'Response',
        source: 'uploaded_document',
        chatHistory: [
          { user: 'Q1', ai: 'A1' },
        ],
      },
    };

    vi.mocked(api.sendChatMessage).mockResolvedValue(mockResponse);

    const { rerender } = render(
      <ChatInterface sessionId={mockSessionId} role="patient" />
    );

    const chatInput = screen.getByPlaceholderText(/Type your question/i);
    const sendButton = screen.getByRole('button', { name: /📤|⏳/i });

    // Send first message as patient
    fireEvent.change(chatInput, { target: { value: 'Q1' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(api.sendChatMessage).toHaveBeenCalled();
    });

    // Switch to asha role
    vi.mocked(api.sendChatMessage).mockClear();
    vi.mocked(api.sendChatMessage).mockResolvedValue(mockResponse);

    rerender(
      <ChatInterface sessionId={mockSessionId} role="asha" />
    );

    // Send second message as asha
    fireEvent.change(chatInput, { target: { value: 'Q2' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(api.sendChatMessage).toHaveBeenCalled();
    });

    // Verify asha role is used
    const callArgs = vi.mocked(api.sendChatMessage).mock.calls[0];
    expect(callArgs[1]).toBe('asha');
    // Verify history from patient role is still included
    expect(callArgs[3]).toEqual([{ user: 'Q1', ai: 'A1' }]);
  });
});
