import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  EntityRecognitionRequest, 
  EntityRecognitionResponse, 
  RecognizedEntity 
} from '../types/entities';

interface UseEntityRecognitionOptions {
  debounceMs?: number;
  enabled?: boolean;
  fuzzyMatching?: boolean;
  confidenceThreshold?: number;
  apiEndpoint?: string;
}

interface UseEntityRecognitionReturn {
  entities: RecognizedEntity[];
  taggedText: string;
  isLoading: boolean;
  error: string | null;
  processingTime: number;
  recognize: (text: string) => void;
  clear: () => void;
}

/**
 * Custom hook for entity recognition with debouncing
 */
export function useEntityRecognition(
  options: UseEntityRecognitionOptions = {}
): UseEntityRecognitionReturn {
  const {
    debounceMs = 500,
    enabled = true,
    fuzzyMatching = false,
    confidenceThreshold = 0.8,
    apiEndpoint = '/api/chat/recognize-entities',
  } = options;

  const [entities, setEntities] = useState<RecognizedEntity[]>([]);
  const [taggedText, setTaggedText] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [processingTime, setProcessingTime] = useState<number>(0);

  const debounceTimer = useRef<NodeJS.Timeout | null>(null);
  const abortController = useRef<AbortController | null>(null);

  /**
   * Perform entity recognition API call
   */
  const performRecognition = useCallback(
    async (text: string) => {
      if (!enabled || !text.trim()) {
        setEntities([]);
        setTaggedText(text);
        return;
      }

      // Cancel previous request if still pending
      if (abortController.current) {
        abortController.current.abort();
      }

      // Create new abort controller for this request
      abortController.current = new AbortController();

      setIsLoading(true);
      setError(null);

      try {
        const request: EntityRecognitionRequest = {
          text,
          options: {
            fuzzy_matching: fuzzyMatching,
            confidence_threshold: confidenceThreshold,
          },
        };

        const response = await fetch(apiEndpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(request),
          signal: abortController.current.signal,
        });

        if (!response.ok) {
          throw new Error(`Recognition failed: ${response.statusText}`);
        }

        const data: EntityRecognitionResponse = await response.json();

        if (data.error) {
          throw new Error(data.error);
        }

        setEntities(data.entities || []);
        setTaggedText(data.tagged_text || text);
        setProcessingTime(data.processing_time_ms || 0);
      } catch (err: unknown) {
        // Ignore abort errors
        if (err instanceof Error && err.name === 'AbortError') {
          return;
        }

        const errorMessage = err instanceof Error ? err.message : 'Entity recognition failed';
        setError(errorMessage);
        setEntities([]);
        setTaggedText(text);
      } finally {
        setIsLoading(false);
        abortController.current = null;
      }
    },
    [enabled, fuzzyMatching, confidenceThreshold, apiEndpoint]
  );

  /**
   * Debounced recognition function
   */
  const recognize = useCallback(
    (text: string) => {
      // Clear existing timer
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }

      // Set new timer
      debounceTimer.current = setTimeout(() => {
        performRecognition(text);
      }, debounceMs);
    },
    [performRecognition, debounceMs]
  );

  /**
   * Clear all entities and reset state
   */
  const clear = useCallback(() => {
    // Cancel any pending requests
    if (abortController.current) {
      abortController.current.abort();
    }

    // Clear debounce timer
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    // Reset state
    setEntities([]);
    setTaggedText('');
    setIsLoading(false);
    setError(null);
    setProcessingTime(0);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
      if (abortController.current) {
        abortController.current.abort();
      }
    };
  }, []);

  return {
    entities,
    taggedText,
    isLoading,
    error,
    processingTime,
    recognize,
    clear,
  };
}

/**
 * Hook for managing entity selection and interaction
 */
export function useEntityInteraction() {
  const [selectedEntity, setSelectedEntity] = useState<RecognizedEntity | null>(null);
  const [removedEntities, setRemovedEntities] = useState<Set<string>>(new Set());

  const handleEntityClick = useCallback((entity: RecognizedEntity) => {
    setSelectedEntity(entity);
    // You can add more logic here, like showing entity details
    // console.log('Entity clicked:', entity);
  }, []);

  const handleEntityRemove = useCallback((entity: RecognizedEntity) => {
    const entityKey = `${entity.start}-${entity.end}`;
    setRemovedEntities(prev => new Set(prev).add(entityKey));
    // console.log('Entity removed:', entity);
  }, []);

  const resetRemovedEntities = useCallback(() => {
    setRemovedEntities(new Set());
  }, []);

  const isEntityRemoved = useCallback(
    (entity: RecognizedEntity) => {
      const entityKey = `${entity.start}-${entity.end}`;
      return removedEntities.has(entityKey);
    },
    [removedEntities]
  );

  return {
    selectedEntity,
    removedEntities,
    handleEntityClick,
    handleEntityRemove,
    resetRemovedEntities,
    isEntityRemoved,
  };
}