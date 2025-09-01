import { renderHook, waitFor } from '@testing-library/react';
import { useEntityRecognition, useEntityInteraction } from '../useEntityRecognition';
import { RecognizedEntity } from '@/types/entities';

// Mock fetch
global.fetch = jest.fn();

const mockResponse = {
  tagged_text: '<manufacturer>Apple</manufacturer> <product>iPhone</product>',
  entities: [
    {
      text: 'Apple',
      type: 'manufacturer',
      start: 0,
      end: 5,
      confidence: 0.95,
      id: 'entity-1',
      metadata: { display_name: 'Apple Inc.' },
    },
    {
      text: 'iPhone',
      type: 'product',
      start: 6,
      end: 12,
      confidence: 0.9,
      id: 'entity-2',
      metadata: { display_name: 'iPhone' },
    },
  ] as RecognizedEntity[],
  processing_time_ms: 150,
};

describe('useEntityRecognition', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('initializes with empty state', () => {
    const { result } = renderHook(() => useEntityRecognition());

    expect(result.current.entities).toEqual([]);
    expect(result.current.taggedText).toBe('');
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe(null);
    expect(result.current.processingTime).toBe(0);
  });

  it('performs entity recognition successfully', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const { result } = renderHook(() => useEntityRecognition());

    result.current.recognize('Apple iPhone');

    // Fast-forward debounce timer
    jest.advanceTimersByTime(500);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.entities).toEqual(mockResponse.entities);
    expect(result.current.taggedText).toBe(mockResponse.tagged_text);
    expect(result.current.processingTime).toBe(150);
    expect(result.current.error).toBe(null);
  });

  it('debounces recognition calls', async () => {
    (fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    });

    const { result } = renderHook(() => useEntityRecognition({ debounceMs: 300 }));

    // Make multiple rapid calls
    result.current.recognize('A');
    result.current.recognize('Ap');
    result.current.recognize('App');
    result.current.recognize('Apple');

    // Should not have called fetch yet
    expect(fetch).not.toHaveBeenCalled();

    // Fast-forward debounce timer
    jest.advanceTimersByTime(300);

    // Should only call fetch once with the last value
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(1);
    });

    expect(fetch).toHaveBeenCalledWith('/api/chat/recognize-entities', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: 'Apple',
        options: {
          fuzzy_matching: false,
          confidence_threshold: 0.8,
        },
      }),
      signal: expect.any(AbortSignal),
    });
  });

  it('handles API errors gracefully', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      statusText: 'Internal Server Error',
    });

    const { result } = renderHook(() => useEntityRecognition());

    result.current.recognize('Apple iPhone');
    jest.advanceTimersByTime(500);

    await waitFor(() => {
      expect(result.current.error).toBe('Recognition failed: Internal Server Error');
    });

    expect(result.current.entities).toEqual([]);
    expect(result.current.isLoading).toBe(false);
  });

  it('handles network errors', async () => {
    (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useEntityRecognition());

    result.current.recognize('Apple iPhone');
    jest.advanceTimersByTime(500);

    await waitFor(() => {
      expect(result.current.error).toBe('Network error');
    });

    expect(result.current.entities).toEqual([]);
    expect(result.current.isLoading).toBe(false);
  });

  it('cancels previous requests when new ones are made', async () => {
    const abortSpy = jest.fn();
    const mockAbortController = {
      abort: abortSpy,
      signal: {} as AbortSignal,
    };

    jest.spyOn(window, 'AbortController').mockImplementation(() => mockAbortController as AbortController);

    (fetch as jest.Mock).mockImplementation(() => new Promise(() => {})); // Never resolves

    const { result } = renderHook(() => useEntityRecognition());

    // First call
    result.current.recognize('Apple');
    jest.advanceTimersByTime(500);

    // Second call should cancel the first
    result.current.recognize('Apple iPhone');
    jest.advanceTimersByTime(500);

    expect(abortSpy).toHaveBeenCalled();
  });

  it('clears state when clear is called', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const { result } = renderHook(() => useEntityRecognition());

    // First recognize some text
    result.current.recognize('Apple iPhone');
    jest.advanceTimersByTime(500);

    await waitFor(() => {
      expect(result.current.entities.length).toBeGreaterThan(0);
    });

    // Then clear
    result.current.clear();

    expect(result.current.entities).toEqual([]);
    expect(result.current.taggedText).toBe('');
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe(null);
    expect(result.current.processingTime).toBe(0);
  });

  it('handles empty text input', () => {
    const { result } = renderHook(() => useEntityRecognition());

    result.current.recognize('');
    jest.advanceTimersByTime(500);

    expect(fetch).not.toHaveBeenCalled();
    expect(result.current.entities).toEqual([]);
  });

  it('respects enabled option', () => {
    const { result } = renderHook(() => useEntityRecognition({ enabled: false }));

    result.current.recognize('Apple iPhone');
    jest.advanceTimersByTime(500);

    expect(fetch).not.toHaveBeenCalled();
    expect(result.current.entities).toEqual([]);
  });

  it('uses custom API endpoint', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const { result } = renderHook(() => 
      useEntityRecognition({ apiEndpoint: '/custom/endpoint' })
    );

    result.current.recognize('Apple iPhone');
    jest.advanceTimersByTime(500);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/custom/endpoint', expect.any(Object));
    });
  });

  it('passes fuzzy matching and confidence threshold options', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const { result } = renderHook(() => 
      useEntityRecognition({ 
        fuzzyMatching: true, 
        confidenceThreshold: 0.7 
      })
    );

    result.current.recognize('Apple iPhone');
    jest.advanceTimersByTime(500);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/chat/recognize-entities', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: 'Apple iPhone',
          options: {
            fuzzy_matching: true,
            confidence_threshold: 0.7,
          },
        }),
        signal: expect.any(AbortSignal),
      });
    });
  });
});

