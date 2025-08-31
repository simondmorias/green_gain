import { useState, useCallback, useRef } from 'react';
import { ChatHookState, ChatHookActions, Message, ApiError } from '@/types/api';
import { chatApi } from '@/utils/api';

interface UseChatOptions {
  maxRetries?: number;
  conversationId?: string;
}

export function useChat(options: UseChatOptions = {}): ChatHookState & ChatHookActions {
  const { maxRetries = 3, conversationId = 'default' } = options;
  
  const [state, setState] = useState<ChatHookState>({
    messages: [],
    isLoading: false,
    error: null,
    isRetrying: false,
  });

  // Keep track of the last user message for retry functionality
  const lastUserMessageRef = useRef<string | null>(null);

  const generateMessageId = useCallback((): string => {
    return `msg_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
  }, []);

  const addMessage = useCallback((message: Omit<Message, 'id'>) => {
    const messageWithId: Message = {
      ...message,
      id: generateMessageId(),
    };

    setState(prev => ({
      ...prev,
      messages: [...prev.messages, messageWithId],
    }));

    return messageWithId;
  }, [generateMessageId]);

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  const clearMessages = useCallback(() => {
    setState(prev => ({
      ...prev,
      messages: [],
      error: null,
    }));
    lastUserMessageRef.current = null;
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) {
      return;
    }

    // Clear any previous errors
    clearError();
    
    // Store the user message for potential retry
    lastUserMessageRef.current = content.trim();

    // Add user message immediately (optimistic update)
    addMessage({
      content: content.trim(),
      role: 'user',
      timestamp: new Date(),
    });

    // Set loading state
    setState(prev => ({ ...prev, isLoading: true }));

    try {
      // Call API with retry logic
      const response = await chatApi.sendMessageWithRetry(
        {
          message: content.trim(),
          conversation_id: conversationId,
        },
        maxRetries
      );

      // Add assistant response
      addMessage({
        content: response.response,
        role: 'assistant',
        timestamp: new Date(response.timestamp),
      });

      setState(prev => ({ ...prev, isLoading: false }));
    } catch (error) {
      console.error('Error sending message:', error);
      
      let errorMessage = 'Sorry, there was an error processing your message. Please try again.';
      let canRetry = true;

      if (error instanceof ApiError) {
        switch (error.code) {
          case 'NETWORK_ERROR':
            errorMessage = 'Connection failed. Please check your internet connection and try again.';
            break;
          case 'TIMEOUT':
            errorMessage = 'Request timed out. Please try again.';
            break;
          case 'BAD_REQUEST':
            errorMessage = 'Invalid message format. Please try rephrasing your message.';
            canRetry = false;
            break;
          case 'RATE_LIMITED':
            errorMessage = 'Too many requests. Please wait a moment and try again.';
            break;
          case 'SERVER_ERROR':
            errorMessage = 'Server error. Please try again in a moment.';
            break;
          default:
            errorMessage = error.message;
        }
      }

      // Add error message to chat
      addMessage({
        content: errorMessage,
        role: 'assistant',
        timestamp: new Date(),
        isError: true,
        canRetry,
      });

      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
    }
  }, [conversationId, maxRetries, addMessage, clearError]);

  const retryLastMessage = useCallback(async () => {
    if (!lastUserMessageRef.current) {
      return;
    }

    setState(prev => ({ ...prev, isRetrying: true }));

    try {
      await sendMessage(lastUserMessageRef.current);
    } finally {
      setState(prev => ({ ...prev, isRetrying: false }));
    }
  }, [sendMessage]);

  return {
    // State
    messages: state.messages,
    isLoading: state.isLoading,
    error: state.error,
    isRetrying: state.isRetrying,
    
    // Actions
    sendMessage,
    retryLastMessage,
    clearError,
    clearMessages,
  };
}