/**
 * MermaidDiagram - Custom Chainlit element for rendering Mermaid diagrams
 *
 * Supports: mindmaps, flowcharts, sequence diagrams, class diagrams, etc.
 *
 * Props:
 *   - diagram: Mermaid syntax string
 *   - title: Optional title above diagram
 *   - theme: 'default', 'dark', 'forest', 'neutral' (default: 'default')
 */

export default function MermaidDiagram() {
  const { updateElement, callAction } = window.Chainlit || {}
  const {
    diagram = '',
    title = '',
    theme = 'default',
    diagramId = 'mermaid-' + Math.random().toString(36).substr(2, 9)
  } = props || {}

  const [svg, setSvg] = React.useState(null)
  const [error, setError] = React.useState(null)
  const [loading, setLoading] = React.useState(true)

  // Load and render Mermaid
  React.useEffect(() => {
    if (!diagram) {
      setLoading(false)
      return
    }

    const renderDiagram = async () => {
      try {
        // Load mermaid from CDN if not already loaded
        if (!window.mermaid) {
          const script = document.createElement('script')
          script.src = 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js'
          script.async = true
          await new Promise((resolve, reject) => {
            script.onload = resolve
            script.onerror = reject
            document.head.appendChild(script)
          })
        }

        // Initialize mermaid with theme
        window.mermaid.initialize({
          startOnLoad: false,
          theme: theme,
          securityLevel: 'loose',
          flowchart: {
            useMaxWidth: true,
            htmlLabels: true,
            curve: 'basis'
          },
          mindmap: {
            useMaxWidth: true,
            padding: 10
          }
        })

        // Render the diagram
        const { svg: renderedSvg } = await window.mermaid.render(diagramId, diagram)
        setSvg(renderedSvg)
        setError(null)
      } catch (err) {
        console.error('Mermaid render error:', err)
        setError(err.message || 'Failed to render diagram')
      } finally {
        setLoading(false)
      }
    }

    renderDiagram()
  }, [diagram, theme, diagramId])

  // Export as PNG
  const handleExport = () => {
    if (!svg) return

    const svgElement = document.querySelector(`#${diagramId}-container svg`)
    if (!svgElement) return

    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const img = new Image()
    const svgBlob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' })
    const url = URL.createObjectURL(svgBlob)

    img.onload = () => {
      canvas.width = img.width * 2
      canvas.height = img.height * 2
      ctx.fillStyle = 'white'
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height)

      const pngUrl = canvas.toDataURL('image/png')
      const link = document.createElement('a')
      link.download = `${title || 'diagram'}.png`
      link.href = pngUrl
      link.click()

      URL.revokeObjectURL(url)
    }
    img.src = url
  }

  // Copy Mermaid source
  const handleCopySource = () => {
    navigator.clipboard.writeText(diagram)
    if (callAction) {
      callAction({ name: 'toast', payload: { message: 'Mermaid code copied!' } })
    }
  }

  // Styles
  const containerStyle = {
    backgroundColor: '#ffffff',
    borderRadius: '12px',
    padding: '16px',
    border: '1px solid #e0e0e0',
    marginBottom: '16px'
  }

  const titleStyle = {
    fontSize: '16px',
    fontWeight: '600',
    color: '#333',
    marginBottom: '12px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  }

  const buttonGroupStyle = {
    display: 'flex',
    gap: '8px'
  }

  const buttonStyle = {
    padding: '4px 12px',
    fontSize: '12px',
    borderRadius: '6px',
    border: '1px solid #ddd',
    backgroundColor: '#f5f5f5',
    cursor: 'pointer',
    transition: 'all 0.2s'
  }

  const diagramContainerStyle = {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '200px',
    overflow: 'auto'
  }

  const errorStyle = {
    color: '#d32f2f',
    padding: '16px',
    backgroundColor: '#ffebee',
    borderRadius: '8px',
    fontSize: '14px'
  }

  const loadingStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '40px',
    color: '#666'
  }

  if (loading) {
    return (
      <div style={containerStyle}>
        <div style={loadingStyle}>
          <span>Rendering diagram...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={containerStyle}>
        {title && <div style={titleStyle}>{title}</div>}
        <div style={errorStyle}>
          <strong>Diagram Error:</strong> {error}
          <pre style={{ marginTop: '8px', fontSize: '12px', overflow: 'auto' }}>
            {diagram}
          </pre>
        </div>
      </div>
    )
  }

  return (
    <div style={containerStyle}>
      {(title || svg) && (
        <div style={titleStyle}>
          <span>{title}</span>
          {svg && (
            <div style={buttonGroupStyle}>
              <button style={buttonStyle} onClick={handleCopySource} title="Copy Mermaid code">
                Copy Code
              </button>
              <button style={buttonStyle} onClick={handleExport} title="Export as PNG">
                Export PNG
              </button>
            </div>
          )}
        </div>
      )}
      <div
        id={`${diagramId}-container`}
        style={diagramContainerStyle}
        dangerouslySetInnerHTML={{ __html: svg || '<p>No diagram content</p>' }}
      />
    </div>
  )
}
