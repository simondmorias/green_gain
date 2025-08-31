import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ChatInterface from '../ChatInterface';

// Mock fetch
global.fetch = jest.fn();

describe('ChatInterface', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear();
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

  it('allows user to type and send message', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ response: 'Hello! How can I help you?' }),
    });

    render(<ChatInterface />);
    
    const textarea = screen.getByPlaceholderText(/Type your message here/);
    const sendButton = screen.getByText('Send');

    fireEvent.change(textarea, { target: { value: 'Hello' } });
    fireEvent.click(sendButton);

    expect(screen.getByText('You')).toBeInTheDocument();
    expect(screen.getByText('Hello')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Assistant')).toBeInTheDocument();
      expect(screen.getByText('Hello! How can I help you?')).toBeInTheDocument();
    });
  });

  it('shows loading state during API call', async () => {
    (fetch as jest.Mock).mockImplementationOnce(() => 
      new Promise(resolve => setTimeout(() => resolve({
        ok: true,
        json: async () => ({ response: 'Response' }),
      }), 100))
    );

    render(<ChatInterface />);
    
    const textarea = screen.getByPlaceholderText(/Type your message here/);
    const sendButton = screen.getByText('Send');

    fireEvent.change(textarea, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);

    expect(screen.getByText('Sending...')).toBeInTheDocument();
    expect(screen.getByText('Thinking...')).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(<ChatInterface />);
    
    const textarea = screen.getByPlaceholderText(/Type your message here/);
    const sendButton = screen.getByText('Send');

    fireEvent.change(textarea, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText('Sorry, there was an error processing your message. Please try again.')).toBeInTheDocument();
    });
  });
});