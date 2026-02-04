/**
 * FloatingActionBar - Sticky action buttons above the chat input
 *
 * This component renders as a fixed bar that stays visible regardless of scroll position.
 * Solves the UX problem where buttons disappear when messages are long.
 */

export default function FloatingActionBar() {
  const { callAction } = window.Chainlit || {}

  // Props from Python
  const {
    actions = [],
    botName = "Lawrence",
    showOpportunities = true
  } = props || {}

  const handleAction = (actionName, payload = {}) => {
    if (callAction) {
      callAction({ name: actionName, payload })
    }
  }

  // Default core actions if none provided
  const defaultActions = [
    { name: "deep_research", label: "Research", icon: "search", color: "blue" },
    { name: "synthesize_conversation", label: "Synthesize", icon: "download", color: "green" },
    { name: "think_through", label: "Think", icon: "brain", color: "purple" },
    { name: "map_ideas", label: "Visualize", icon: "chart", color: "orange" },
    { name: "view_opportunities", label: "Bank", icon: "bank", color: "yellow" },
  ]

  const displayActions = actions.length > 0 ? actions : defaultActions

  // Icon mapping
  const icons = {
    search: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="11" cy="11" r="8"/>
        <path d="m21 21-4.35-4.35"/>
      </svg>
    ),
    download: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="7,10 12,15 17,10"/>
        <line x1="12" y1="15" x2="12" y2="3"/>
      </svg>
    ),
    brain: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 2a8 8 0 0 0-8 8c0 3.5 2.5 6.5 6 7.5V22h4v-4.5c3.5-1 6-4 6-7.5a8 8 0 0 0-8-8z"/>
      </svg>
    ),
    chart: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="3" y="3" width="18" height="18" rx="2"/>
        <path d="M3 9h18M9 21V9"/>
      </svg>
    ),
    bank: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3"/>
      </svg>
    ),
    example: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
      </svg>
    ),
  }

  const styles = {
    container: {
      position: 'fixed',
      bottom: '80px', // Above chat input
      left: '50%',
      transform: 'translateX(-50%)',
      zIndex: 1000,
      display: 'flex',
      gap: '8px',
      padding: '8px 16px',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderRadius: '24px',
      boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)',
      backdropFilter: 'blur(10px)',
      border: '1px solid rgba(0, 0, 0, 0.1)',
    },
    button: {
      display: 'flex',
      alignItems: 'center',
      gap: '6px',
      padding: '8px 14px',
      borderRadius: '16px',
      border: 'none',
      cursor: 'pointer',
      fontSize: '13px',
      fontWeight: '500',
      transition: 'all 0.2s ease',
      backgroundColor: '#f3f4f6',
      color: '#374151',
    },
    buttonHover: {
      backgroundColor: '#e5e7eb',
      transform: 'translateY(-1px)',
    },
  }

  // Color variants
  const colorStyles = {
    blue: { backgroundColor: '#dbeafe', color: '#1d4ed8' },
    green: { backgroundColor: '#d1fae5', color: '#047857' },
    purple: { backgroundColor: '#ede9fe', color: '#7c3aed' },
    orange: { backgroundColor: '#ffedd5', color: '#c2410c' },
    yellow: { backgroundColor: '#fef3c7', color: '#b45309' },
    gray: { backgroundColor: '#f3f4f6', color: '#374151' },
  }

  // Handle keyboard navigation within toolbar
  const handleKeyDown = (e, index) => {
    const buttons = e.currentTarget.parentElement.querySelectorAll('button')
    let nextIndex = index

    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      e.preventDefault()
      nextIndex = (index + 1) % buttons.length
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      e.preventDefault()
      nextIndex = (index - 1 + buttons.length) % buttons.length
    } else if (e.key === 'Home') {
      e.preventDefault()
      nextIndex = 0
    } else if (e.key === 'End') {
      e.preventDefault()
      nextIndex = buttons.length - 1
    }

    if (nextIndex !== index) {
      buttons[nextIndex].focus()
    }
  }

  return (
    <div
      style={styles.container}
      role="toolbar"
      aria-label={`${botName} quick actions`}
    >
      {displayActions.map((action, index) => (
        <button
          key={action.name || index}
          style={{
            ...styles.button,
            ...(colorStyles[action.color] || colorStyles.gray),
          }}
          onClick={() => handleAction(action.name, action.payload || {})}
          onKeyDown={(e) => handleKeyDown(e, index)}
          onMouseEnter={(e) => {
            e.target.style.transform = 'translateY(-2px)'
            e.target.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)'
          }}
          onMouseLeave={(e) => {
            e.target.style.transform = 'translateY(0)'
            e.target.style.boxShadow = 'none'
          }}
          title={action.tooltip || action.label}
          aria-label={action.tooltip || `${action.label} - ${action.name.replace(/_/g, ' ')}`}
          tabIndex={index === 0 ? 0 : -1}
        >
          <span aria-hidden="true">{icons[action.icon] || null}</span>
          {action.label}
        </button>
      ))}
    </div>
  )
}
