import { ChatRequest, ChatResponse, ApiError } from '@/types/api';

export class ApiClient {
  private baseUrl: string;
  private timeout: number;

  constructor(baseUrl?: string, timeout: number = 30000) {
    this.baseUrl = baseUrl || process.env.NEXT_PUBLIC_API_URL || '';
    this.timeout = timeout;
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const url = this.baseUrl ? `${this.baseUrl}${endpoint}` : endpoint;
      
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorMessage = 'An error occurred';
        let errorCode = 'UNKNOWN_ERROR';

        try {
          const errorData = await response.json();
          errorMessage = errorData.message || errorData.error || errorMessage;
          errorCode = errorData.error || `HTTP_${response.status}`;
        } catch {
          // If we can't parse the error response, use status-based messages
          switch (response.status) {
            case 400:
              errorMessage = 'Invalid request. Please check your input.';
              errorCode = 'BAD_REQUEST';
              break;
            case 401:
              errorMessage = 'Authentication required.';
              errorCode = 'UNAUTHORIZED';
              break;
            case 403:
              errorMessage = 'Access denied.';
              errorCode = 'FORBIDDEN';
              break;
            case 404:
              errorMessage = 'Resource not found.';
              errorCode = 'NOT_FOUND';
              break;
            case 429:
              errorMessage = 'Too many requests. Please try again later.';
              errorCode = 'RATE_LIMITED';
              break;
            case 500:
              errorMessage = 'Server error. Please try again.';
              errorCode = 'SERVER_ERROR';
              break;
            default:
              errorMessage = `Request failed with status ${response.status}`;
              errorCode = `HTTP_${response.status}`;
          }
        }

        throw new ApiError(errorMessage, errorCode, response.status);
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof ApiError) {
        throw error;
      }

      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new ApiError(
            'Request timed out. Please try again.',
            'TIMEOUT',
            408
          );
        }

        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
          throw new ApiError(
            'Connection failed. Please check your internet connection and try again.',
            'NETWORK_ERROR',
            0
          );
        }
      }

      // Handle unknown error types
      const errorMessage = error instanceof Error ? error.message : 'An unexpected error occurred';
      throw new ApiError(
        `${errorMessage}. Please try again.`,
        'UNKNOWN_ERROR',
        0
      );
    }
  }

  async sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
    return this.makeRequest<ChatResponse>('/api/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Utility method for retrying failed requests
  async withRetry<T>(
    operation: () => Promise<T>,
    maxRetries: number = 3,
    delay: number = 1000
  ): Promise<T> {
    let lastError: Error;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error as Error;
        
        // Don't retry on client errors (4xx) except for 429 (rate limit)
        if (error instanceof ApiError && error.status >= 400 && error.status < 500 && error.status !== 429) {
          throw error;
        }

        if (attempt === maxRetries) {
          break;
        }

        // Exponential backoff
        const backoffDelay = delay * Math.pow(2, attempt - 1);
        await new Promise(resolve => setTimeout(resolve, backoffDelay));
      }
    }

    throw lastError!;
  }
}

// Default API client instance
export const apiClient = new ApiClient();

// Utility functions for common operations
export const chatApi = {
  sendMessage: (request: ChatRequest) => apiClient.sendChatMessage(request),
  sendMessageWithRetry: (request: ChatRequest, maxRetries?: number) =>
    apiClient.withRetry(() => apiClient.sendChatMessage(request), maxRetries),
};