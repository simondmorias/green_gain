import React from 'react';
import { ChatInterfaceProps } from '@/types/chat';
import { useChat } from '@/hooks/useChat';
import MessageList from './MessageList';
import MessageInput from './MessageInput';

const ChatInterface: React.FC<ChatInterfaceProps> = ({ className = '' }) => {
  const {
    messages,
    isLoading,
    error,
    isRetrying,
    sendMessage,
    retryLastMessage,
    clearError,
  } = useChat({
    maxRetries: 3,
    conversationId: 'default',
  });

  const handleSendMessage = async (content: string) => {
    await sendMessage(content);
  };

  const handleRetry = async () => {
    await retryLastMessage();
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

      {/* Error Display with Retry Option */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 p-3">
          <div className="flex items-center justify-between">
            <div className="text-red-600 text-sm">
              <strong>Error:</strong> {error}
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleRetry}
                disabled={isRetrying}
                className="text-xs bg-red-100 hover:bg-red-200 text-red-700 px-2 py-1 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isRetrying ? 'Retrying...' : 'Retry'}
              </button>
              <button
                onClick={clearError}
                className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-2 py-1 rounded"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <MessageList 
        messages={messages} 
        isLoading={isLoading || isRetrying}
        onRetry={handleRetry}
      />

      {/* Input */}
      <MessageInput
        onSendMessage={handleSendMessage}
        isLoading={isLoading || isRetrying}
      />
    </div>
  );
};

export default ChatInterface;