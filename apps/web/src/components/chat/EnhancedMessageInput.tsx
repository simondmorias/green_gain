import React, { useState, KeyboardEvent, useEffect, useRef } from 'react';
import { MessageInputProps } from '@/types/chat';
import { Button } from '@/components/ui/button';
import { useEntityRecognition, useEntityInteraction } from '@/hooks/useEntityRecognition';

interface EnhancedMessageInputProps extends MessageInputProps {
  enableEntityRecognition?: boolean;
}

const EnhancedMessageInput: React.FC<EnhancedMessageInputProps> = ({ 
  onSendMessage, 
  isLoading, 
  disabled = false,
  enableEntityRecognition = true,
}) => {
  const [message, setMessage] = useState('');
  const [showHighlights, setShowHighlights] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Entity recognition hook
  const {
    entities,
    isLoading: isRecognizing,
    error: recognitionError,
    processingTime,
    recognize,
    clear: clearRecognition,
  } = useEntityRecognition({
    enabled: enableEntityRecognition,
    debounceMs: 500,
  });

  // Entity interaction hook
  const {
    selectedEntity,
    resetRemovedEntities,
  } = useEntityInteraction();

  // Trigger entity recognition when message changes
  useEffect(() => {
    if (enableEntityRecognition && message) {
      recognize(message);
      setShowHighlights(true);
    } else {
      clearRecognition();
      setShowHighlights(false);
    }
  }, [message, enableEntityRecognition, recognize, clearRecognition]);

  const handleSend = () => {
    const trimmedMessage = message.trim();
    if (trimmedMessage && !isLoading && !disabled) {
      onSendMessage(trimmedMessage);
      setMessage('');
      clearRecognition();
      resetRemovedEntities();
      setShowHighlights(false);
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
      <div className="flex flex-col space-y-3">
        {/* Entity recognition status */}
        {enableEntityRecognition && message && (
          <div className="flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center space-x-2">
              {isRecognizing && (
                <span className="flex items-center">
                  <div className="loading-spinner-small mr-1"></div>
                  Recognizing entities...
                </span>
              )}
              {!isRecognizing && entities.length > 0 && (
                <span>
                  Found {entities.length} {entities.length === 1 ? 'entity' : 'entities'}
                  {processingTime > 0 && ` (${Math.round(processingTime)}ms)`}
                </span>
              )}
              {recognitionError && (
                <span className="text-red-500">Recognition error: {recognitionError}</span>
              )}
            </div>
            {entities.length > 0 && (
              <button
                onClick={() => setShowHighlights(!showHighlights)}
                className="text-blue-500 hover:text-blue-600"
              >
                {showHighlights ? 'Hide' : 'Show'} highlights
              </button>
            )}
          </div>
        )}



        {/* Message input */}
        <div className="flex items-end space-x-3">
          <div className="flex-1">
            {/* Recognized entities display */}
            {showHighlights && entities.length > 0 && (
              <div className="mb-2 px-2 py-1 text-xs text-gray-600">
                <span className="inline-flex items-center gap-2">
                  <span>Recognized:</span>
                  {entities.map((entity, index) => (
                    <span
                      key={`${entity.type}-${entity.start}-${index}`}
                      className="font-semibold text-blue-600"
                      title={`${entity.type}: ${entity.text}`}
                    >
                      {entity.text}
                    </span>
                  ))}
                </span>
              </div>
            )}
            
            {/* Textarea */}
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message here... (Press Enter to send, Shift+Enter for new line)"
              className="w-full border border-gray-300 rounded-lg px-4 py-3 text-gray-900 placeholder-gray-500 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
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

        {/* Selected entity details */}
        {selectedEntity && (
          <div className="p-2 bg-gray-50 rounded-lg text-sm">
            <div className="font-semibold">{selectedEntity.type}: {selectedEntity.text}</div>
            {selectedEntity.metadata.full_name && (
              <div className="text-gray-600">Full name: {selectedEntity.metadata.full_name}</div>
            )}
            {selectedEntity.confidence < 1 && (
              <div className="text-gray-500">
                Confidence: {Math.round(selectedEntity.confidence * 100)}%
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default EnhancedMessageInput;