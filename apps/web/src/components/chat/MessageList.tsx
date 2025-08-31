import React, { useEffect, useRef } from 'react';
import { MessageListProps } from '@/types/chat';
import MessageBubble from './MessageBubble';

const MessageList: React.FC<MessageListProps> = ({ messages, isLoading, onRetry }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.length === 0 ? (
        <div className="flex items-center justify-center h-full">
          <div className="text-center text-gray-500">
            <div className="text-6xl mb-4">💬</div>
            <h3 className="text-xl font-semibold mb-2 text-gray-900">Start a conversation</h3>
            <p className="text-gray-600">
              Type a message below to begin chatting with the AI assistant.
            </p>
          </div>
        </div>
      ) : (
        <>
          {messages.map((message) => (
            <MessageBubble 
              key={message.id} 
              message={message} 
              onRetry={message.isError && message.canRetry ? onRetry : undefined}
            />
          ))}
          {isLoading && (
            <div className="flex justify-start mb-4">
              <div className="max-w-[70%] px-4 py-3 rounded-lg bg-gray-50 text-gray-900 rounded-bl-sm border border-gray-200 shadow-sm">
                <div className="text-sm font-medium mb-1 text-gray-600">Assistant</div>
                <div className="flex items-center space-x-2">
                  <div className="loading-spinner"></div>
                  <span className="text-gray-500">Thinking...</span>
                </div>
              </div>
            </div>
          )}
        </>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;