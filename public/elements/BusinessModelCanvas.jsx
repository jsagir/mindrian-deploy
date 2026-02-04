/**
 * BusinessModelCanvas - Interactive 9-box Business Model Canvas
 *
 * Based on Alexander Osterwalder's Business Model Canvas
 *
 * Props:
 *   - title: Canvas title (default: "Business Model Canvas")
 *   - data: Object with section arrays:
 *     - keyPartners: []
 *     - keyActivities: []
 *     - keyResources: []
 *     - valuePropositions: []
 *     - customerRelationships: []
 *     - channels: []
 *     - customerSegments: []
 *     - costStructure: []
 *     - revenueStreams: []
 *   - editable: Boolean to enable editing (default: false)
 *   - variant: 'bmc' | 'lean' (default: 'bmc')
 */

export default function BusinessModelCanvas() {
  const { callAction } = window.Chainlit || {}
  const {
    title = 'Business Model Canvas',
    data = {},
    editable = false,
    variant = 'bmc'
  } = props || {}

  const [canvasData, setCanvasData] = React.useState(data)
  const [editingSection, setEditingSection] = React.useState(null)
  const [editValue, setEditValue] = React.useState('')

  // BMC sections configuration
  const bmcSections = {
    keyPartners: { label: 'Key Partners', icon: '🤝', color: '#e3f2fd', question: 'Who are your key partners and suppliers?' },
    keyActivities: { label: 'Key Activities', icon: '⚡', color: '#e8f5e9', question: 'What key activities does your value proposition require?' },
    keyResources: { label: 'Key Resources', icon: '🏗️', color: '#fff3e0', question: 'What key resources does your value proposition require?' },
    valuePropositions: { label: 'Value Propositions', icon: '🎁', color: '#fce4ec', question: 'What value do you deliver to the customer?' },
    customerRelationships: { label: 'Customer Relationships', icon: '💬', color: '#f3e5f5', question: 'What type of relationship does each segment expect?' },
    channels: { label: 'Channels', icon: '📦', color: '#e0f7fa', question: 'How do you reach your customer segments?' },
    customerSegments: { label: 'Customer Segments', icon: '👥', color: '#fff8e1', question: 'For whom are you creating value?' },
    costStructure: { label: 'Cost Structure', icon: '💰', color: '#ffebee', question: 'What are the most important costs?' },
    revenueStreams: { label: 'Revenue Streams', icon: '💵', color: '#e8f5e9', question: 'For what value are customers willing to pay?' }
  }

  // Lean Canvas sections (alternative)
  const leanSections = {
    problem: { label: 'Problem', icon: '❓', color: '#ffebee', question: 'Top 3 problems' },
    solution: { label: 'Solution', icon: '💡', color: '#e8f5e9', question: 'Top 3 features' },
    keyMetrics: { label: 'Key Metrics', icon: '📊', color: '#e3f2fd', question: 'Key activities you measure' },
    uniqueValue: { label: 'Unique Value Proposition', icon: '🎯', color: '#fce4ec', question: 'Single, clear message' },
    unfairAdvantage: { label: 'Unfair Advantage', icon: '🛡️', color: '#f3e5f5', question: "Can't be easily copied" },
    channels: { label: 'Channels', icon: '📦', color: '#e0f7fa', question: 'Path to customers' },
    customerSegments: { label: 'Customer Segments', icon: '👥', color: '#fff8e1', question: 'Target customers' },
    costStructure: { label: 'Cost Structure', icon: '💰', color: '#ffebee', question: 'Customer acquisition, hosting, etc.' },
    revenueStreams: { label: 'Revenue Streams', icon: '💵', color: '#e8f5e9', question: 'Revenue model, lifetime value' }
  }

  const sections = variant === 'lean' ? leanSections : bmcSections

  // Handle adding item to section
  const handleAddItem = (sectionKey) => {
    if (!editValue.trim()) return

    const newData = { ...canvasData }
    if (!newData[sectionKey]) newData[sectionKey] = []
    newData[sectionKey] = [...newData[sectionKey], editValue.trim()]

    setCanvasData(newData)
    setEditValue('')
    setEditingSection(null)

    if (callAction) {
      callAction({
        name: 'canvas_updated',
        payload: { section: sectionKey, data: newData }
      })
    }
  }

  // Handle removing item
  const handleRemoveItem = (sectionKey, index) => {
    const newData = { ...canvasData }
    newData[sectionKey] = newData[sectionKey].filter((_, i) => i !== index)
    setCanvasData(newData)

    if (callAction) {
      callAction({
        name: 'canvas_updated',
        payload: { section: sectionKey, data: newData }
      })
    }
  }

  // Export canvas as text
  const handleExport = () => {
    let text = `# ${title}\n\n`
    Object.entries(sections).forEach(([key, config]) => {
      text += `## ${config.icon} ${config.label}\n`
      const items = canvasData[key] || []
      if (items.length > 0) {
        items.forEach(item => { text += `- ${item}\n` })
      } else {
        text += `- (empty)\n`
      }
      text += '\n'
    })

    navigator.clipboard.writeText(text)
    if (callAction) {
      callAction({ name: 'toast', payload: { message: 'Canvas copied to clipboard!' } })
    }
  }

  // Styles
  const containerStyle = {
    backgroundColor: '#ffffff',
    borderRadius: '12px',
    padding: '16px',
    border: '1px solid #e0e0e0',
    fontFamily: 'system-ui, -apple-system, sans-serif'
  }

  const headerStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px'
  }

  const titleStyle = {
    fontSize: '20px',
    fontWeight: '600',
    color: '#333'
  }

  const buttonStyle = {
    padding: '6px 12px',
    fontSize: '12px',
    borderRadius: '6px',
    border: '1px solid #ddd',
    backgroundColor: '#f5f5f5',
    cursor: 'pointer',
    minHeight: '44px',  // Minimum touch target
    minWidth: '44px'
  }

  // BMC Grid Layout
  const gridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(10, 1fr)',
    gridTemplateRows: 'repeat(3, minmax(120px, auto))',
    gap: '8px'
  }

  // Section component
  const Section = ({ sectionKey, gridArea }) => {
    const config = sections[sectionKey]
    const items = canvasData[sectionKey] || []
    const isEditing = editingSection === sectionKey

    return (
      <div style={{
        gridArea,
        backgroundColor: config.color,
        borderRadius: '8px',
        padding: '10px',
        border: '1px solid rgba(0,0,0,0.1)',
        minHeight: '100px',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <div style={{
          fontSize: '11px',
          fontWeight: '600',
          color: '#333',
          marginBottom: '6px',
          display: 'flex',
          alignItems: 'center',
          gap: '4px'
        }}>
          <span>{config.icon}</span>
          <span>{config.label}</span>
        </div>

        <div style={{ fontSize: '9px', color: '#666', marginBottom: '8px', fontStyle: 'italic' }}>
          {config.question}
        </div>

        <div style={{ flex: 1, overflowY: 'auto' }}>
          {items.map((item, index) => (
            <div key={index} style={{
              fontSize: '11px',
              padding: '4px 6px',
              backgroundColor: 'rgba(255,255,255,0.7)',
              borderRadius: '4px',
              marginBottom: '4px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <span>• {item}</span>
              {editable && (
                <button
                  onClick={() => handleRemoveItem(sectionKey, index)}
                  onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && handleRemoveItem(sectionKey, index)}
                  style={{
                    border: 'none',
                    background: 'none',
                    cursor: 'pointer',
                    color: '#999',
                    fontSize: '14px',
                    padding: '8px',
                    minWidth: '32px',
                    minHeight: '32px'
                  }}
                  aria-label={`Remove ${item} from ${config.label}`}
                  title={`Remove ${item}`}
                >×</button>
              )}
            </div>
          ))}
        </div>

        {editable && (
          <div style={{ marginTop: '8px' }}>
            {isEditing ? (
              <div style={{ display: 'flex', gap: '4px' }}>
                <input
                  type="text"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddItem(sectionKey)}
                  placeholder="Add item..."
                  style={{
                    flex: 1,
                    padding: '4px 8px',
                    fontSize: '11px',
                    border: '1px solid #ddd',
                    borderRadius: '4px'
                  }}
                  autoFocus
                />
                <button
                  onClick={() => handleAddItem(sectionKey)}
                  style={{
                    padding: '4px 8px',
                    fontSize: '11px',
                    border: 'none',
                    borderRadius: '4px',
                    backgroundColor: '#6366f1',
                    color: 'white',
                    cursor: 'pointer'
                  }}
                >+</button>
                <button
                  onClick={() => { setEditingSection(null); setEditValue('') }}
                  style={{
                    padding: '4px 8px',
                    fontSize: '11px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    backgroundColor: 'white',
                    cursor: 'pointer'
                  }}
                >×</button>
              </div>
            ) : (
              <button
                onClick={() => setEditingSection(sectionKey)}
                onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && setEditingSection(sectionKey)}
                style={{
                  width: '100%',
                  padding: '8px',
                  fontSize: '11px',
                  border: '1px dashed #999',
                  borderRadius: '4px',
                  backgroundColor: 'transparent',
                  cursor: 'pointer',
                  color: '#666',
                  minHeight: '44px'
                }}
                aria-label={`Add item to ${config.label}`}
                title={`Add item to ${config.label}`}
              >+ Add</button>
            )}
          </div>
        )}
      </div>
    )
  }

  return (
    <div style={containerStyle} role="region" aria-labelledby="canvas-title">
      <div style={headerStyle}>
        <h2 style={titleStyle} id="canvas-title">{title}</h2>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            style={buttonStyle}
            onClick={handleExport}
            onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && handleExport()}
            aria-label="Copy canvas to clipboard"
            title="Copy canvas contents to clipboard"
          >
            📋 Copy
          </button>
        </div>
      </div>

      <div style={gridStyle} role="grid" aria-label="Business Model Canvas sections">
        {/* Row 1 */}
        <Section sectionKey="keyPartners" gridArea="1 / 1 / 3 / 3" />
        <Section sectionKey="keyActivities" gridArea="1 / 3 / 2 / 5" />
        <Section sectionKey="valuePropositions" gridArea="1 / 5 / 3 / 7" />
        <Section sectionKey="customerRelationships" gridArea="1 / 7 / 2 / 9" />
        <Section sectionKey="customerSegments" gridArea="1 / 9 / 3 / 11" />

        {/* Row 2 */}
        <Section sectionKey="keyResources" gridArea="2 / 3 / 3 / 5" />
        <Section sectionKey="channels" gridArea="2 / 7 / 3 / 9" />

        {/* Row 3 */}
        <Section sectionKey="costStructure" gridArea="3 / 1 / 4 / 6" />
        <Section sectionKey="revenueStreams" gridArea="3 / 6 / 4 / 11" />
      </div>

      {/* Instructions */}
      {editable && (
        <div style={{
          marginTop: '12px',
          padding: '8px 12px',
          backgroundColor: '#f8f9fa',
          borderRadius: '6px',
          fontSize: '11px',
          color: '#666'
        }}>
          💡 Click "+ Add" in any section to add items. Press Enter to save.
        </div>
      )}
    </div>
  )
}
