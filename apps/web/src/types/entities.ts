/**
 * Type definitions for entity recognition and highlighting
 */

export type EntityType = 
  | 'manufacturer'
  | 'brand'
  | 'product'
  | 'category'
  | 'metric'
  | 'time-period'
  | 'time_period';  // Support both formats

export interface EntityMetadata {
  display_name: string;
  full_name?: string;
  parent?: string;
  unit?: string;
  aggregation?: string;
  start_date?: string;
  end_date?: string;
}

export interface RecognizedEntity {
  text: string;
  type: EntityType;
  start: number;
  end: number;
  confidence: number;
  id?: string;
  metadata: EntityMetadata;
}

export interface EntityRecognitionResponse {
  tagged_text: string;
  entities: RecognizedEntity[];
  processing_time_ms: number;
  suggestions?: unknown[];
  error?: string;
}

export interface EntityRecognitionRequest {
  text: string;
  options?: {
    fuzzy_matching?: boolean;
    confidence_threshold?: number;
  };
}

export interface EntityPillProps {
  entity: RecognizedEntity;
  onClick?: (entity: RecognizedEntity) => void;
  onRemove?: (entity: RecognizedEntity) => void;
  showConfidence?: boolean;
  isInteractive?: boolean;
}

export interface HighlightedTextProps {
  text: string;
  entities: RecognizedEntity[];
  onEntityClick?: (entity: RecognizedEntity) => void;
  onEntityRemove?: (entity: RecognizedEntity) => void;
  showConfidence?: boolean;
  isInteractive?: boolean;
}

// Color mapping for entity types
export const ENTITY_COLORS: Record<string, { gradient: string; text: string }> = {
  manufacturer: {
    gradient: 'linear-gradient(135deg, #1FC1F0, #1821ED)',
    text: 'white',
  },
  brand: {
    gradient: 'linear-gradient(135deg, #1FC1F0, #1821ED)',
    text: 'white',
  },
  product: {
    gradient: 'linear-gradient(135deg, #10B981, #059669)',
    text: 'white',
  },
  category: {
    gradient: 'linear-gradient(135deg, #6B7280, #4B5563)',
    text: 'white',
  },
  metric: {
    gradient: 'linear-gradient(135deg, #A034F9, #7C3AED)',
    text: 'white',
  },
  'time-period': {
    gradient: 'linear-gradient(135deg, #FF8E00, #F59E0B)',
    text: 'white',
  },
  'time_period': {
    gradient: 'linear-gradient(135deg, #FF8E00, #F59E0B)',
    text: 'white',
  },
};