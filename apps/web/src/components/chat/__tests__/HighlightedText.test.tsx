import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { HighlightedText, HighlightedTaggedText } from '../HighlightedText';
import { RecognizedEntity } from '@/types/entities';

const mockEntities: RecognizedEntity[] = [
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
];

describe('HighlightedText', () => {
  it('renders plain text when no entities', () => {
    render(<HighlightedText text="Hello world" entities={[]} />);
    expect(screen.getByText('Hello world')).toBeInTheDocument();
  });

  it('renders text with entity pills', () => {
    render(
      <HighlightedText 
        text="Apple iPhone is great" 
        entities={mockEntities}
      />
    );
    
    expect(screen.getByText('Apple')).toBeInTheDocument();
    expect(screen.getByText('iPhone')).toBeInTheDocument();
    expect(screen.getByText(' is great')).toBeInTheDocument();
  });

  it('handles overlapping entities correctly', () => {
    const overlappingEntities: RecognizedEntity[] = [
      {
        text: 'Apple iPhone',
        type: 'product',
        start: 0,
        end: 12,
        confidence: 0.8,
        id: 'entity-1',
        metadata: { display_name: 'Apple iPhone' },
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
    ];

    render(
      <HighlightedText 
        text="Apple iPhone is great" 
        entities={overlappingEntities}
      />
    );
    
    // Should render the first entity (sorted by start position)
    expect(screen.getByText('Apple iPhone')).toBeInTheDocument();
  });

  it('calls onEntityClick when entity is clicked', () => {
    const mockOnClick = jest.fn();
    render(
      <HighlightedText 
        text="Apple iPhone" 
        entities={mockEntities}
        onEntityClick={mockOnClick}
      />
    );
    
    const appleEntity = screen.getByText('Apple');
    fireEvent.click(appleEntity);
    
    expect(mockOnClick).toHaveBeenCalledWith(mockEntities[0]);
  });

  it('calls onEntityRemove when entity remove is triggered', () => {
    const mockOnRemove = jest.fn();
    render(
      <HighlightedText 
        text="Apple iPhone" 
        entities={mockEntities}
        onEntityRemove={mockOnRemove}
      />
    );
    
    const removeButton = screen.getByLabelText('Remove Apple');
    fireEvent.click(removeButton);
    
    expect(mockOnRemove).toHaveBeenCalledWith(mockEntities[0]);
  });

  it('renders non-interactive pills when isInteractive is false', () => {
    render(
      <HighlightedText 
        text="Apple iPhone" 
        entities={mockEntities}
        isInteractive={false}
      />
    );
    
    const appleEntity = screen.getByText('Apple');
    expect(appleEntity.closest('[role="text"]')).toBeInTheDocument();
  });

  it('shows confidence when showConfidence is true', () => {
    const lowConfidenceEntity: RecognizedEntity = {
      ...mockEntities[0],
      confidence: 0.6,
    };

    render(
      <HighlightedText 
        text="Apple" 
        entities={[lowConfidenceEntity]}
        showConfidence={true}
      />
    );
    
    expect(screen.getByText('60%')).toBeInTheDocument();
  });

  it('handles empty entities array', () => {
    render(<HighlightedText text="Hello world" entities={[]} />);
    expect(screen.getByText('Hello world')).toBeInTheDocument();
  });

  it('handles entities at text boundaries', () => {
    const boundaryEntities: RecognizedEntity[] = [
      {
        text: 'Start',
        type: 'manufacturer',
        start: 0,
        end: 5,
        confidence: 0.9,
        id: 'entity-1',
        metadata: { display_name: 'Start' },
      },
      {
        text: 'End',
        type: 'product',
        start: 6,
        end: 9,
        confidence: 0.9,
        id: 'entity-2',
        metadata: { display_name: 'End' },
      },
    ];

    render(
      <HighlightedText 
        text="Start End" 
        entities={boundaryEntities}
      />
    );
    
    expect(screen.getByText('Start')).toBeInTheDocument();
    expect(screen.getByText('End')).toBeInTheDocument();
  });
});

describe('HighlightedTaggedText', () => {
  it('parses XML-style tagged text correctly', () => {
    const taggedText = '<manufacturer>Apple</manufacturer> <product>iPhone</product> is great';
    
    render(
      <HighlightedTaggedText 
        taggedText={taggedText}
        entities={mockEntities}
      />
    );
    
    expect(screen.getByText('Apple')).toBeInTheDocument();
    expect(screen.getByText('iPhone')).toBeInTheDocument();
    expect(screen.getByText(' is great')).toBeInTheDocument();
  });

  it('handles nested tags correctly', () => {
    const taggedText = 'The <manufacturer>Apple</manufacturer> <product>iPhone</product>';
    
    render(
      <HighlightedTaggedText 
        taggedText={taggedText}
        entities={mockEntities}
      />
    );
    
    expect(screen.getByText('The ')).toBeInTheDocument();
    expect(screen.getByText('Apple')).toBeInTheDocument();
    expect(screen.getByText(' ')).toBeInTheDocument();
    expect(screen.getByText('iPhone')).toBeInTheDocument();
  });

  it('handles text without tags', () => {
    const taggedText = 'Plain text without any tags';
    
    render(
      <HighlightedTaggedText 
        taggedText={taggedText}
        entities={[]}
      />
    );
    
    expect(screen.getByText('Plain text without any tags')).toBeInTheDocument();
  });

  it('handles hyphenated entity types', () => {
    const taggedText = '<time-period>Q1 2024</time-period>';
    const timePeriodEntity: RecognizedEntity = {
      text: 'Q1 2024',
      type: 'time-period',
      start: 0,
      end: 7,
      confidence: 0.9,
      id: 'entity-1',
      metadata: { display_name: 'Q1 2024' },
    };
    
    render(
      <HighlightedTaggedText 
        taggedText={taggedText}
        entities={[timePeriodEntity]}
      />
    );
    
    expect(screen.getByText('Q1 2024')).toBeInTheDocument();
  });

  it('creates fallback entities for unmatched tags', () => {
    const taggedText = '<category>Unknown Category</category>';
    
    render(
      <HighlightedTaggedText 
        taggedText={taggedText}
        entities={[]}
      />
    );
    
    expect(screen.getByText('Unknown Category')).toBeInTheDocument();
  });

  it('handles multiple instances of same entity type', () => {
    const taggedText = '<product>iPhone</product> and <product>iPad</product>';
    const entities: RecognizedEntity[] = [
      {
        text: 'iPhone',
        type: 'product',
        start: 0,
        end: 6,
        confidence: 0.9,
        id: 'entity-1',
        metadata: { display_name: 'iPhone' },
      },
      {
        text: 'iPad',
        type: 'product',
        start: 11,
        end: 15,
        confidence: 0.9,
        id: 'entity-2',
        metadata: { display_name: 'iPad' },
      },
    ];
    
    render(
      <HighlightedTaggedText 
        taggedText={taggedText}
        entities={entities}
      />
    );
    
    expect(screen.getByText('iPhone')).toBeInTheDocument();
    expect(screen.getByText('iPad')).toBeInTheDocument();
    expect(screen.getByText(' and ')).toBeInTheDocument();
  });
});