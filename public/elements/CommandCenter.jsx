/**
 * CommandCenter - Unified Tools & Actions Panel
 *
 * Consolidates all agentic tools, waves, and actions into one clean interface.
 * Replaces the scattered ToolsPanel and multiple action buttons.
 *
 * Tabs:
 * - Actions: Primary actions (Research, Think, Synthesize, Find Breakthrough)
 * - Agents: Switch between PWS methodology agents
 * - Waves: Forking, Canvas, Orchestration tools
 * - Settings: Quick settings toggles
 */

import { useState } from "react"

// Tab definitions
const TABS = [
  { id: "actions", label: "Actions", icon: "⚡" },
  { id: "agents", label: "Agents", icon: "🤖" },
  { id: "waves", label: "Waves", icon: "🌊" },
]

// Primary Actions - Most used tools
const PRIMARY_ACTIONS = [
  {
    id: "find_breakthrough",
    name: "Find Breakthrough",
    icon: "🚀",
    description: "Auto-orchestrated multi-agent analysis",
    action: "find_breakthrough",
    color: "#7c3aed",
    featured: true,
  },
  {
    id: "deep_research",
    name: "Research",
    icon: "🔍",
    description: "Web search with Tavily",
    action: "deep_research",
    color: "#2563eb",
  },
  {
    id: "think_through",
    name: "Think It Through",
    icon: "🧠",
    description: "Structured analysis",
    action: "think_through",
    color: "#7c3aed",
  },
  {
    id: "multi_agent",
    name: "Multi-Agent",
    icon: "👥",
    description: "Get multiple perspectives",
    action: "multi_agent_analysis",
    color: "#059669",
  },
  {
    id: "synthesize",
    name: "Synthesize",
    icon: "📝",
    description: "Summarize conversation",
    action: "synthesize_conversation",
    color: "#16a34a",
  },
  {
    id: "extract",
    name: "Extract",
    icon: "🔎",
    description: "Extract insights & data",
    action: "extract_insights",
    color: "#ea580c",
  },
]

// Agent shortcuts - Switch between bots
const AGENTS = [
  { id: "lawrence", name: "Lawrence", icon: "🎓", color: "#3b82f6", action: "switch_to_larry" },
  { id: "tta", name: "TTA", icon: "📈", color: "#7c3aed", action: "switch_to_tta" },
  { id: "jtbd", name: "JTBD", icon: "🎯", color: "#2563eb", action: "switch_to_jtbd" },
  { id: "redteam", name: "Red Team", icon: "💀", color: "#dc2626", action: "switch_to_redteam" },
  { id: "ackoff", name: "Ackoff", icon: "🔺", color: "#4f46e5", action: "switch_to_ackoff" },
  { id: "scurve", name: "S-Curve", icon: "📊", color: "#16a34a", action: "switch_to_scurve" },
]

// Wave tools - Advanced workflow features
const WAVE_TOOLS = [
  {
    id: "branches",
    name: "Branches",
    icon: "🌿",
    description: "Fork & manage conversation branches",
    action: "show_branch_selector",
    color: "#16a34a",
    wave: 2,
  },
  {
    id: "canvas",
    name: "Idea Canvas",
    icon: "🎨",
    description: "Visual workspace for ideas",
    action: "show_idea_canvas",
    color: "#f59e0b",
    wave: 3,
  },
  {
    id: "workflows",
    name: "Workflows",
    icon: "📋",
    description: "Choose orchestration workflow",
    action: "show_workflow_options",
    color: "#8b5cf6",
    wave: 4,
  },
  {
    id: "extract_ideas",
    name: "Extract Ideas",
    icon: "💡",
    description: "Pull ideas from conversation",
    action: "extract_ideas_now",
    color: "#eab308",
    wave: 3,
  },
]

const styles = {
  // Collapsed FAB
  fab: {
    position: 'fixed',
    bottom: '20px',
    right: '20px',
    zIndex: 9999,
    width: '56px',
    height: '56px',
    borderRadius: '50%',
    backgroundColor: '#3b82f6',
    color: 'white',
    border: 'none',
    cursor: 'pointer',
    boxShadow: '0 4px 14px rgba(59, 130, 246, 0.4)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '24px',
    transition: 'all 0.2s ease',
  },
  // Expanded panel
  panel: {
    position: 'fixed',
    bottom: '20px',
    right: '20px',
    zIndex: 9999,
    width: '320px',
    backgroundColor: 'white',
    borderRadius: '16px',
    boxShadow: '0 8px 30px rgba(0,0,0,0.12)',
    border: '1px solid #e5e7eb',
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 16px',
    borderBottom: '1px solid #f3f4f6',
    backgroundColor: '#fafafa',
  },
  title: {
    fontWeight: '600',
    fontSize: '14px',
    color: '#1f2937',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  closeBtn: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    fontSize: '18px',
    color: '#9ca3af',
    padding: '4px',
    borderRadius: '4px',
    transition: 'all 0.15s',
  },
  tabs: {
    display: 'flex',
    borderBottom: '1px solid #f3f4f6',
    backgroundColor: '#fafafa',
  },
  tab: {
    flex: 1,
    padding: '10px 8px',
    border: 'none',
    background: 'none',
    cursor: 'pointer',
    fontSize: '12px',
    fontWeight: '500',
    color: '#6b7280',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '4px',
    transition: 'all 0.15s',
    borderBottom: '2px solid transparent',
  },
  tabActive: {
    color: '#3b82f6',
    borderBottomColor: '#3b82f6',
    backgroundColor: 'white',
  },
  content: {
    padding: '12px',
    maxHeight: '400px',
    overflowY: 'auto',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '8px',
  },
  gridWide: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '8px',
  },
  button: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '12px 8px',
    border: '1px solid #e5e7eb',
    borderRadius: '10px',
    backgroundColor: 'white',
    cursor: 'pointer',
    transition: 'all 0.15s ease',
    minHeight: '70px',
  },
  buttonFeatured: {
    gridColumn: 'span 3',
    flexDirection: 'row',
    justifyContent: 'flex-start',
    gap: '12px',
    padding: '14px 16px',
    backgroundColor: '#f5f3ff',
    borderColor: '#7c3aed',
  },
  buttonIcon: {
    fontSize: '22px',
    marginBottom: '4px',
  },
  buttonName: {
    fontSize: '11px',
    fontWeight: '500',
    color: '#374151',
    textAlign: 'center',
  },
  buttonDesc: {
    fontSize: '10px',
    color: '#6b7280',
    textAlign: 'left',
  },
  waveBadge: {
    position: 'absolute',
    top: '-4px',
    right: '-4px',
    width: '16px',
    height: '16px',
    borderRadius: '50%',
    backgroundColor: '#3b82f6',
    color: 'white',
    fontSize: '9px',
    fontWeight: '700',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  divider: {
    height: '1px',
    backgroundColor: '#f3f4f6',
    margin: '12px 0',
  },
  hint: {
    fontSize: '11px',
    color: '#9ca3af',
    textAlign: 'center',
    marginTop: '8px',
  },
}

