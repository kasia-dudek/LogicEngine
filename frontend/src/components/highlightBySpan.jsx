import React from 'react';

/**
 * Helper function to render text with highlight based on span (start, end)
 * Splits text into 3 parts: before highlight, highlight, after highlight
 * Wraps middle part in <span> with given className
 */
export function highlightBySpan(text, span, highlightClass) {
  if (!text || !span || span.start == null || span.end == null) {
    return text;
  }
  
  const start = Math.max(0, span.start);
  const end = Math.min(text.length, span.end);
  
  if (start >= end || start < 0 || end > text.length) {
    // Invalid span, return text as-is
    return text;
  }
  
  // Use slice as per requirements
  return (
    <>
      {text.slice(0, start)}
      <span className={highlightClass}>{text.slice(start, end)}</span>
      {text.slice(end)}
    </>
  );
}

/**
 * Helper function to slice text by code-points (not UTF-16 code units)
 * Handles multi-byte characters correctly
 */
function sliceByCodePoints(text, start, end) {
  const arr = Array.from(text);
  return arr.slice(start, end).join('');
}

/**
 * Render multiple non-overlapping spans in text using code-point indexing.
 * Spans format: List of tuples [(start, end), ...] (code-points)
 * Uses Array.from() to handle multi-byte characters correctly.
 * Optionally merges overlapping/adjacent spans to avoid nested <span> tags.
 */
export function highlightBySpansCP(text, spans, highlightClass = 'bg-red-100 rounded px-1') {
  if (!text || !spans || spans.length === 0) {
    return text;
  }
  
  // Convert text to array of code-points for accurate indexing
  const arr = Array.from(text);
  const parts = [];
  let i = 0;
  
  // Normalize spans format - handle both [{start, end}, ...] and [[start, end], ...]
  const normalizedSpans = spans.map(span => {
    if (Array.isArray(span)) {
      // Tuple format: [start, end]
      return { start: span[0], end: span[1] };
    } else {
      // Object format: {start, end}
      return { start: span.start || 0, end: span.end || text.length };
    }
  });
  
  // Sort spans by start position
  const sortedSpans = [...normalizedSpans].sort((a, b) => a.start - b.start);
  
  // Merge overlapping or adjacent spans (end >= next.start)
  const merged = [];
  for (const span of sortedSpans) {
    const start = span.start;
    const end = Math.min(span.end, arr.length);
    
    if (merged.length === 0) {
      merged.push({ start, end });
    } else {
      const last = merged[merged.length - 1];
      // If overlapping or adjacent, merge
      if (start <= last.end) {
        last.end = Math.max(last.end, end);
      } else {
        merged.push({ start, end });
      }
    }
  }
  
  // Render text with merged spans
  for (const span of merged) {
    const start = span.start;
    const end = Math.min(span.end, arr.length);
    
    // Add text before this span
    if (start > i) {
      parts.push(arr.slice(i, start).join(''));
    }
    
    // Add highlighted text
    parts.push(
      <span key={`highlight-${start}`} className={highlightClass}>
        {arr.slice(start, end).join('')}
      </span>
    );
    
    i = Math.max(i, end);
  }
  
  // Add remaining text
  if (i < arr.length) {
    parts.push(arr.slice(i).join(''));
  }
  
  return <>{parts}</>;
}

