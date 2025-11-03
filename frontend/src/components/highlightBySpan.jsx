import React from 'react';

/**
 * Helper function to render text with highlight based on span (start, end)
 * Splits text into 3 parts: before highlight, highlight, after highlight
 * Wraps middle part in <span> with given className
 */
export function highlightBySpan(text, span, highlightClass) {
  if (!text || !span || span.start === undefined || span.end === undefined) {
    return text;
  }
  
  const start = Math.max(0, span.start);
  const end = Math.min(text.length, span.end);
  
  if (start >= end || start < 0 || end > text.length) {
    // Invalid span, return text as-is
    return text;
  }
  
  const before = text.substring(0, start);
  const highlighted = text.substring(start, end);
  const after = text.substring(end);
  
  return (
    <>
      {before}
      <span className={highlightClass}>{highlighted}</span>
      {after}
    </>
  );
}

/**
 * Render multiple non-overlapping spans in text.
 * Spans are merged if overlapping, with priority: later spans override earlier ones.
 */
export function highlightBySpans(text, spans, highlightClass) {
  if (!text || !spans || spans.length === 0) {
    return text;
  }
  
  // Sort spans by start position
  const sortedSpans = [...spans].sort((a, b) => a[0] - b[0]);
  
  // Merge overlapping spans
  const merged = [];
  for (const span of sortedSpans) {
    const [start, end] = span;
    if (merged.length === 0) {
      merged.push([start, end]);
    } else {
      const last = merged[merged.length - 1];
      if (start <= last[1]) {
        // Overlapping, merge
        last[1] = Math.max(last[1], end);
      } else {
        merged.push([start, end]);
      }
    }
  }
  
  // Render text with highlights
  const parts = [];
  let lastEnd = 0;
  
  for (const [start, end] of merged) {
    // Add text before this span
    if (start > lastEnd) {
      parts.push(text.substring(lastEnd, start));
    }
    // Add highlighted text
    parts.push(
      <span key={`highlight-${start}`} className={highlightClass}>
        {text.substring(start, end)}
      </span>
    );
    lastEnd = end;
  }
  
  // Add remaining text
  if (lastEnd < text.length) {
    parts.push(text.substring(lastEnd));
  }
  
  return <>{parts}</>;
}