export default function CommandCenter() {
  const { callAction } = window.Chainlit || {}
  const {
    currentBot = "lawrence",
    initialTab = "actions",
    expanded: initialExpanded = false,
  } = props || {}

  const [isExpanded, setIsExpanded] = useState(initialExpanded)
  const [activeTab, setActiveTab] = useState(initialTab)

  const handleAction = (actionName, payload = {}) => {
    if (callAction) {
      callAction({ name: actionName, payload })
    }
    // Close panel after action (optional)
    // setIsExpanded(false)
  }

  // Collapsed state - just the FAB
  if (!isExpanded) {
    return (
      <button
        style={styles.fab}
        onClick={() => setIsExpanded(true)}
        onMouseEnter={(e) => {
          e.target.style.transform = 'scale(1.1)'
          e.target.style.boxShadow = '0 6px 20px rgba(59, 130, 246, 0.5)'
        }}
        onMouseLeave={(e) => {
          e.target.style.transform = 'scale(1)'
          e.target.style.boxShadow = '0 4px 14px rgba(59, 130, 246, 0.4)'
        }}
        title="Command Center"
        aria-label="Open Command Center"
      >
        ⚡
      </button>
    )
  }

  // Render action button
  const renderButton = (item, featured = false) => (
    <button
      key={item.id}
      style={{
        ...styles.button,
        ...(featured ? styles.buttonFeatured : {}),
        position: 'relative',
      }}
      onClick={() => handleAction(item.action, { tool_id: item.id })}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = item.color
        e.currentTarget.style.backgroundColor = '#f9fafb'
        e.currentTarget.style.transform = 'translateY(-2px)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = featured ? item.color : '#e5e7eb'
        e.currentTarget.style.backgroundColor = featured ? '#f5f3ff' : 'white'
        e.currentTarget.style.transform = 'translateY(0)'
      }}
      title={item.description}
    >
      <span style={{ ...styles.buttonIcon, color: item.color }}>{item.icon}</span>
      {featured ? (
        <div>
          <div style={{ ...styles.buttonName, textAlign: 'left', fontSize: '13px' }}>{item.name}</div>
          <div style={styles.buttonDesc}>{item.description}</div>
        </div>
      ) : (
        <span style={styles.buttonName}>{item.name}</span>
      )}
      {item.wave && (
        <span style={styles.waveBadge}>{item.wave}</span>
      )}
    </button>
  )

  // Tab content renderers
  const renderActions = () => (
    <div>
      {/* Featured action */}
      <div style={{ marginBottom: '12px' }}>
        {renderButton(PRIMARY_ACTIONS.find(a => a.featured), true)}
      </div>
      {/* Grid of other actions */}
      <div style={styles.grid}>
        {PRIMARY_ACTIONS.filter(a => !a.featured).map(a => renderButton(a))}
      </div>
    </div>
  )

  const renderAgents = () => (
    <div>
      <div style={styles.grid}>
        {AGENTS.map(a => renderButton(a))}
      </div>
      <div style={styles.hint}>
        Switch to a different PWS methodology expert
      </div>
    </div>
  )

  const renderWaves = () => (
    <div>
      <div style={styles.gridWide}>
        {WAVE_TOOLS.map(w => renderButton(w))}
      </div>
      <div style={styles.divider} />
      <div style={styles.hint}>
        Advanced workflow tools from Waves 2-4
      </div>
    </div>
  )

  const tabContent = {
    actions: renderActions,
    agents: renderAgents,
    waves: renderWaves,
  }

  return (
    <div style={styles.panel}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.title}>
          <span>⚡</span>
          <span>Command Center</span>
        </div>
        <button
          style={styles.closeBtn}
          onClick={() => setIsExpanded(false)}
          onMouseEnter={(e) => e.target.style.color = '#374151'}
          onMouseLeave={(e) => e.target.style.color = '#9ca3af'}
        >
          ✕
        </button>
      </div>

      {/* Tabs */}
      <div style={styles.tabs}>
        {TABS.map(tab => (
          <button
            key={tab.id}
            style={{
              ...styles.tab,
              ...(activeTab === tab.id ? styles.tabActive : {}),
            }}
            onClick={() => setActiveTab(tab.id)}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={styles.content}>
        {tabContent[activeTab]?.()}
      </div>
    </div>
  )
}
