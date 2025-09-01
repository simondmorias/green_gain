import React, { useMemo } from 'react';
import { EntityPill } from './EntityPill';
import { HighlightedTextProps, RecognizedEntity, EntityType } from '../../types/entities';

/**
 * Parse XML-style tagged text and extract entities
 */
function parseTaggedText(taggedText: string): Array<{ type: 'text' | 'entity'; content: string; entityType?: string }> {
  const parts: Array<{ type: 'text' | 'entity'; content: string; entityType?: string }> = [];
  
  // Regular expression to match XML-style tags
  const tagRegex = /<(\w+[-]?\w*)>([^<]+)<\/\1>/g;
  let lastIndex = 0;
  let match;

  while ((match = tagRegex.exec(taggedText)) !== null) {
    // Add text before the match
    if (match.index > lastIndex) {
      parts.push({
        type: 'text',
        content: taggedText.slice(lastIndex, match.index),
      });
    }

    // Add the entity
    parts.push({
      type: 'entity',
      content: match[2],
      entityType: match[1],
    });

    lastIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (lastIndex < taggedText.length) {
    parts.push({
      type: 'text',
      content: taggedText.slice(lastIndex),
    });
  }

  return parts;
}

/**
 * HighlightedText component - Renders text with entity pills
 */
export const HighlightedText: React.FC<HighlightedTextProps> = ({
  text,
  entities,
  onEntityClick,
  onEntityRemove,
  showConfidence = false,
  isInteractive = true,
}) => {
  const renderedElements = useMemo(() => {
    if (!entities || entities.length === 0) {
      return <span>{text}</span>;
    }

    // Sort entities by start position
    const sortedEntities = [...entities].sort((a, b) => a.start - b.start);
    const elements: React.ReactNode[] = [];
    let lastPos = 0;

    sortedEntities.forEach((entity, index) => {
      // Add text before entity
      if (entity.start > lastPos) {
        elements.push(
          <span key={`text-${lastPos}`}>{text.slice(lastPos, entity.start)}</span>
        );
      }

      // Add entity pill
      elements.push(
        <EntityPill
          key={`entity-${index}-${entity.start}`}
          entity={entity}
          onClick={onEntityClick}
          onRemove={onEntityRemove}
          showConfidence={showConfidence}
          isInteractive={isInteractive}
        />
      );

      lastPos = entity.end;
    });

    // Add remaining text
    if (lastPos < text.length) {
      elements.push(<span key={`text-${lastPos}`}>{text.slice(lastPos)}</span>);
    }

    return elements;
  }, [text, entities, onEntityClick, onEntityRemove, showConfidence, isInteractive]);

  return <div className="highlighted-text">{renderedElements}</div>;
};

/**
 * Alternative component that works with tagged text from the API
 */
export const HighlightedTaggedText: React.FC<{
  taggedText: string;
  entities: RecognizedEntity[];
  onEntityClick?: (entity: RecognizedEntity) => void;
  onEntityRemove?: (entity: RecognizedEntity) => void;
  showConfidence?: boolean;
  isInteractive?: boolean;
}> = ({
  taggedText,
  entities,
  onEntityClick,
  onEntityRemove,
  showConfidence = false,
  isInteractive = true,
}) => {
  const renderedElements = useMemo(() => {
    const parts = parseTaggedText(taggedText);
    const entityMap = new Map<string, RecognizedEntity>();

    // Create a map of entity text to entity object
    entities.forEach(entity => {
      const key = `${entity.type}-${entity.text}`;
      entityMap.set(key, entity);
    });

    return parts.map((part, index) => {
      if (part.type === 'text') {
        return <span key={`text-${index}`}>{part.content}</span>;
      }

      // Find matching entity
      const entityKey = `${part.entityType}-${part.content}`;
      const entity = entityMap.get(entityKey) || {
        text: part.content,
        type: (part.entityType || 'category') as EntityType,
        start: 0,
        end: 0,
        confidence: 1.0,
        metadata: { display_name: part.content },
      };

      return (
        <EntityPill
          key={`entity-${index}`}
          entity={entity}
          onClick={onEntityClick}
          onRemove={onEntityRemove}
          showConfidence={showConfidence}
          isInteractive={isInteractive}
        />
      );
    });
  }, [taggedText, entities, onEntityClick, onEntityRemove, showConfidence, isInteractive]);

  return <div className="highlighted-text">{renderedElements}</div>;
};

export default HighlightedText;