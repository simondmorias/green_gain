import React from 'react';
import { MessageBubbleProps } from '@/types/chat';

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, onRetry }) => {
  const isUser = message.role === 'user';
  const isError = message.isError;
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[70%] px-4 py-3 rounded-lg shadow-sm ${
          isUser
            ? 'gradient-bg text-white rounded-br-sm'
            : isError
            ? 'bg-red-50 text-red-900 rounded-bl-sm border border-red-200'
            : 'bg-gray-50 text-gray-900 rounded-bl-sm border border-gray-200'
        }`}
      >
        <div className={`text-sm font-medium mb-1 ${
          isUser 
            ? 'text-white/90' 
            : isError 
            ? 'text-red-600' 
            : 'text-gray-600'
        }`}>
          {isUser ? 'You' : isError ? 'Error' : 'Assistant'}
        </div>
        <div className="text-base leading-relaxed whitespace-pre-wrap">
          {message.content}
        </div>
        <div className="flex items-center justify-between mt-2">
          <div className={`text-xs ${
            isUser 
              ? 'text-white/70' 
              : isError 
              ? 'text-red-500' 
              : 'text-gray-500'
          }`}>
            {message.timestamp.toLocaleTimeString([], { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </div>
          {isError && message.canRetry && onRetry && (
            <button
              onClick={onRetry}
              className="text-xs bg-red-100 hover:bg-red-200 text-red-700 px-2 py-1 rounded transition-colors"
            >
              Retry
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;