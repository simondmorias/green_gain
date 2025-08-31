import React from 'react';
import { MessageBubbleProps } from '@/types/chat';

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[70%] px-4 py-3 rounded-lg shadow-sm ${
          isUser
            ? 'gradient-bg text-white rounded-br-sm'
            : 'bg-gray-50 text-gray-900 rounded-bl-sm border border-gray-200'
        }`}
      >
        <div className={`text-sm font-medium mb-1 ${
          isUser ? 'text-white/90' : 'text-gray-600'
        }`}>
          {isUser ? 'You' : 'Assistant'}
        </div>
        <div className="text-base leading-relaxed whitespace-pre-wrap">
          {message.content}
        </div>
        <div className={`text-xs mt-2 ${
          isUser ? 'text-white/70' : 'text-gray-500'
        }`}>
          {message.timestamp.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;