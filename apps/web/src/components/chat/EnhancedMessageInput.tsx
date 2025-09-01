import React, { useState, KeyboardEvent, useEffect, useRef } from 'react';
import { MessageInputProps } from '@/types/chat';
import { Button } from '@/components/ui/button';
import { useEntityRecognition, useEntityInteraction } from '@/hooks/useEntityRecognition';
import { HighlightedText } from './HighlightedText';
import { RecognizedEntity } from '@/types/entities';

interface EnhancedMessageInputProps extends MessageInputProps {
  enableEntityRecognition?: boolean;
  showEntityPills?: boolean;
}

const EnhancedMessageInput: React.FC<EnhancedMessageInputProps> = ({ 
  onSendMessage, 
  isLoading, 
  disabled = false,
  enableEntityRecognition = true,
  showEntityPills = true,
}) => {
  const [message, setMessage] = useState('');
  const [showHighlights, setShowHighlights] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const highlightLayerRef = useRef<HTMLDivElement>(null);

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
    handleEntityClick,
    handleEntityRemove,
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

  const handleEntityClickInternal = (entity: RecognizedEntity) => {
    handleEntityClick(entity);
    // Optionally show entity details in a tooltip or modal
    // console.log('Entity clicked:', entity);
  };

  const isDisabled = isLoading || disabled || !message.trim();

  // Sync scroll position between textarea and highlight layer
  const handleScroll = () => {
    if (textareaRef.current && highlightLayerRef.current) {
      highlightLayerRef.current.scrollTop = textareaRef.current.scrollTop;
    }
  };

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

        {/* Message input with overlay for entity highlights */}
        <div className="flex items-end space-x-3">
          <div className="flex-1 relative">
            {/* Highlight overlay (behind textarea) */}
            {showHighlights && showEntityPills && entities.length > 0 && (
              <div
                ref={highlightLayerRef}
                className="absolute inset-0 pointer-events-none overflow-hidden"
                style={{
                  padding: '12px 16px',
                  paddingRight: '32px',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  lineHeight: '1.5',
                  fontSize: '14px',
                }}
              >
                <HighlightedText
                  text={message}
                  entities={entities}
                  onEntityClick={handleEntityClickInternal}
                  onEntityRemove={handleEntityRemove}
                  showConfidence={false}
                  isInteractive={false}
                />
              </div>
            )}

            {/* Textarea */}
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              onScroll={handleScroll}
              placeholder="Type your message here... (Press Enter to send, Shift+Enter for new line)"
              className={`w-full border border-gray-300 rounded-lg px-4 py-3 text-gray-900 placeholder-gray-500 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                showHighlights && entities.length > 0 ? 'bg-transparent' : 'bg-white'
              }`}
              style={{
                position: 'relative',
                zIndex: 1,
                backgroundColor: showHighlights && entities.length > 0 ? 'transparent' : 'white',
              }}
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