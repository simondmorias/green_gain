/**
 * Entity Recognition API client service
 */

import { 
  EntityRecognitionRequest, 
  EntityRecognitionResponse 
} from '../types/entities';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Simple in-memory cache for entity recognition results
const responseCache = new Map<string, { data: EntityRecognitionResponse; timestamp: number }>();
const CACHE_TTL = 15 * 60 * 1000; // 15 minutes

export class EntityApiService {
  private abortController: AbortController | null = null;

  /**
   * Recognize entities in text with caching and retry logic
   */
  async recognizeEntities(
    request: EntityRecognitionRequest,
    maxRetries: number = 3
  ): Promise<EntityRecognitionResponse> {
    // Check cache first
    const cacheKey = this.getCacheKey(request);
    const cached = this.getFromCache(cacheKey);
    if (cached) {
      return cached;
    }

    // Cancel any pending request
    this.cancelPendingRequest();

    // Create new abort controller
    this.abortController = new AbortController();

    let lastError: Error | null = null;

    // Retry logic
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const response = await this.makeRequest(request, this.abortController.signal);
        
        // Cache successful response
        this.saveToCache(cacheKey, response);
        
        return response;
      } catch (error: unknown) {
        // Don't retry on abort
        if (error instanceof Error && error.name === 'AbortError') {
          throw error;
        }

        lastError = error instanceof Error ? error : new Error('Unknown error');

        // Don't retry on client errors (4xx)
        if (error && typeof error === 'object' && 'status' in error) {
          const status = (error as { status: number }).status;
          if (status >= 400 && status < 500) {
            throw error;
          }
        }

        // Wait before retrying (exponential backoff)
        if (attempt < maxRetries) {
          await this.sleep(Math.pow(2, attempt - 1) * 1000);
        }
      }
    }

    // All retries failed
    throw lastError || new Error('Entity recognition failed after retries');
  }

  /**
   * Make the actual API request
   */
  private async makeRequest(
    request: EntityRecognitionRequest,
    signal: AbortSignal
  ): Promise<EntityRecognitionResponse> {
    const response = await fetch(`${API_BASE_URL}/api/chat/recognize-entities`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
      signal,
    });

    if (!response.ok) {
      const error = new Error(`Recognition failed: ${response.statusText}`) as Error & { status: number };
      error.status = response.status;
      throw error;
    }

    const data: EntityRecognitionResponse = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    return data;
  }

  /**
   * Cancel any pending request
   */
  cancelPendingRequest(): void {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }

  /**
   * Get cache key for request
   */
  private getCacheKey(request: EntityRecognitionRequest): string {
    return JSON.stringify({
      text: request.text,
      options: request.options,
    });
  }

  /**
   * Get from cache if valid
   */
  private getFromCache(key: string): EntityRecognitionResponse | null {
    const cached = responseCache.get(key);
    
    if (!cached) {
      return null;
    }

    // Check if cache is still valid
    if (Date.now() - cached.timestamp > CACHE_TTL) {
      responseCache.delete(key);
      return null;
    }

    return cached.data;
  }

  /**
   * Save to cache
   */
  private saveToCache(key: string, data: EntityRecognitionResponse): void {
    // Limit cache size
    if (responseCache.size > 100) {
      // Remove oldest entries
      const entriesToRemove = Array.from(responseCache.entries())
        .sort((a, b) => a[1].timestamp - b[1].timestamp)
        .slice(0, 50);
      
      entriesToRemove.forEach(([key]) => responseCache.delete(key));
    }

    responseCache.set(key, {
      data,
      timestamp: Date.now(),
    });
  }

  /**
   * Clear the cache
   */
  clearCache(): void {
    responseCache.clear();
  }

  /**
   * Sleep for specified milliseconds
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Singleton instance
let apiInstance: EntityApiService | null = null;

export function getEntityApiService(): EntityApiService {
  if (!apiInstance) {
    apiInstance = new EntityApiService();
  }
  return apiInstance;
}

// Convenience functions
export async function recognizeEntities(
  text: string,
  options?: EntityRecognitionRequest['options']
): Promise<EntityRecognitionResponse> {
  const service = getEntityApiService();
  return service.recognizeEntities({ text, options });
}

export function cancelPendingRecognition(): void {
  const service = getEntityApiService();
  service.cancelPendingRequest();
}

export function clearEntityCache(): void {
  const service = getEntityApiService();
  service.clearCache();
}