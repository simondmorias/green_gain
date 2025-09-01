import type { NextApiRequest, NextApiResponse } from 'next';
import { EntityRecognitionRequest, EntityRecognitionResponse } from '@/types/entities';

interface ErrorResponse {
  error: string;
  message: string;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<EntityRecognitionResponse | ErrorResponse>
) {
  if (req.method !== 'POST') {
    return res.status(405).json({
      error: 'Method not allowed',
      message: 'Only POST requests are supported'
    });
  }

  try {
    const { text, options }: EntityRecognitionRequest = req.body;

    if (!text || typeof text !== 'string') {
      return res.status(400).json({
        error: 'Invalid request',
        message: 'Text is required and must be a string'
      });
    }

    if (text.length > 500) {
      return res.status(400).json({
        error: 'Text too long',
        message: 'Text must be 500 characters or less'
      });
    }

    // Call the FastAPI backend for entity recognition
    const apiUrl = process.env.API_URL || 'http://localhost:8000';
    const response = await fetch(`${apiUrl}/api/chat/recognize-entities`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text,
        options: options || {},
      }),
    });

    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`);
    }

    const data: EntityRecognitionResponse = await response.json();

    return res.status(200).json(data);
  } catch (error) {
    console.error('Entity recognition API error:', error);
    
    return res.status(500).json({
      error: 'Internal server error',
      message: 'Failed to process entity recognition request. Please try again.'
    });
  }
}