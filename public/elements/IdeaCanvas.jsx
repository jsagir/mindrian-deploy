/**
 * IdeaCanvas.jsx - Visual workspace for extracted ideas
 * Wave 3 of Mindrian Session Management
 *
 * Displays ideas extracted from conversation in a draggable, filterable canvas.
 * Supports tree, cluster, timeline, and type-column layouts.
 */

export default function IdeaCanvas() {
  const { callAction, updateElement } = window.Chainlit || {};

  const {
    nodes = [],
    layout = { positions: {}, zoom: 1, pan_x: 0, pan_y: 0 },
    viewMode = "tree",
    filters = {},
    currentBranchId = "main",
    editable = true,
    title = "Idea Canvas",
    compact = false,
  } = props || {};

  // Local state
  const [selectedNode, setSelectedNode] = React.useState(null);
  const [hoveredNode, setHoveredNode] = React.useState(null);
  const [localPositions, setLocalPositions] = React.useState(
    layout.positions || {}
  );
  const [isDragging, setIsDragging] = React.useState(false);
  const [dragNode, setDragNode] = React.useState(null);
  const [dragOffset, setDragOffset] = React.useState({ x: 0, y: 0 });
  const [currentZoom, setCurrentZoom] = React.useState(layout.zoom || 1);
  const [pan, setPan] = React.useState({
    x: layout.pan_x || 0,
    y: layout.pan_y || 0,
  });
  const [filterState, setFilterState] = React.useState({
    problem: true,
    insight: true,
    assumption: true,
    decision: true,
    question: true,
    starred_only: false,
    hide_pruned: true,
    ...filters,
  });
  const [currentViewMode, setCurrentViewMode] = React.useState(viewMode);

  // Canvas ref for mouse position calculations
  const canvasRef = React.useRef(null);

  // Canvas dimensions
  const canvasWidth = compact ? 400 : 800;
  const canvasHeight = compact ? 300 : 600;

  // Node colors and icons
  const typeStyles = {
    problem: {
      bg: "#fef2f2",
      border: "#ef4444",
      text: "#b91c1c",
      icon: "⚠️",
    },
    insight: {
      bg: "#fefce8",
      border: "#eab308",
      text: "#a16207",
      icon: "💡",
    },
    assumption: {
      bg: "#faf5ff",
      border: "#a855f7",
      text: "#7c3aed",
      icon: "❓",
    },
    decision: {
      bg: "#f0fdf4",
      border: "#22c55e",
      text: "#15803d",
      icon: "✅",
    },
    question: {
      bg: "#eff6ff",
      border: "#3b82f6",
      text: "#1d4ed8",
      icon: "🤔",
    },
  };

  // Filter visible nodes
  const visibleNodes = React.useMemo(() => {
    return nodes.filter((node) => {
      if (filterState.hide_pruned && node.pruned) return false;
      if (filterState.starred_only && !node.starred) return false;
      if (!filterState[node.node_type]) return false;
      return true;
    });
  }, [nodes, filterState]);

  // Calculate auto-layout if positions not provided
  React.useEffect(() => {
    if (Object.keys(localPositions).length === 0 && visibleNodes.length > 0) {
      const autoPositions = calculateAutoLayout(
        visibleNodes,
        currentViewMode,
        canvasWidth,
        canvasHeight
      );
      setLocalPositions(autoPositions);
    }
  }, [visibleNodes, currentViewMode]);

  // Auto-layout calculation
  function calculateAutoLayout(nodeList, mode, width, height) {
    const positions = {};
    if (nodeList.length === 0) return positions;

    if (mode === "timeline") {
      // Left-to-right by message index
      const sorted = [...nodeList].sort(
        (a, b) => (a.message_index || 0) - (b.message_index || 0)
      );
      const maxIdx =
        Math.max(...nodeList.map((n) => n.message_index || 0)) || 1;
      const indexCounts = {};

      sorted.forEach((node) => {
        const idx = node.message_index || 0;
        const count = indexCounts[idx] || 0;
        indexCounts[idx] = count + 1;

        positions[node.node_id] = {
          x: 50 + (idx / maxIdx) * (width - 100),
          y: height / 2 + count * 80 - 40,
        };
      });
    } else if (mode === "type") {
      // Columns by type
      const types = ["problem", "insight", "assumption", "decision", "question"];
      const colWidth = width / types.length;

      types.forEach((type, t) => {
        const typeNodes = nodeList.filter((n) => n.node_type === type);
        typeNodes.forEach((node, j) => {
          positions[node.node_id] = {
            x: colWidth / 2 + t * colWidth,
            y: 60 + j * 70,
          };
        });
      });
    } else if (mode === "cluster") {
      // Circular cluster by type
      const types = ["problem", "insight", "assumption", "decision", "question"];
      const centerX = width / 2;
      const centerY = height / 2;
      const radius = Math.min(width, height) * 0.3;

      types.forEach((type, t) => {
        const angle = (t / types.length) * 2 * Math.PI - Math.PI / 2;
        const clusterX = centerX + radius * Math.cos(angle);
        const clusterY = centerY + radius * Math.sin(angle);

        const typeNodes = nodeList.filter((n) => n.node_type === type);
        typeNodes.forEach((node, j) => {
          const offset = 35;
          const row = Math.floor(j / 3);
          const col = j % 3;
          positions[node.node_id] = {
            x: clusterX + (col - 1) * offset,
            y: clusterY + row * offset,
          };
        });
      });
    } else {
      // Tree layout (default)
      const roots = nodeList.filter((n) => !n.parent_node_id);
      const getChildren = (nodeId) =>
        nodeList.filter((n) => n.parent_node_id === nodeId);

      function layoutSubtree(node, x, y, w, depth = 0) {
        positions[node.node_id] = { x, y };
        const children = getChildren(node.node_id);
        if (children.length === 0) return;

        const childWidth = w / children.length;
        children.forEach((child, i) => {
          const childX = x - w / 2 + childWidth / 2 + i * childWidth;
          layoutSubtree(child, childX, y + 100, childWidth, depth + 1);
        });
      }

      const rootWidth = width / Math.max(roots.length, 1);
      roots.forEach((root, i) => {
        layoutSubtree(root, rootWidth / 2 + i * rootWidth, 50, rootWidth);
      });

      // Position orphan nodes (nodes without roots positioned)
      nodeList.forEach((node, idx) => {
        if (!positions[node.node_id]) {
          positions[node.node_id] = {
            x: 100 + (idx % 5) * 150,
            y: 100 + Math.floor(idx / 5) * 100,
          };
        }
      });
    }

    return positions;
  }

  // Drag handlers
  const handleMouseDown = (e, nodeId) => {
    if (!editable) return;
    e.preventDefault();

    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;

    const nodePos = localPositions[nodeId] || { x: 0, y: 0 };
    const mouseX = (e.clientX - rect.left) / currentZoom - pan.x;
    const mouseY = (e.clientY - rect.top) / currentZoom - pan.y;

    setDragOffset({
      x: mouseX - nodePos.x,
      y: mouseY - nodePos.y,
    });
    setIsDragging(true);
    setDragNode(nodeId);
  };

  const handleMouseMove = (e) => {
    if (!isDragging || !dragNode || !canvasRef.current) return;

    const rect = canvasRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / currentZoom - pan.x - dragOffset.x;
    const y = (e.clientY - rect.top) / currentZoom - pan.y - dragOffset.y;

    setLocalPositions((prev) => ({
      ...prev,
      [dragNode]: { x, y },
    }));
  };

  const handleMouseUp = () => {
    if (isDragging && dragNode && callAction) {
      callAction({
        name: "canvas_layout_updated",
        payload: { positions: localPositions },
      });
    }
    setIsDragging(false);
    setDragNode(null);
  };

  // Node actions
  const handleNodeClick = (node) => {
    setSelectedNode(node.node_id === selectedNode ? null : node.node_id);

    if (callAction) {
      callAction({
        name: "canvas_node_selected",
        payload: {
          node_id: node.node_id,
          message_id: node.message_id,
          message_index: node.message_index,
        },
      });
    }
  };

  const handleStar = (nodeId, e) => {
    e.stopPropagation();
    if (callAction) {
      callAction({
        name: "star_idea",
        payload: { node_id: nodeId },
      });
    }
  };

  const handlePrune = (nodeId, e) => {
    e.stopPropagation();
    if (callAction) {
      callAction({
        name: "prune_idea",
        payload: { node_id: nodeId },
      });
    }
  };

  const toggleFilter = (type) => {
    setFilterState((prev) => ({
      ...prev,
      [type]: !prev[type],
    }));
  };

  // Render a single node
  const renderNode = (node) => {
    const pos = localPositions[node.node_id] || { x: 100, y: 100 };
    const style = typeStyles[node.node_type] || typeStyles.insight;
    const isSelected = selectedNode === node.node_id;
    const isHovered = hoveredNode === node.node_id;
    const isDragTarget = dragNode === node.node_id;

    return (
      <g
        key={node.node_id}
        transform={`translate(${pos.x}, ${pos.y})`}
        onMouseDown={(e) => handleMouseDown(e, node.node_id)}
        onClick={() => handleNodeClick(node)}
        onMouseEnter={() => setHoveredNode(node.node_id)}
        onMouseLeave={() => setHoveredNode(null)}
        style={{ cursor: editable ? "grab" : "pointer" }}
      >
        {/* Connection lines to children */}
        {node.child_node_ids?.map((childId) => {
          const childPos = localPositions[childId];
          if (!childPos) return null;
          return (
            <line
              key={`line-${node.node_id}-${childId}`}
              x1={0}
              y1={30}
              x2={childPos.x - pos.x}
              y2={childPos.y - pos.y - 30}
              stroke="#d1d5db"
              strokeWidth={1}
              strokeDasharray={node.starred ? "0" : "4"}
            />
          );
        })}

        {/* Node card */}
        <rect
          x={-80}
          y={-30}
          width={160}
          height={60}
          rx={8}
          fill={style.bg}
          stroke={isSelected ? "#000" : isDragTarget ? "#6366f1" : style.border}
          strokeWidth={isSelected ? 2 : 1}
          style={{
            filter: isHovered
              ? "drop-shadow(0 4px 6px rgba(0,0,0,0.1))"
              : "none",
          }}
        />

        {/* Type icon */}
        <text
          x={-70}
          y={-10}
          fontSize={14}
          dominantBaseline="middle"
        >
          {style.icon}
        </text>

        {/* Content (truncated) */}
        <text
          x={-55}
          y={-10}
          fontSize={11}
          fill={style.text}
          dominantBaseline="middle"
          style={{ pointerEvents: "none" }}
        >
          {node.content.length > 20
            ? node.content.substring(0, 20) + "..."
            : node.content}
        </text>

        {/* Second line of content */}
        {node.content.length > 20 && (
          <text
            x={-70}
            y={8}
            fontSize={10}
            fill="#6b7280"
            dominantBaseline="middle"
            style={{ pointerEvents: "none" }}
          >
            {node.content.substring(20, 45)}
            {node.content.length > 45 ? "..." : ""}
          </text>
        )}

        {/* Star indicator */}
        {node.starred && (
          <text x={55} y={-20} fontSize={14}>
            ⭐
          </text>
        )}

        {/* Action buttons (on hover) */}
        {(isHovered || isSelected) && editable && (
          <>
            <circle
              cx={50}
              cy={20}
              r={10}
              fill="#fff"
              stroke={node.starred ? "#eab308" : "#d1d5db"}
              strokeWidth={1}
              onClick={(e) => handleStar(node.node_id, e)}
              style={{ cursor: "pointer" }}
            />
            <text
              x={50}
              y={24}
              fontSize={10}
              textAnchor="middle"
              style={{ pointerEvents: "none" }}
            >
              {node.starred ? "★" : "☆"}
            </text>

            <circle
              cx={70}
              cy={20}
              r={10}
              fill="#fff"
              stroke="#ef4444"
              strokeWidth={1}
              onClick={(e) => handlePrune(node.node_id, e)}
              style={{ cursor: "pointer" }}
            />
            <text
              x={70}
              y={24}
              fontSize={10}
              textAnchor="middle"
              fill="#ef4444"
              style={{ pointerEvents: "none" }}
            >
              ×
            </text>
          </>
        )}
      </g>
    );
  };

  // Styles
  const containerStyle = {
    backgroundColor: "#ffffff",
    borderRadius: "12px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
    overflow: "hidden",
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  };

  const headerStyle = {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "12px 16px",
    borderBottom: "1px solid #374151",
    backgroundColor: "#1f2937",
    color: "#f9fafb",
  };

  const filterBarStyle = {
    display: "flex",
    gap: "6px",
    flexWrap: "wrap",
  };

  const filterButtonStyle = {
    padding: "4px 10px",
    borderRadius: "12px",
    border: "1px solid",
    fontSize: "11px",
    cursor: "pointer",
    transition: "all 0.15s ease",
  };

  const viewModeStyle = {
    display: "flex",
    gap: "4px",
  };

  const viewModeButtonStyle = {
    padding: "4px 8px",
    borderRadius: "4px",
    border: "1px solid #4b5563",
    backgroundColor: "#374151",
    color: "#f9fafb",
    fontSize: "11px",
    cursor: "pointer",
  };

  // Empty state
  if (nodes.length === 0) {
    return (
      <div style={containerStyle}>
        <div style={headerStyle}>
          <span style={{ fontWeight: 600, fontSize: "14px" }}>
            🎨 {title}
          </span>
        </div>
        <div
          style={{
            padding: "40px",
            textAlign: "center",
            color: "#6b7280",
          }}
        >
          <p style={{ margin: "0 0 8px 0", fontSize: "14px" }}>
            No ideas extracted yet
          </p>
          <p style={{ margin: 0, fontSize: "12px" }}>
            Ideas will appear here as you explore
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      {/* Header */}
      <div style={headerStyle}>
        <span style={{ fontWeight: 600, fontSize: "14px", color: "#f9fafb" }}>
          🎨 {title}
          <span
            style={{
              marginLeft: "8px",
              fontSize: "12px",
              color: "#9ca3af",
              fontWeight: 400,
            }}
          >
            ({visibleNodes.length} ideas)
          </span>
        </span>

        {/* View mode selector */}
        <div style={viewModeStyle}>
          {["tree", "cluster", "timeline", "type"].map((mode) => (
            <button
              key={mode}
              onClick={() => {
                setCurrentViewMode(mode);
                const newPositions = calculateAutoLayout(
                  visibleNodes,
                  mode,
                  canvasWidth,
                  canvasHeight
                );
                setLocalPositions(newPositions);
              }}
              style={{
                ...viewModeButtonStyle,
                backgroundColor:
                  currentViewMode === mode ? "#e0e7ff" : "transparent",
                fontWeight: currentViewMode === mode ? 600 : 400,
              }}
            >
              {mode}
            </button>
          ))}
        </div>
      </div>

      {/* Filter bar */}
      <div
        style={{
          padding: "8px 16px",
          borderBottom: "1px solid #e5e7eb",
        }}
      >
        <div style={filterBarStyle}>
          {Object.entries(typeStyles).map(([type, style]) => (
            <button
              key={type}
              onClick={() => toggleFilter(type)}
              style={{
                ...filterButtonStyle,
                backgroundColor: filterState[type] ? style.bg : "#f5f5f5",
                borderColor: filterState[type] ? style.border : "#e0e0e0",
                color: filterState[type] ? style.text : "#9ca3af",
                opacity: filterState[type] ? 1 : 0.6,
              }}
            >
              {style.icon} {type}
            </button>
          ))}
          <button
            onClick={() =>
              setFilterState((prev) => ({
                ...prev,
                starred_only: !prev.starred_only,
              }))
            }
            style={{
              ...filterButtonStyle,
              backgroundColor: filterState.starred_only ? "#fef3c7" : "#f5f5f5",
              borderColor: filterState.starred_only ? "#f59e0b" : "#e0e0e0",
              color: filterState.starred_only ? "#b45309" : "#6b7280",
            }}
          >
            ⭐ {filterState.starred_only ? "All" : "Starred"}
          </button>
        </div>
      </div>

      {/* Canvas */}
      <div
        ref={canvasRef}
        style={{
          width: "100%",
          minWidth: canvasWidth,
          height: canvasHeight,
          overflow: "auto",
          position: "relative",
        }}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <svg
          width={canvasWidth}
          height={canvasHeight}
          style={{
            transform: `scale(${currentZoom}) translate(${pan.x}px, ${pan.y}px)`,
            transformOrigin: "0 0",
          }}
        >
          {/* Render nodes */}
          {visibleNodes.map(renderNode)}
        </svg>
      </div>

      {/* Footer with zoom controls */}
      <div
        style={{
          padding: "8px 16px",
          borderTop: "1px solid #e5e7eb",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          backgroundColor: "#f9fafb",
          fontSize: "11px",
          color: "#6b7280",
        }}
      >
        <span>
          Branch: {currentBranchId} • Drag nodes to reposition
        </span>
        <div style={{ display: "flex", gap: "4px", alignItems: "center" }}>
          <button
            onClick={() => setCurrentZoom((z) => Math.max(0.5, z - 0.1))}
            style={{
              padding: "2px 8px",
              border: "1px solid #d1d5db",
              borderRadius: "4px",
              backgroundColor: "#fff",
              cursor: "pointer",
            }}
          >
            −
          </button>
          <span style={{ minWidth: "40px", textAlign: "center" }}>
            {Math.round(currentZoom * 100)}%
          </span>
          <button
            onClick={() => setCurrentZoom((z) => Math.min(2, z + 0.1))}
            style={{
              padding: "2px 8px",
              border: "1px solid #d1d5db",
              borderRadius: "4px",
              backgroundColor: "#fff",
              cursor: "pointer",
            }}
          >
            +
          </button>
        </div>
      </div>
    </div>
  );
}
