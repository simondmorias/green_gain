export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  isError?: boolean;
  canRetry?: boolean;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
}

export interface MessageInputProps {
  onSendMessage: (content: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export interface MessageBubbleProps {
  message: Message;
  onRetry?: () => void;
}

export interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
  onRetry?: () => void;
}

export interface ChatInterfaceProps {
  className?: string;
}