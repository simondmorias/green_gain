import React, { KeyboardEvent, MouseEvent } from 'react';
import { EntityPillProps, ENTITY_COLORS } from '../../types/entities';
import styles from './EntityPill.module.css';

/**
 * EntityPill component - Renders a single entity as an interactive pill
 */
export const EntityPill: React.FC<EntityPillProps> = ({
  entity,
  onClick,
  onRemove,
  showConfidence = false,
  isInteractive = true,
}) => {
  const isLowConfidence = entity.confidence < 0.8;
  const entityType = entity.type.replace('_', '-'); // Normalize type format
  const colors = ENTITY_COLORS[entityType] || ENTITY_COLORS.category;

  const handleClick = (e: MouseEvent<HTMLSpanElement>) => {
    if (isInteractive && onClick) {
      e.stopPropagation();
      onClick(entity);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLSpanElement>) => {
    if (!isInteractive) return;

    if (e.key === 'Enter' && onClick) {
      e.preventDefault();
      onClick(entity);
    } else if (e.key === 'Delete' && onRemove) {
      e.preventDefault();
      onRemove(entity);
    }
  };

  const pillClassName = [
    styles.entityPill,
    styles[`entityPill--${entityType}`],
    isLowConfidence ? styles.entityPillUncertain : '',
    isInteractive ? styles.entityPillInteractive : '',
  ]
    .filter(Boolean)
    .join(' ');

  const pillStyle = {
    background: !isLowConfidence ? colors.gradient : 'transparent',
    color: !isLowConfidence ? colors.text : 'currentColor',
    borderColor: isLowConfidence ? 'currentColor' : 'transparent',
  };

  return (
    <span
      className={pillClassName}
      style={pillStyle}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      tabIndex={isInteractive ? 0 : -1}
      role={isInteractive ? 'button' : 'text'}
      aria-label={`${entity.type}: ${entity.text}${
        showConfidence ? ` (${Math.round(entity.confidence * 100)}% confidence)` : ''
      }`}
      data-entity-type={entityType}
      data-entity-id={entity.id}
      data-confidence={entity.confidence}
    >
      <span className={styles.entityPillText}>{entity.text}</span>
      {showConfidence && isLowConfidence && (
        <span className={styles.entityPillConfidence}>
          {Math.round(entity.confidence * 100)}%
        </span>
      )}

    </span>
  );
};

export default EntityPill;