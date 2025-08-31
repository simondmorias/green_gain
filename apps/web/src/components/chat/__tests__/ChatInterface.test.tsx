import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { useChat } from '@/hooks/useChat';
import ChatInterface from '../ChatInterface';

// Mock the useChat hook
jest.mock('@/hooks/useChat', () => ({
  useChat: jest.fn(() => ({
    messages: [],
    isLoading: false,
    error: null,
    isRetrying: false,
    sendMessage: jest.fn(),
    retryLastMessage: jest.fn(),
    clearError: jest.fn(),
    clearMessages: jest.fn(),
  })),
}));

// Mock fetch
global.fetch = jest.fn();

const mockUseChat = useChat as jest.MockedFunction<typeof useChat>;

describe('ChatInterface', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear();
    jest.clearAllMocks();
  });

  it('renders chat interface with header', () => {
    render(<ChatInterface />);
    
    expect(screen.getByText('AI Assistant Chat')).toBeInTheDocument();
    expect(screen.getByText('Ask me anything and I\'ll help you out!')).toBeInTheDocument();
  });

  it('shows empty state when no messages', () => {
    render(<ChatInterface />);
    
    expect(screen.getByText('Start a conversation')).toBeInTheDocument();
    expect(screen.getByText('Type a message below to begin chatting with the AI assistant.')).toBeInTheDocument();
  });

  it('displays error message with retry and dismiss buttons', () => {
    mockUseChat.mockReturnValue({
      messages: [],
      isLoading: false,
      error: 'Connection failed. Please try again.',
      isRetrying: false,
      sendMessage: jest.fn(),
      retryLastMessage: jest.fn(),
      clearError: jest.fn(),
      clearMessages: jest.fn(),
    });

    render(<ChatInterface />);
    
    // Use more flexible text matching since the error message is split across HTML elements
    expect(screen.getByText(/Connection failed\. Please try again\./)).toBeInTheDocument();
    expect(screen.getByText('Error:')).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
    expect(screen.getByText('Dismiss')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    mockUseChat.mockReturnValue({
      messages: [
        {
          id: '1',
          content: 'Hello',
          role: 'user',
          timestamp: new Date(),
        }
      ],
      isLoading: true,
      error: null,
      isRetrying: false,
      sendMessage: jest.fn(),
      retryLastMessage: jest.fn(),
      clearError: jest.fn(),
      clearMessages: jest.fn(),
    });

    render(<ChatInterface />);
    
    expect(screen.getByText('Thinking...')).toBeInTheDocument();
  });

  it('calls sendMessage when user sends a message', async () => {
    const mockSendMessage = jest.fn();
    mockUseChat.mockReturnValue({
      messages: [],
      isLoading: false,
      error: null,
      isRetrying: false,
      sendMessage: mockSendMessage,
      retryLastMessage: jest.fn(),
      clearError: jest.fn(),
      clearMessages: jest.fn(),
    });

    render(<ChatInterface />);
    
    const textarea = screen.getByPlaceholderText(/Type your message here/);
    const sendButton = screen.getByText('Send');

    fireEvent.change(textarea, { target: { value: 'Hello' } });
    fireEvent.click(sendButton);

    expect(mockSendMessage).toHaveBeenCalledWith('Hello');
  });

  it('calls retryLastMessage when retry button is clicked', () => {
    const mockRetryLastMessage = jest.fn();
    mockUseChat.mockReturnValue({
      messages: [],
      isLoading: false,
      error: 'Connection failed. Please try again.',
      isRetrying: false,
      sendMessage: jest.fn(),
      retryLastMessage: mockRetryLastMessage,
      clearError: jest.fn(),
      clearMessages: jest.fn(),
    });

    render(<ChatInterface />);
    
    const retryButton = screen.getByText('Retry');
    fireEvent.click(retryButton);

    expect(mockRetryLastMessage).toHaveBeenCalled();
  });

  it('calls clearError when dismiss button is clicked', () => {
    const mockClearError = jest.fn();
    mockUseChat.mockReturnValue({
      messages: [],
      isLoading: false,
      error: 'Connection failed. Please try again.',
      isRetrying: false,
      sendMessage: jest.fn(),
      retryLastMessage: jest.fn(),
      clearError: mockClearError,
      clearMessages: jest.fn(),
    });

    render(<ChatInterface />);
    
    const dismissButton = screen.getByText('Dismiss');
    fireEvent.click(dismissButton);

    expect(mockClearError).toHaveBeenCalled();
  });
});