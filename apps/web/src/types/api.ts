// API Request/Response Types
export interface ChatRequest {
  message: string;
  conversation_id?: string;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  timestamp: string;
}

export interface ApiErrorResponse {
  error: string;
  message: string;
}

// Custom API Error class
export class ApiError extends Error {
  public readonly code: string;
  public readonly status: number;

  constructor(message: string, code: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
  }
}

// API Client Configuration
export interface ApiClientConfig {
  baseUrl?: string;
  timeout?: number;
  retries?: number;
}

// Chat Hook State Types
export interface ChatHookState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  isRetrying: boolean;
}

export interface ChatHookActions {
  sendMessage: (content: string) => Promise<void>;
  retryLastMessage: () => Promise<void>;
  clearError: () => void;
  clearMessages: () => void;
}

// Re-export Message type from chat types for convenience
export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  isError?: boolean;
  canRetry?: boolean;
}