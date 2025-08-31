import type { NextApiRequest, NextApiResponse } from 'next';

interface ChatRequest {
  message: string;
  conversation_id: string;
}

interface ChatResponse {
  response: string;
  conversation_id: string;
  timestamp: string;
}

interface ErrorResponse {
  error: string;
  message: string;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ChatResponse | ErrorResponse>
) {
  if (req.method !== 'POST') {
    return res.status(405).json({
      error: 'Method not allowed',
      message: 'Only POST requests are supported'
    });
  }

  try {
    const { message, conversation_id }: ChatRequest = req.body;

    if (!message || typeof message !== 'string') {
      return res.status(400).json({
        error: 'Invalid request',
        message: 'Message is required and must be a string'
      });
    }

    if (message.length > 2000) {
      return res.status(400).json({
        error: 'Message too long',
        message: 'Message must be 2000 characters or less'
      });
    }

    // Call the FastAPI backend
    const apiUrl = process.env.API_URL || 'http://localhost:8000';
    const response = await fetch(`${apiUrl}/api/chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
      }),
    });

    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`);
    }

    const data = await response.json();

    return res.status(200).json({
      response: data.response,
      conversation_id: conversation_id || 'default',
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Chat API error:', error);
    
    return res.status(500).json({
      error: 'Internal server error',
      message: 'Failed to process chat request. Please try again.'
    });
  }
}