/**
 * QuadrantChart - 2x2 Matrix visualization for PWS analysis
 *
 * Use cases: Risk/Impact, Effort/Value, Urgency/Importance, Assumption mapping
 *
 * Props:
 *   - title: Chart title
 *   - xLabel: X-axis label (e.g., "Certainty")
 *   - yLabel: Y-axis label (e.g., "Impact")
 *   - items: Array of {name, x, y, color?, size?} (x,y are 0-100)
 *   - quadrantLabels: {topLeft, topRight, bottomLeft, bottomRight}
 *   - quadrantColors: {topLeft, topRight, bottomLeft, bottomRight}
 */

export default function QuadrantChart() {
  const { callAction } = window.Chainlit || {}
  const {
    title = '2x2 Analysis',
    xLabel = 'X Axis',
    yLabel = 'Y Axis',
    items = [],
    quadrantLabels = {
      topLeft: 'High Y / Low X',
      topRight: 'High Y / High X',
      bottomLeft: 'Low Y / Low X',
      bottomRight: 'Low Y / High X'
    },
    quadrantColors = {
      topLeft: 'rgba(255, 193, 7, 0.15)',    // Yellow - caution
      topRight: 'rgba(76, 175, 80, 0.15)',   // Green - go
      bottomLeft: 'rgba(158, 158, 158, 0.15)', // Gray - ignore
      bottomRight: 'rgba(33, 150, 243, 0.15)'  // Blue - consider
    }
  } = props || {}

  const [hoveredItem, setHoveredItem] = React.useState(null)
  const [selectedItem, setSelectedItem] = React.useState(null)

  // Chart dimensions
  const width = 500
  const height = 400
  const padding = 50
  const chartWidth = width - padding * 2
  const chartHeight = height - padding * 2

  // Scale functions
  const scaleX = (val) => padding + (val / 100) * chartWidth
  const scaleY = (val) => height - padding - (val / 100) * chartHeight

  // Handle item click
  const handleItemClick = (item) => {
    setSelectedItem(item)
    if (callAction) {
      callAction({
        name: 'quadrant_item_selected',
        payload: { item }
      })
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

  const titleStyle = {
    fontSize: '18px',
    fontWeight: '600',
    color: '#333',
    marginBottom: '16px',
    textAlign: 'center'
  }

  const svgStyle = {
    display: 'block',
    margin: '0 auto'
  }

  const legendStyle = {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
    marginTop: '16px',
    justifyContent: 'center'
  }

  const legendItemStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    fontSize: '12px',
    color: '#666',
    padding: '4px 8px',
    backgroundColor: '#f5f5f5',
    borderRadius: '4px',
    cursor: 'pointer'
  }

  const tooltipStyle = {
    position: 'absolute',
    backgroundColor: 'rgba(0,0,0,0.8)',
    color: 'white',
    padding: '8px 12px',
    borderRadius: '6px',
    fontSize: '12px',
    pointerEvents: 'none',
    zIndex: 1000,
    maxWidth: '200px'
  }

  return (
    <div style={containerStyle}>
      <div style={titleStyle}>{title}</div>

      <svg width={width} height={height} style={svgStyle}>
        {/* Quadrant backgrounds */}
        <rect x={padding} y={padding} width={chartWidth/2} height={chartHeight/2}
              fill={quadrantColors.topLeft} />
        <rect x={padding + chartWidth/2} y={padding} width={chartWidth/2} height={chartHeight/2}
              fill={quadrantColors.topRight} />
        <rect x={padding} y={padding + chartHeight/2} width={chartWidth/2} height={chartHeight/2}
              fill={quadrantColors.bottomLeft} />
        <rect x={padding + chartWidth/2} y={padding + chartHeight/2} width={chartWidth/2} height={chartHeight/2}
              fill={quadrantColors.bottomRight} />

        {/* Quadrant labels */}
        <text x={padding + chartWidth/4} y={padding + 20} textAnchor="middle"
              fontSize="11" fill="#666" opacity="0.7">{quadrantLabels.topLeft}</text>
        <text x={padding + chartWidth*3/4} y={padding + 20} textAnchor="middle"
              fontSize="11" fill="#666" opacity="0.7">{quadrantLabels.topRight}</text>
        <text x={padding + chartWidth/4} y={height - padding - 10} textAnchor="middle"
              fontSize="11" fill="#666" opacity="0.7">{quadrantLabels.bottomLeft}</text>
        <text x={padding + chartWidth*3/4} y={height - padding - 10} textAnchor="middle"
              fontSize="11" fill="#666" opacity="0.7">{quadrantLabels.bottomRight}</text>

        {/* Axes */}
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding}
              stroke="#333" strokeWidth="2" />
        <line x1={padding} y1={padding} x2={padding} y2={height - padding}
              stroke="#333" strokeWidth="2" />

        {/* Center lines (dashed) */}
        <line x1={padding + chartWidth/2} y1={padding} x2={padding + chartWidth/2} y2={height - padding}
              stroke="#999" strokeWidth="1" strokeDasharray="4,4" />
        <line x1={padding} y1={padding + chartHeight/2} x2={width - padding} y2={padding + chartHeight/2}
              stroke="#999" strokeWidth="1" strokeDasharray="4,4" />

        {/* Axis labels */}
        <text x={width/2} y={height - 10} textAnchor="middle" fontSize="14" fontWeight="500" fill="#333">
          {xLabel} →
        </text>
        <text x={15} y={height/2} textAnchor="middle" fontSize="14" fontWeight="500" fill="#333"
              transform={`rotate(-90, 15, ${height/2})`}>
          {yLabel} →
        </text>

        {/* Scale markers */}
        <text x={padding} y={height - padding + 20} textAnchor="middle" fontSize="10" fill="#999">0</text>
        <text x={padding + chartWidth/2} y={height - padding + 20} textAnchor="middle" fontSize="10" fill="#999">50</text>
        <text x={width - padding} y={height - padding + 20} textAnchor="middle" fontSize="10" fill="#999">100</text>
        <text x={padding - 10} y={height - padding} textAnchor="end" fontSize="10" fill="#999">0</text>
        <text x={padding - 10} y={padding + chartHeight/2} textAnchor="end" fontSize="10" fill="#999">50</text>
        <text x={padding - 10} y={padding + 5} textAnchor="end" fontSize="10" fill="#999">100</text>

        {/* Data points */}
        {items.map((item, index) => {
          const cx = scaleX(item.x || 50)
          const cy = scaleY(item.y || 50)
          const r = item.size || 12
          const color = item.color || '#6366f1'
          const isHovered = hoveredItem === index
          const isSelected = selectedItem?.name === item.name

          return (
            <g key={index}>
              {/* Shadow/glow effect */}
              {(isHovered || isSelected) && (
                <circle cx={cx} cy={cy} r={r + 4}
                        fill={color} opacity="0.3" />
              )}
              {/* Main circle */}
              <circle
                cx={cx} cy={cy} r={r}
                fill={color}
                stroke={isSelected ? '#333' : 'white'}
                strokeWidth={isSelected ? 3 : 2}
                style={{ cursor: 'pointer', transition: 'all 0.2s' }}
                onMouseEnter={() => setHoveredItem(index)}
                onMouseLeave={() => setHoveredItem(null)}
                onClick={() => handleItemClick(item)}
              />
              {/* Label */}
              <text
                x={cx}
                y={cy + r + 14}
                textAnchor="middle"
                fontSize="11"
                fontWeight={isHovered ? '600' : '400'}
                fill="#333"
              >
                {item.name?.substring(0, 15)}{item.name?.length > 15 ? '...' : ''}
              </text>
            </g>
          )
        })}
      </svg>

      {/* Legend */}
      {items.length > 0 && (
        <div style={legendStyle}>
          {items.map((item, index) => (
            <div
              key={index}
              style={{
                ...legendItemStyle,
                backgroundColor: selectedItem?.name === item.name ? '#e0e0e0' : '#f5f5f5'
              }}
              onClick={() => handleItemClick(item)}
            >
              <span style={{
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                backgroundColor: item.color || '#6366f1'
              }} />
              <span>{item.name}</span>
              <span style={{ color: '#999' }}>({item.x}, {item.y})</span>
            </div>
          ))}
        </div>
      )}

      {/* Selected item details */}
      {selectedItem && (
        <div style={{
          marginTop: '16px',
          padding: '12px',
          backgroundColor: '#f8f9fa',
          borderRadius: '8px',
          borderLeft: `4px solid ${selectedItem.color || '#6366f1'}`
        }}>
          <strong>{selectedItem.name}</strong>
          <div style={{ fontSize: '13px', color: '#666', marginTop: '4px' }}>
            {xLabel}: {selectedItem.x} | {yLabel}: {selectedItem.y}
          </div>
          {selectedItem.description && (
            <div style={{ fontSize: '13px', marginTop: '8px' }}>
              {selectedItem.description}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