describe('useEntityInteraction', () => {
  const mockEntity: RecognizedEntity = {
    text: 'Apple',
    type: 'manufacturer',
    start: 0,
    end: 5,
    confidence: 0.95,
    id: 'entity-1',
    metadata: { display_name: 'Apple Inc.' },
  };

  it('initializes with empty state', () => {
    const { result } = renderHook(() => useEntityInteraction());

    expect(result.current.selectedEntity).toBe(null);
    expect(result.current.removedEntities.size).toBe(0);
  });

  it('handles entity click', () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
    const { result } = renderHook(() => useEntityInteraction());

    result.current.handleEntityClick(mockEntity);

    expect(result.current.selectedEntity).toBe(mockEntity);
    expect(consoleSpy).toHaveBeenCalledWith('Entity clicked:', mockEntity);

    consoleSpy.mockRestore();
  });

  it('handles entity removal', () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
    const { result } = renderHook(() => useEntityInteraction());

    result.current.handleEntityRemove(mockEntity);

    expect(result.current.isEntityRemoved(mockEntity)).toBe(true);
    expect(consoleSpy).toHaveBeenCalledWith('Entity removed:', mockEntity);

    consoleSpy.mockRestore();
  });

  it('resets removed entities', () => {
    const { result } = renderHook(() => useEntityInteraction());

    // First remove an entity
    result.current.handleEntityRemove(mockEntity);
    expect(result.current.isEntityRemoved(mockEntity)).toBe(true);

    // Then reset
    result.current.resetRemovedEntities();

    expect(result.current.isEntityRemoved(mockEntity)).toBe(false);
    expect(result.current.removedEntities.size).toBe(0);
  });

  it('tracks multiple removed entities', () => {
    const { result } = renderHook(() => useEntityInteraction());

    const entity2: RecognizedEntity = {
      ...mockEntity,
      text: 'iPhone',
      start: 6,
      end: 12,
      id: 'entity-2',
    };

    result.current.handleEntityRemove(mockEntity);
    result.current.handleEntityRemove(entity2);

    expect(result.current.isEntityRemoved(mockEntity)).toBe(true);
    expect(result.current.isEntityRemoved(entity2)).toBe(true);
    expect(result.current.removedEntities.size).toBe(2);
  });
});