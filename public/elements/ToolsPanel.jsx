/**
 * ToolsPanel - Floating PWS Tools Repository
 *
 * A floating panel (bottom-right) showing available PWS methodology tools
 * with contextual tooltips that explain WHY each tool might help.
 *
 * Uses inline styles (not shadcn) for Chainlit compatibility.
 */

import { useState } from "react"

// PWS Tools configuration - Core methodology tools
const PWS_TOOLS = [
  {
    id: "reverse_salient",
    name: "Reverse Salient",
    icon: "🔓",
    shortDesc: "Find the bottleneck",
    whyHelps: "Use when you're stuck. Finds the ONE constraint holding everything back.",
    contextTriggers: ["stuck", "bottleneck", "constraint", "blocking", "infrastructure", "scaling"],
    action: "switch_to_tta",
    color: "#d97706",
  },
  {
    id: "jtbd",
    name: "Jobs to Be Done",
    icon: "🎯",
    shortDesc: "What job are they hiring?",
    whyHelps: "Use when exploring customer needs. People hire products to make progress.",
    contextTriggers: ["customer", "user", "buying", "product", "feature", "want", "need"],
    action: "switch_to_jtbd",
    color: "#2563eb",
  },
  {
    id: "tta",
    name: "Trending to Absurd",
    icon: "📈",
    shortDesc: "Take it to extremes",
    whyHelps: "Use when exploring trends. What happens if this continues? What breaks first?",
    contextTriggers: ["trend", "future", "growing", "changing", "emerging", "AI", "technology"],
    action: "switch_to_tta",
    color: "#7c3aed",
  },
  {
    id: "red_team",
    name: "Red Team",
    icon: "💀",
    shortDesc: "Attack your assumptions",
    whyHelps: "Use when you feel confident. Find the flaws before the market does.",
    contextTriggers: ["assumption", "believe", "think", "confident", "sure", "risk", "compete"],
    action: "switch_to_redteam",
    color: "#dc2626",
  },
  {
    id: "scurve",
    name: "S-Curve",
    icon: "📊",
    shortDesc: "Where on the curve?",
    whyHelps: "Use for timing decisions. Is this technology early, rapid growth, or plateauing?",
    contextTriggers: ["timing", "market", "adoption", "mature", "early", "late", "invest"],
    action: "switch_to_scurve",
    color: "#16a34a",
  },
  {
    id: "ackoff",
    name: "DIKW Pyramid",
    icon: "🔺",
    shortDesc: "Validate understanding",
    whyHelps: "Use when making decisions. Do you have data, info, knowledge, or wisdom?",
    contextTriggers: ["data", "information", "understand", "decision", "evidence", "know"],
    action: "switch_to_ackoff",
    color: "#4f46e5",
  },
  {
    id: "scenario",
    name: "Scenario Analysis",
    icon: "🌐",
    shortDesc: "Multiple futures",
    whyHelps: "Use when facing uncertainty. Explore multiple plausible paths forward.",
    contextTriggers: ["future", "uncertain", "might", "could", "planning", "strategy"],
    action: "switch_to_scenario",
    color: "#0891b2",
  },
  {
    id: "beautiful_question",
    name: "Beautiful Question",
    icon: "❓",
    shortDesc: "WHY → WHAT IF → HOW",
    whyHelps: "Use when stuck on framing. Better questions lead to better solutions.",
    contextTriggers: ["why", "question", "curious", "wonder", "how might"],
    action: "switch_to_beautiful_question",
    color: "#db2777",
  },
]

