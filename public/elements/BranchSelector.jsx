/**
 * BranchSelector.jsx - Conversation Branch Navigation
 * Wave 2 of Mindrian Session Management
 *
 * Displays the conversation branch tree and allows switching between branches.
 * Uses inline styles for Chainlit compatibility (no external CSS).
 */

export default function BranchSelector() {
  const { callAction } = window.Chainlit || {};

  const {
    branches = [],
    activeBranchId = null,
    rootBranchId = null,
    forkPoints = [],
    showTree = true,
    compact = false,
  } = props || {};

  // Build tree structure from flat list
  const buildTree = (branchList, parentId = null) => {
    return branchList
      .filter((b) => b.parent_branch_id === parentId)
      .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
      .map((branch) => ({
        ...branch,
        children: buildTree(branchList, branch.branch_id),
      }));
  };

  const tree = buildTree(branches, null);

  const handleSwitch = (branchId) => {
    if (callAction && branchId !== activeBranchId) {
      callAction({ name: "switch_branch", payload: { branch_id: branchId } });
    }
  };

  const handleMerge = (sourceId) => {
    if (callAction && rootBranchId) {
      callAction({
        name: "merge_branches",
        payload: {
          source_branch_id: sourceId,
          target_branch_id: rootBranchId,
        },
      });
    }
  };

  const handleDelete = (branchId) => {
    if (callAction) {
      callAction({ name: "delete_branch", payload: { branch_id: branchId } });
    }
  };

  const handleCreate = () => {
    if (callAction) {
      callAction({ name: "fork_conversation", payload: {} });
    }
  };

  // Status indicators
  const statusIcons = {
    active: "●",
    paused: "○",
    merged: "◐",
    archived: "×",
  };

  const statusColors = {
    active: "#22c55e",
    paused: "#6b7280",
    merged: "#8b5cf6",
    archived: "#9ca3af",
  };

  // Styles
  const containerStyle = {
    backgroundColor: "#ffffff",
    borderRadius: "12px",
    padding: compact ? "12px" : "16px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
    maxWidth: compact ? "320px" : "400px",
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  };

  const headerStyle = {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "12px",
    paddingBottom: "8px",
    borderBottom: "1px solid #e5e7eb",
  };

  const titleStyle = {
    fontWeight: 600,
    fontSize: compact ? "14px" : "16px",
    color: "#111827",
    display: "flex",
    alignItems: "center",
    gap: "6px",
  };

  const createButtonStyle = {
    padding: "6px 12px",
    borderRadius: "6px",
    border: "1px solid #d1d5db",
    backgroundColor: "#ffffff",
    cursor: "pointer",
    fontSize: "13px",
    display: "flex",
    alignItems: "center",
    gap: "4px",
    transition: "all 0.15s ease",
  };

  const branchListStyle = {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  };

  // Render a single branch with its children
  const renderBranch = (branch, depth = 0) => {
    const isActive = branch.branch_id === activeBranchId;
    const isRoot = branch.branch_id === rootBranchId;
    const isMerged = branch.status === "merged";
    const isArchived = branch.status === "archived";

    const branchItemStyle = {
      paddingLeft: `${depth * 20}px`,
      display: "flex",
      alignItems: "center",
      gap: "8px",
      padding: compact ? "6px 8px" : "8px 12px",
      paddingLeft: `${depth * 20 + 8}px`,
      backgroundColor: isActive ? "#eff6ff" : "transparent",
      borderRadius: "6px",
      cursor: isMerged || isArchived ? "default" : "pointer",
      opacity: isArchived ? 0.5 : 1,
      border: isActive ? "1px solid #3b82f6" : "1px solid transparent",
      transition: "all 0.15s ease",
    };

    const branchTitleStyle = {
      flex: 1,
      fontWeight: isActive ? 600 : 400,
      fontSize: compact ? "13px" : "14px",
      color: isActive ? "#1d4ed8" : "#374151",
      textDecoration: isMerged ? "line-through" : "none",
    };

    const badgeStyle = {
      fontSize: "11px",
      color: "#6b7280",
      backgroundColor: "#f3f4f6",
      padding: "2px 6px",
      borderRadius: "4px",
    };

    const actionButtonStyle = {
      padding: "2px 6px",
      borderRadius: "4px",
      border: "none",
      backgroundColor: "transparent",
      cursor: "pointer",
      fontSize: "11px",
      color: "#6b7280",
      opacity: 0.6,
      transition: "opacity 0.15s ease",
    };

    return (
      <div key={branch.branch_id}>
        <div
          style={branchItemStyle}
          onClick={() =>
            !isMerged && !isArchived && handleSwitch(branch.branch_id)
          }
          onMouseEnter={(e) => {
            if (!isMerged && !isArchived) {
              e.currentTarget.style.backgroundColor = isActive
                ? "#eff6ff"
                : "#f9fafb";
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = isActive
              ? "#eff6ff"
              : "transparent";
          }}
        >
          {/* Status indicator */}
          <span
            style={{
              color: statusColors[branch.status] || "#6b7280",
              fontSize: "12px",
              minWidth: "14px",
            }}
          >
            {statusIcons[branch.status] || "○"}
          </span>

          {/* Branch title */}
          <span style={branchTitleStyle}>{branch.title}</span>

          {/* Message count badge */}
          <span style={badgeStyle}>
            {branch.message_count || 0} msg{branch.message_count !== 1 && "s"}
          </span>

          {/* Action buttons (only for non-root, non-active branches) */}
          {!isRoot && !isActive && !isMerged && !isArchived && (
            <>
              <button
                style={actionButtonStyle}
                onClick={(e) => {
                  e.stopPropagation();
                  handleMerge(branch.branch_id);
                }}
                title="Merge into main"
                onMouseEnter={(e) => (e.target.style.opacity = 1)}
                onMouseLeave={(e) => (e.target.style.opacity = 0.6)}
              >
                ⤴ merge
              </button>
              <button
                style={{ ...actionButtonStyle, color: "#ef4444" }}
                onClick={(e) => {
                  e.stopPropagation();
                  handleDelete(branch.branch_id);
                }}
                title="Archive branch"
                onMouseEnter={(e) => (e.target.style.opacity = 1)}
                onMouseLeave={(e) => (e.target.style.opacity = 0.6)}
              >
                ×
              </button>
            </>
          )}
        </div>

        {/* Render children */}
        {branch.children && branch.children.length > 0 && (
          <div style={{ marginTop: "2px" }}>
            {branch.children.map((child) => renderBranch(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  // Empty state
  if (branches.length === 0) {
    return (
      <div style={containerStyle}>
        <div style={headerStyle}>
          <span style={titleStyle}>🌿 Branches</span>
        </div>
        <div
          style={{ textAlign: "center", padding: "20px", color: "#6b7280" }}
        >
          <p style={{ margin: "0 0 12px 0", fontSize: "14px" }}>
            No branches yet
          </p>
          <button
            style={{
              ...createButtonStyle,
              margin: "0 auto",
              backgroundColor: "#3b82f6",
              color: "white",
              border: "none",
            }}
            onClick={handleCreate}
          >
            <span>+</span> Create Branch
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      {/* Header */}
      <div style={headerStyle}>
        <span style={titleStyle}>
          🌿 Branches
          <span
            style={{
              fontSize: "12px",
              color: "#6b7280",
              fontWeight: 400,
            }}
          >
            ({branches.length})
          </span>
        </span>
        <button
          style={createButtonStyle}
          onClick={handleCreate}
          onMouseEnter={(e) => {
            e.target.style.backgroundColor = "#f3f4f6";
          }}
          onMouseLeave={(e) => {
            e.target.style.backgroundColor = "#ffffff";
          }}
        >
          <span>+</span> Fork
        </button>
      </div>

      {/* Branch tree */}
      <div style={branchListStyle}>
        {tree.map((branch) => renderBranch(branch, 0))}
      </div>

      {/* Legend */}
      <div
        style={{
          marginTop: "12px",
          paddingTop: "8px",
          borderTop: "1px solid #e5e7eb",
          fontSize: "11px",
          color: "#9ca3af",
          display: "flex",
          gap: "12px",
          flexWrap: "wrap",
        }}
      >
        <span>
          <span style={{ color: statusColors.active }}>●</span> active
        </span>
        <span>
          <span style={{ color: statusColors.paused }}>○</span> paused
        </span>
        <span>
          <span style={{ color: statusColors.merged }}>◐</span> merged
        </span>
      </div>
    </div>
  );
}
