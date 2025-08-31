import React, { useState } from 'react';
import { ChatInterfaceProps, Message, ChatState } from '@/types/chat';
import MessageList from './MessageList';
import MessageInput from './MessageInput';

const ChatInterface: React.FC<ChatInterfaceProps> = ({ className = '' }) => {
  const [chatState, setChatState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    error: null,
  });

  const generateMessageId = (): string => {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  };

  const handleSendMessage = async (content: string) => {
    // Clear any previous errors
    setChatState(prev => ({ ...prev, error: null }));

    // Add user message
    const userMessage: Message = {
      id: generateMessageId(),
      content,
      role: 'user',
      timestamp: new Date(),
    };

    setChatState(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      isLoading: true,
    }));

    try {
      // Call the API
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: content,
          conversation_id: 'default', // For now, use a default conversation ID
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Add assistant message
      const assistantMessage: Message = {
        id: generateMessageId(),
        content: data.response || 'Sorry, I could not process your request.',
        role: 'assistant',
        timestamp: new Date(),
      };

      setChatState(prev => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
        isLoading: false,
      }));
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Add error message
      const errorMessage: Message = {
        id: generateMessageId(),
        content: 'Sorry, there was an error processing your message. Please try again.',
        role: 'assistant',
        timestamp: new Date(),
      };

      setChatState(prev => ({
        ...prev,
        messages: [...prev.messages, errorMessage],
        isLoading: false,
        error: error instanceof Error ? error.message : 'An unknown error occurred',
      }));
    }
  };

  return (
    <div className={`flex flex-col h-full bg-white border border-gray-200 rounded-lg overflow-hidden shadow-lg ${className}`}>
      {/* Header */}
      <div className="bg-gray-50 border-b border-gray-200 p-4">
        <h2 className="text-xl font-semibold gradient-text">
          AI Assistant Chat
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          Ask me anything and I&apos;ll help you out!
        </p>
      </div>

      {/* Error Display */}
      {chatState.error && (
        <div className="bg-red-50 border-b border-red-200 p-3">
          <div className="text-red-600 text-sm">
            <strong>Error:</strong> {chatState.error}
          </div>
        </div>
      )}

      {/* Messages */}
      <MessageList 
        messages={chatState.messages} 
        isLoading={chatState.isLoading} 
      />

      {/* Input */}
      <MessageInput
        onSendMessage={handleSendMessage}
        isLoading={chatState.isLoading}
      />
    </div>
  );
};

export default ChatInterface;