// Advanced LangGraph Pipelines - Multi-step analysis tools
const ADVANCED_TOOLS = [
  {
    id: "minto",
    name: "Minto Pyramid",
    icon: "📋",
    shortDesc: "SCQA structured analysis",
    whyHelps: "Use for complex problems. Situation → Complication → Question → Answer.",
    action: "run_minto_analysis",
    color: "#ea580c",
  },
  {
    id: "validation",
    name: "Multi-Validation",
    icon: "✅",
    shortDesc: "6-perspective stress test",
    whyHelps: "Use before big decisions. Tests your idea from six thinking hat perspectives.",
    action: "switch_to_validation",
    color: "#059669",
  },
  {
    id: "domain",
    name: "Domain Discovery",
    icon: "🧭",
    shortDesc: "Find your territory",
    whyHelps: "Use when exploring opportunities. Maps where you can uniquely contribute.",
    action: "switch_to_domain",
    color: "#0d9488",
  },
  {
    id: "oracle",
    name: "Oracle Foresight",
    icon: "🔮",
    shortDesc: "Prediction thinking",
    whyHelps: "Use for forecasting. Structure predictions with confidence and resolution criteria.",
    action: "run_oracle_prediction",
    color: "#8b5cf6",
  },
  {
    id: "genesis",
    name: "Genesis Expert",
    icon: "🧠",
    shortDesc: "Multi-domain expert panel",
    whyHelps: "Use for breakthrough ideas. Simulates expert panel with Six Hats perspectives.",
    action: "run_genesis_analysis",
    color: "#4338ca",
  },
]

// Styles
const styles = {
  // Collapsed button
  collapsedContainer: {
    position: 'fixed',
    bottom: '16px',
    right: '16px',
    zIndex: 9999,
  },
  toggleButton: {
    width: '48px',
    height: '48px',
    borderRadius: '50%',
    backgroundColor: '#3b82f6',
    color: 'white',
    border: 'none',
    cursor: 'pointer',
    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '20px',
    transition: 'transform 0.2s, box-shadow 0.2s',
  },
  // Expanded panel
  expandedContainer: {
    position: 'fixed',
    bottom: '16px',
    right: '16px',
    zIndex: 9999,
    width: '300px',
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
    border: '1px solid #e5e7eb',
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 16px',
    borderBottom: '1px solid #e5e7eb',
    backgroundColor: '#f9fafb',
  },
  headerTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontWeight: '600',
    fontSize: '14px',
    color: '#1f2937',
  },
  closeButton: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    padding: '4px',
    borderRadius: '4px',
    color: '#6b7280',
    fontSize: '16px',
  },
  content: {
    padding: '12px',
    maxHeight: '500px',
    overflowY: 'auto',
  },
  sectionLabel: {
    fontSize: '11px',
    fontWeight: '600',
    color: '#6b7280',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    marginBottom: '8px',
    marginTop: '4px',
  },
  toolsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '8px',
    marginBottom: '16px',
  },
  toolButton: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '10px 4px',
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    backgroundColor: 'white',
    cursor: 'pointer',
    transition: 'all 0.2s',
    minHeight: '60px',
  },
  toolButtonRelevant: {
    backgroundColor: '#eff6ff',
    borderColor: '#3b82f6',
  },
  toolIcon: {
    fontSize: '20px',
    marginBottom: '4px',
  },
  toolName: {
    fontSize: '9px',
    textAlign: 'center',
    color: '#374151',
    lineHeight: '1.2',
  },
  tooltip: {
    position: 'absolute',
    right: '100%',
    top: '50%',
    transform: 'translateY(-50%)',
    marginRight: '8px',
    backgroundColor: '#1f2937',
    color: 'white',
    padding: '10px 14px',
    borderRadius: '8px',
    fontSize: '12px',
    width: '220px',
    zIndex: 10000,
    boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
  },
  tooltipTitle: {
    fontWeight: '600',
    marginBottom: '6px',
    fontSize: '13px',
  },
  tooltipShort: {
    color: '#a5b4fc',
    fontSize: '11px',
    marginBottom: '6px',
  },
  tooltipWhy: {
    color: '#fcd34d',
    fontSize: '11px',
    fontStyle: 'italic',
    lineHeight: '1.4',
  },
  contextHint: {
    textAlign: 'center',
    fontSize: '10px',
    color: '#9ca3af',
    padding: '8px',
    borderTop: '1px solid #e5e7eb',
  },
  divider: {
    borderTop: '1px solid #e5e7eb',
    margin: '8px 0',
  },
}

