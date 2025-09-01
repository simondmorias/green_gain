import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { EntityPill } from '../EntityPill';
import { RecognizedEntity } from '@/types/entities';

const mockEntity: RecognizedEntity = {
  text: 'Apple',
  type: 'manufacturer',
  start: 0,
  end: 5,
  confidence: 0.95,
  id: 'entity-1',
  metadata: {
    display_name: 'Apple Inc.',
    full_name: 'Apple Inc.',
  },
};

const lowConfidenceEntity: RecognizedEntity = {
  ...mockEntity,
  confidence: 0.6,
};

describe('EntityPill', () => {
  it('renders entity text correctly', () => {
    render(<EntityPill entity={mockEntity} />);
    expect(screen.getByText('Apple')).toBeInTheDocument();
  });

  it('applies correct ARIA label', () => {
    render(<EntityPill entity={mockEntity} showConfidence />);
    const pill = screen.getByRole('button');
    expect(pill).toHaveAttribute('aria-label', 'manufacturer: Apple (95% confidence)');
  });

  it('shows confidence for low confidence entities', () => {
    render(<EntityPill entity={lowConfidenceEntity} showConfidence />);
    expect(screen.getByText('60%')).toBeInTheDocument();
  });

  it('applies uncertain styling for low confidence entities', () => {
    render(<EntityPill entity={lowConfidenceEntity} />);
    const pill = screen.getByRole('button');
    expect(pill).toHaveClass('entityPillUncertain');
  });

  it('calls onClick when clicked', () => {
    const mockOnClick = jest.fn();
    render(<EntityPill entity={mockEntity} onClick={mockOnClick} />);
    
    const pill = screen.getByRole('button');
    fireEvent.click(pill);
    
    expect(mockOnClick).toHaveBeenCalledWith(mockEntity);
  });

  it('calls onRemove when remove button is clicked', () => {
    const mockOnRemove = jest.fn();
    render(<EntityPill entity={mockEntity} onRemove={mockOnRemove} />);
    
    const removeButton = screen.getByLabelText('Remove Apple');
    fireEvent.click(removeButton);
    
    expect(mockOnRemove).toHaveBeenCalledWith(mockEntity);
  });

  it('handles keyboard navigation - Enter key', () => {
    const mockOnClick = jest.fn();
    render(<EntityPill entity={mockEntity} onClick={mockOnClick} />);
    
    const pill = screen.getByRole('button');
    fireEvent.keyDown(pill, { key: 'Enter' });
    
    expect(mockOnClick).toHaveBeenCalledWith(mockEntity);
  });

  it('handles keyboard navigation - Delete key', () => {
    const mockOnRemove = jest.fn();
    render(<EntityPill entity={mockEntity} onRemove={mockOnRemove} />);
    
    const pill = screen.getByRole('button');
    fireEvent.keyDown(pill, { key: 'Delete' });
    
    expect(mockOnRemove).toHaveBeenCalledWith(mockEntity);
  });

  it('renders as non-interactive when isInteractive is false', () => {
    render(<EntityPill entity={mockEntity} isInteractive={false} />);
    const pill = screen.getByRole('text');
    expect(pill).toHaveAttribute('tabIndex', '-1');
    expect(pill).not.toHaveClass('entityPillInteractive');
  });

  it('applies correct data attributes', () => {
    render(<EntityPill entity={mockEntity} />);
    const pill = screen.getByRole('button');
    
    expect(pill).toHaveAttribute('data-entity-type', 'manufacturer');
    expect(pill).toHaveAttribute('data-entity-id', 'entity-1');
    expect(pill).toHaveAttribute('data-confidence', '0.95');
  });

  it('renders different entity types with correct styling', () => {
    const productEntity: RecognizedEntity = {
      ...mockEntity,
      type: 'product',
      text: 'iPhone',
    };

    render(<EntityPill entity={productEntity} />);
    const pill = screen.getByRole('button');
    expect(pill).toHaveClass('entityPill--product');
  });

  it('handles time-period entity type normalization', () => {
    const timePeriodEntity: RecognizedEntity = {
      ...mockEntity,
      type: 'time_period',
      text: 'Q1 2024',
    };

    render(<EntityPill entity={timePeriodEntity} />);
    const pill = screen.getByRole('button');
    expect(pill).toHaveClass('entityPill--time-period');
  });

  it('does not show remove button when onRemove is not provided', () => {
    render(<EntityPill entity={mockEntity} />);
    expect(screen.queryByLabelText('Remove Apple')).not.toBeInTheDocument();
  });

  it('stops event propagation on click', () => {
    const mockOnClick = jest.fn();
    const mockParentClick = jest.fn();
    
    render(
      <div onClick={mockParentClick}>
        <EntityPill entity={mockEntity} onClick={mockOnClick} />
      </div>
    );
    
    const pill = screen.getByRole('button');
    fireEvent.click(pill);
    
    expect(mockOnClick).toHaveBeenCalled();
    expect(mockParentClick).not.toHaveBeenCalled();
  });
});