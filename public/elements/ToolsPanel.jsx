/**
 * ToolsPanel - Floating PWS Tools Repository
 *
 * A floating panel (bottom-right) showing available PWS methodology tools
 * with contextual tooltips that explain WHY each tool might help.
 *
 * Uses inline styles (not shadcn) for Chainlit compatibility.
 */

import { useState } from "react"

// PWS Tools configuration
const PWS_TOOLS = [
  {
    id: "reverse_salient",
    name: "Reverse Salient",
    icon: "🔓",
    shortDesc: "Find the bottleneck",
    fullDesc: "Identify the ONE constraint holding everything else back.",
    contextTriggers: ["stuck", "bottleneck", "constraint", "blocking", "infrastructure", "scaling"],
    action: "switch_to_tta",
    color: "#d97706",
  },
  {
    id: "jtbd",
    name: "Jobs to Be Done",
    icon: "🎯",
    shortDesc: "What job are they hiring?",
    fullDesc: "People don't buy products — they hire them to make progress.",
    contextTriggers: ["customer", "user", "buying", "product", "feature", "want", "need"],
    action: "switch_to_jtbd",
    color: "#2563eb",
  },
  {
    id: "tta",
    name: "Trending to Absurd",
    icon: "📈",
    shortDesc: "Take it to extremes",
    fullDesc: "Extrapolate trends to their logical extreme. What breaks first?",
    contextTriggers: ["trend", "future", "growing", "changing", "emerging", "AI", "technology"],
    action: "switch_to_tta",
    color: "#7c3aed",
  },
  {
    id: "red_team",
    name: "Red Team",
    icon: "💀",
    shortDesc: "Attack your assumptions",
    fullDesc: "Be your own devil's advocate. Find the flaws before the market does.",
    contextTriggers: ["assumption", "believe", "think", "confident", "sure", "risk", "compete"],
    action: "switch_to_redteam",
    color: "#dc2626",
  },
  {
    id: "scurve",
    name: "S-Curve",
    icon: "📊",
    shortDesc: "Where on the curve?",
    fullDesc: "Every technology follows slow → rapid → plateau. Timing is everything.",
    contextTriggers: ["timing", "market", "adoption", "mature", "early", "late", "invest"],
    action: "switch_to_scurve",
    color: "#16a34a",
  },
  {
    id: "ackoff",
    name: "DIKW Pyramid",
    icon: "🔺",
    shortDesc: "Validate understanding",
    fullDesc: "Data → Information → Knowledge → Wisdom. Don't act on incomplete understanding.",
    contextTriggers: ["data", "information", "understand", "decision", "evidence", "know"],
    action: "switch_to_ackoff",
    color: "#4f46e5",
  },
  {
    id: "scenario",
    name: "Scenario Analysis",
    icon: "🌐",
    shortDesc: "Multiple futures",
    fullDesc: "The future is uncertain. Explore multiple plausible paths.",
    contextTriggers: ["future", "uncertain", "might", "could", "planning", "strategy"],
    action: "switch_to_scenario",
    color: "#0891b2",
  },
  {
    id: "beautiful_question",
    name: "Beautiful Question",
    icon: "❓",
    shortDesc: "WHY → WHAT IF → HOW",
    fullDesc: "The quality of your solution depends on the quality of your question.",
    contextTriggers: ["why", "question", "curious", "wonder", "how might"],
    action: "switch_to_beautiful_question",
    color: "#db2777",
  },
]

