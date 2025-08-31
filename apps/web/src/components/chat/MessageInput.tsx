import React, { useState, KeyboardEvent } from 'react';
import { MessageInputProps } from '@/types/chat';
import { Button } from '@/components/ui/button';

const MessageInput: React.FC<MessageInputProps> = ({ 
  onSendMessage, 
  isLoading, 
  disabled = false 
}) => {
  const [message, setMessage] = useState('');

  const handleSend = () => {
    const trimmedMessage = message.trim();
    if (trimmedMessage && !isLoading && !disabled) {
      onSendMessage(trimmedMessage);
      setMessage('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isDisabled = isLoading || disabled || !message.trim();

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      <div className="flex items-end space-x-3">
        <div className="flex-1">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message here... (Press Enter to send, Shift+Enter for new line)"
            className="w-full bg-white border border-gray-300 rounded-lg px-4 py-3 text-gray-900 placeholder-gray-500 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            rows={3}
            disabled={disabled}
            maxLength={2000}
          />
          <div className="text-xs text-gray-500 mt-1 text-right">
            {message.length}/2000
          </div>
        </div>
        <Button
          onClick={handleSend}
          disabled={isDisabled}
          className="min-w-[100px] h-12"
        >
          {isLoading ? (
            <>
              <div className="loading-spinner mr-2"></div>
              Sending...
            </>
          ) : (
            'Send'
          )}
        </Button>
      </div>
    </div>
  );
};

export default MessageInput;