export default function ToolsPanel() {
  const { callAction, sendUserMessage } = window.Chainlit || {}
  const {
    conversationContext = "",
    currentBot = "lawrence",
    expanded: initialExpanded = false,
  } = props || {}

  const [isExpanded, setIsExpanded] = useState(initialExpanded)
  const [hoveredTool, setHoveredTool] = useState(null)

  // Check if tool is relevant to current conversation
  const getRelevance = (tool) => {
    if (!conversationContext || !tool.contextTriggers) return false
    const ctx = conversationContext.toLowerCase()
    return tool.contextTriggers.some((trigger) => ctx.includes(trigger))
  }

  // Handle tool click
  const handleToolClick = (tool) => {
    if (callAction && tool.action) {
      callAction({ name: tool.action, payload: { tool_id: tool.id } })
    } else if (sendUserMessage) {
      sendUserMessage(`Help me use ${tool.name} for my current exploration`)
    }
  }

  // Sort tools by relevance
  const sortedTools = [...PWS_TOOLS].sort((a, b) => {
    const aRelevant = getRelevance(a)
    const bRelevant = getRelevance(b)
    if (aRelevant && !bRelevant) return -1
    if (!aRelevant && bRelevant) return 1
    return 0
  })

  // Render tool button with tooltip
  const renderToolButton = (tool, isAdvanced = false) => {
    const isRelevant = !isAdvanced && getRelevance(tool)
    const isHovered = hoveredTool === tool.id

    return (
      <div key={tool.id} style={{ position: 'relative' }}>
        <button
          style={{
            ...styles.toolButton,
            ...(isRelevant ? styles.toolButtonRelevant : {}),
            backgroundColor: isHovered ? '#f3f4f6' : (isRelevant ? '#eff6ff' : 'white'),
            borderColor: isHovered ? tool.color : (isRelevant ? '#3b82f6' : '#e5e7eb'),
          }}
          onClick={() => handleToolClick(tool)}
          onMouseEnter={() => setHoveredTool(tool.id)}
          onMouseLeave={() => setHoveredTool(null)}
        >
          <span style={{ ...styles.toolIcon, color: tool.color }}>
            {tool.icon}
          </span>
          <span style={styles.toolName}>
            {tool.name.split(" ")[0]}
          </span>
          {isRelevant && (
            <span style={{
              position: 'absolute',
              top: '-4px',
              right: '-4px',
              width: '8px',
              height: '8px',
              backgroundColor: '#3b82f6',
              borderRadius: '50%',
            }} />
          )}
        </button>

        {/* Tooltip on hover */}
        {isHovered && (
          <div style={styles.tooltip}>
            <div style={styles.tooltipTitle}>{tool.name}</div>
            <div style={styles.tooltipShort}>{tool.shortDesc}</div>
            <div style={styles.tooltipWhy}>{tool.whyHelps}</div>
          </div>
        )}
      </div>
    )
  }

  // Collapsed state
  if (!isExpanded) {
    return (
      <div style={styles.collapsedContainer}>
        <button
          style={styles.toggleButton}
          onClick={() => setIsExpanded(true)}
          onMouseEnter={(e) => {
            e.target.style.transform = 'scale(1.1)'
            e.target.style.boxShadow = '0 6px 16px rgba(0,0,0,0.2)'
          }}
          onMouseLeave={(e) => {
            e.target.style.transform = 'scale(1)'
            e.target.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)'
          }}
          title="Open PWS Tools"
        >
          🛠️
        </button>
      </div>
    )
  }

  // Expanded state - all tools visible
  return (
    <div style={styles.expandedContainer}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerTitle}>
          <span>🛠️</span>
          <span>PWS Tools</span>
        </div>
        <button
          style={styles.closeButton}
          onClick={() => setIsExpanded(false)}
        >
          ✕
        </button>
      </div>

      {/* Content */}
      <div style={styles.content}>
        {/* Core PWS Tools */}
        <div style={styles.sectionLabel}>Core Frameworks</div>
        <div style={styles.toolsGrid}>
          {sortedTools.map((tool) => renderToolButton(tool, false))}
        </div>

        {/* Divider */}
        <div style={styles.divider} />

        {/* Advanced Pipelines - Always visible */}
        <div style={styles.sectionLabel}>Advanced Pipelines</div>
        <div style={styles.toolsGrid}>
          {ADVANCED_TOOLS.map((tool) => renderToolButton(tool, true))}
        </div>

        {/* Context indicator */}
        {conversationContext && (
          <div style={styles.contextHint}>
            ✨ Highlighted tools match your conversation
          </div>
        )}
      </div>
    </div>
  )
}