// Advanced LangGraph Pipelines
const ADVANCED_TOOLS = [
  {
    id: "minto",
    name: "Minto Pyramid",
    icon: "📋",
    shortDesc: "SCQA structured analysis",
    fullDesc: "Situation → Complication → Question → Answer.",
    action: "run_minto_analysis",
    color: "#ea580c",
  },
  {
    id: "validation",
    name: "Multi-Validation",
    icon: "✅",
    shortDesc: "6-perspective stress test",
    fullDesc: "Six Thinking Hats + research. Test your idea from every angle.",
    action: "switch_to_validation",
    color: "#059669",
  },
  {
    id: "domain",
    name: "Domain Discovery",
    icon: "🧭",
    shortDesc: "Find your territory",
    fullDesc: "Analyze your background to find where you can uniquely contribute.",
    action: "switch_to_domain",
    color: "#0d9488",
  },
  {
    id: "oracle",
    name: "Oracle Foresight",
    icon: "🔮",
    shortDesc: "Prediction thinking",
    fullDesc: "Structure predictions with confidence levels.",
    action: "run_oracle_prediction",
    color: "#8b5cf6",
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
    width: '280px',
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
  },
  content: {
    padding: '12px',
    maxHeight: '400px',
    overflowY: 'auto',
  },
  toolsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '8px',
    marginBottom: '12px',
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
    fontSize: '10px',
    textAlign: 'center',
    color: '#374151',
    lineHeight: '1.2',
  },
  advancedToggle: {
    width: '100%',
    padding: '8px',
    backgroundColor: 'transparent',
    border: 'none',
    cursor: 'pointer',
    fontSize: '12px',
    color: '#6b7280',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '4px',
  },
  advancedSection: {
    borderTop: '1px solid #e5e7eb',
    paddingTop: '12px',
    marginTop: '8px',
  },
  tooltip: {
    position: 'absolute',
    right: '100%',
    top: '50%',
    transform: 'translateY(-50%)',
    marginRight: '8px',
    backgroundColor: '#1f2937',
    color: 'white',
    padding: '8px 12px',
    borderRadius: '6px',
    fontSize: '12px',
    width: '200px',
    zIndex: 10000,
    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
  },
  tooltipTitle: {
    fontWeight: '600',
    marginBottom: '4px',
  },
  tooltipDesc: {
    color: '#d1d5db',
    fontSize: '11px',
  },
  contextHint: {
    textAlign: 'center',
    fontSize: '10px',
    color: '#9ca3af',
    marginTop: '12px',
    padding: '8px',
    borderTop: '1px solid #e5e7eb',
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
  const [showAdvanced, setShowAdvanced] = useState(false)
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

  // Expanded state
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
        {/* Main Tools Grid */}
        <div style={styles.toolsGrid}>
          {sortedTools.map((tool) => {
            const isRelevant = getRelevance(tool)
            const isHovered = hoveredTool === tool.id

            return (
              <div key={tool.id} style={{ position: 'relative' }}>
                <button
                  style={{
                    ...styles.toolButton,
                    ...(isRelevant ? styles.toolButtonRelevant : {}),
                    backgroundColor: isHovered ? '#f3f4f6' : (isRelevant ? '#eff6ff' : 'white'),
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
                    <div style={styles.tooltipDesc}>{tool.shortDesc}</div>
                    <div style={{ ...styles.tooltipDesc, marginTop: '4px', fontStyle: 'italic' }}>
                      {tool.fullDesc}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Advanced Tools Toggle */}
        <button
          style={styles.advancedToggle}
          onClick={() => setShowAdvanced(!showAdvanced)}
        >
          {showAdvanced ? "▲" : "▼"} {showAdvanced ? "Hide" : "Show"} Advanced Pipelines
        </button>

        {/* Advanced Tools */}
        {showAdvanced && (
          <div style={styles.advancedSection}>
            <div style={styles.toolsGrid}>
              {ADVANCED_TOOLS.map((tool) => {
                const isHovered = hoveredTool === tool.id

                return (
                  <div key={tool.id} style={{ position: 'relative' }}>
                    <button
                      style={{
                        ...styles.toolButton,
                        backgroundColor: isHovered ? '#f3f4f6' : 'white',
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
                    </button>

                    {/* Tooltip */}
                    {isHovered && (
                      <div style={styles.tooltip}>
                        <div style={styles.tooltipTitle}>{tool.name}</div>
                        <div style={styles.tooltipDesc}>{tool.shortDesc}</div>
                        <div style={{ ...styles.tooltipDesc, marginTop: '4px', fontStyle: 'italic' }}>
                          {tool.fullDesc}
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}

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
