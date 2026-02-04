/**
 * ThinkingPanel - Extended Thinking UI for Mindrian
 *
 * Visualizes LLM reasoning steps in a dedicated collapsible panel.
 * Works across all bots (Lawrence, TTA, JTBD, S-Curve, Red Team, Ackoff, etc.)
 *
 * Props:
 *   - steps: Array of thinking steps with {name, status, output, icon}
 *   - title: Panel title (default: "Lawrence's Thinking")
 *   - collapsed: Whether to start collapsed (default: false)
 *   - botId: Current bot ID for styling
 */

import { useState, useEffect } from 'react';

const statusColors = {
  pending: '#6b7280',    // gray
  active: '#3b82f6',     // blue
  complete: '#10b981',   // green
  error: '#ef4444',      // red
};

const statusIcons = {
  pending: '○',
  active: '◐',
  complete: '●',
  error: '✕',
};

const botColors = {
  lawrence: '#6366f1',      // indigo
  larry_playground: '#8b5cf6', // purple
  tta: '#f59e0b',           // amber
  jtbd: '#10b981',          // emerald
  scurve: '#3b82f6',        // blue
  redteam: '#ef4444',       // red
  ackoff: '#14b8a6',        // teal
  scenario: '#6366f1',      // indigo
  beautiful_question: '#ec4899', // pink
  nested_hierarchies: '#0891b2', // cyan
  validation: '#059669',    // emerald-600
  bono: '#7c3aed',          // violet
  knowns: '#dc2626',        // red-600
  domain: '#0d9488',        // teal-600
  investment: '#ca8a04',    // yellow-600
  grading: '#4f46e5',       // indigo-600
};

function ThinkingStep({ step, index, isLast }) {
  const [expanded, setExpanded] = useState(step.status === 'active');

  const statusColor = statusColors[step.status] || statusColors.pending;
  const statusIcon = statusIcons[step.status] || statusIcons.pending;

  return (
    <div
      style={{
        position: 'relative',
        paddingLeft: '24px',
        paddingBottom: isLast ? '0' : '16px',
      }}
    >
      {/* Vertical connector line */}
      {!isLast && (
        <div
          style={{
            position: 'absolute',
            left: '7px',
            top: '20px',
            bottom: '0',
            width: '2px',
            backgroundColor: step.status === 'complete' ? '#10b981' : '#e5e7eb',
          }}
        />
      )}

      {/* Status indicator */}
      <div
        style={{
          position: 'absolute',
          left: '0',
          top: '2px',
          width: '16px',
          height: '16px',
          borderRadius: '50%',
          backgroundColor: statusColor,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontSize: '10px',
          fontWeight: 'bold',
        }}
      >
        {step.status === 'active' && (
          <div
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: 'white',
              animation: 'pulse 1s infinite',
            }}
          />
        )}
      </div>

      {/* Step content */}
      <div
        onClick={() => step.output && setExpanded(!expanded)}
        style={{
          cursor: step.output ? 'pointer' : 'default',
          padding: '4px 8px',
          borderRadius: '4px',
          backgroundColor: expanded ? '#f3f4f6' : 'transparent',
          transition: 'background-color 0.2s',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {step.icon && <span style={{ fontSize: '14px' }}>{step.icon}</span>}
          <span
            style={{
              fontWeight: step.status === 'active' ? '600' : '400',
              color: step.status === 'complete' ? '#10b981' : '#374151',
            }}
          >
            {step.name}
          </span>
          {step.output && (
            <span style={{ color: '#9ca3af', fontSize: '12px' }}>
              {expanded ? '▼' : '▶'}
            </span>
          )}
        </div>

        {/* Expanded output */}
        {expanded && step.output && (
          <div
            style={{
              marginTop: '8px',
              padding: '8px',
              backgroundColor: 'white',
              borderRadius: '4px',
              border: '1px solid #e5e7eb',
              fontSize: '13px',
              color: '#4b5563',
              whiteSpace: 'pre-wrap',
            }}
          >
            {step.output}
          </div>
        )}
      </div>
    </div>
  );
}

