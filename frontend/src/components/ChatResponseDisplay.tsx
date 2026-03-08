import React from 'react';
import type { FormattedChatResponse } from '../utils/chatResponseFormatter';

interface ChatResponseDisplayProps {
  response: FormattedChatResponse;
}

export const ChatResponseDisplay: React.FC<ChatResponseDisplayProps> = ({ response }) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
      }}
    >
      {/* Summary Section */}
      {response.summary && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <h4
            style={{
              margin: 0,
              fontSize: '14px',
              fontWeight: '700',
              color: 'var(--text-primary)',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}
          >
            📋 Summary
          </h4>
          <p
            style={{
              margin: 0,
              fontSize: '14px',
              lineHeight: '1.6',
              color: 'var(--text-primary)',
              paddingLeft: '12px',
              borderLeft: '3px solid var(--accent-primary)',
            }}
          >
            {response.summary}
          </p>
        </div>
      )}

      {/* Important Findings Section */}
      {response.importantFindings && response.importantFindings.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <h4
            style={{
              margin: 0,
              fontSize: '14px',
              fontWeight: '700',
              color: 'var(--text-primary)',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}
          >
            🔍 Important Findings
          </h4>
          <ul
            style={{
              margin: 0,
              paddingLeft: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
            }}
          >
            {response.importantFindings.map((finding, index) => (
              <li
                key={index}
                style={{
                  fontSize: '14px',
                  lineHeight: '1.6',
                  color: 'var(--text-primary)',
                  listStyleType: 'disc',
                }}
              >
                {finding}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* What It Means Section */}
      {response.whatItMeans && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <h4
            style={{
              margin: 0,
              fontSize: '14px',
              fontWeight: '700',
              color: 'var(--text-primary)',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}
          >
            💡 What It Means
          </h4>
          <p
            style={{
              margin: 0,
              fontSize: '14px',
              lineHeight: '1.6',
              color: 'var(--text-primary)',
              paddingLeft: '12px',
              borderLeft: '3px solid var(--accent-primary)',
            }}
          >
            {response.whatItMeans}
          </p>
        </div>
      )}

      {/* Suggested Action Section */}
      {response.suggestedAction && response.suggestedAction.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <h4
            style={{
              margin: 0,
              fontSize: '14px',
              fontWeight: '700',
              color: 'var(--text-primary)',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}
          >
            ✅ Suggested Action
          </h4>
          <ol
            style={{
              margin: 0,
              paddingLeft: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
            }}
          >
            {response.suggestedAction.map((action, index) => (
              <li
                key={index}
                style={{
                  fontSize: '14px',
                  lineHeight: '1.6',
                  color: 'var(--text-primary)',
                  listStyleType: 'decimal',
                }}
              >
                {action}
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
};