// Bot display names for dynamic title
const botNames = {
  lawrence: 'Lawrence',
  larry_playground: 'Larry Playground',
  tta: 'TTA',
  jtbd: 'JTBD',
  scurve: 'S-Curve',
  redteam: 'Red Team',
  ackoff: 'Ackoff',
  scenario: 'Scenario',
  beautiful_question: 'Beautiful Question',
  nested_hierarchies: 'Nested Hierarchies',
  validation: 'Validation',
  bono: 'BONO',
  knowns: 'Known-Unknowns',
  domain: 'Domain',
  investment: 'Investment',
  grading: 'Minto Grading',
};

export default function ThinkingPanel({
  steps = [],
  title = null, // Now optional - will use bot name if not provided
  collapsed = false,
  botId = 'lawrence',
  methodology = null,
  showWhenEmpty = false, // QA fix: Don't show when empty by default
}) {
  const [isCollapsed, setIsCollapsed] = useState(collapsed);
  const accentColor = botColors[botId] || botColors.lawrence;

  // Dynamic title: use provided title, or generate from bot name
  const displayTitle = title || `${botNames[botId] || 'AI'}'s Thinking`;

  // Auto-expand when new active step appears
  useEffect(() => {
    const hasActiveStep = steps.some(s => s.status === 'active');
    if (hasActiveStep && isCollapsed) {
      setIsCollapsed(false);
    }
  }, [steps]);

  const completedCount = steps.filter(s => s.status === 'complete').length;
  const totalCount = steps.length;
  const progress = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

  // QA P2 UPDATE: Still show panel when empty but with a different message
  // The user wants thinking to WORK, not be hidden
  // Show a helpful "initializing" state instead of confusing "0/0"
  const isInitializing = totalCount === 0;

  return (
    <div
      style={{
        backgroundColor: '#ffffff',
        borderRadius: '8px',
        border: '1px solid #e5e7eb',
        overflow: 'hidden',
        marginBottom: '16px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      }}
    >
      {/* Header */}
      <div
        onClick={() => setIsCollapsed(!isCollapsed)}
        style={{
          padding: '12px 16px',
          backgroundColor: accentColor,
          color: 'white',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '18px' }}>🧠</span>
          <span style={{ fontWeight: '600' }}>{displayTitle}</span>
          {methodology && (
            <span
              style={{
                fontSize: '12px',
                backgroundColor: 'rgba(255,255,255,0.2)',
                padding: '2px 8px',
                borderRadius: '4px',
              }}
            >
              {methodology}
            </span>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Progress indicator - show helpful text when initializing */}
          <span style={{ fontSize: '12px', opacity: 0.9 }}>
            {isInitializing ? 'Analyzing...' : `${completedCount}/${totalCount}`}
          </span>
          {/* Collapse icon */}
          <span style={{ fontSize: '12px' }}>
            {isCollapsed ? '▶' : '▼'}
          </span>
        </div>
      </div>

      {/* Progress bar */}
      <div style={{ height: '3px', backgroundColor: '#e5e7eb' }}>
        <div
          style={{
            height: '100%',
            width: `${progress}%`,
            backgroundColor: '#10b981',
            transition: 'width 0.3s ease',
          }}
        />
      </div>

      {/* Steps */}
      {!isCollapsed && (
        <div style={{ padding: '16px' }}>
          {steps.length === 0 ? (
            <div style={{ color: '#6b7280', textAlign: 'center', padding: '20px' }}>
              <div style={{ fontSize: '24px', marginBottom: '8px' }}>🔄</div>
              <div style={{ fontWeight: '500' }}>Analyzing your message...</div>
              <div style={{ fontSize: '12px', marginTop: '4px', color: '#9ca3af' }}>
                Checking assumptions, patterns, and PWS methodology fit
              </div>
            </div>
          ) : (
            steps.map((step, index) => (
              <ThinkingStep
                key={index}
                step={step}
                index={index}
                isLast={index === steps.length - 1}
              />
            ))
          )}
        </div>
      )}

      {/* Pulse animation */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
}
