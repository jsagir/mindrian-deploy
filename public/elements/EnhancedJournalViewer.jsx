/**
 * EnhancedJournalViewer - Interactive Conversation Journal with Filtering & Search
 *
 * Enhanced version of JournalViewer with:
 * - Type filtering (badges)
 * - Text search
 * - Summarization button
 * - View Full button
 * - Entry expansion modal
 *
 * IMPORTANT: Uses inline styles only (Chainlit-safe, no shadcn imports)
 */

export default function EnhancedJournalViewer() {
    const { callAction } = window.Chainlit || {};

    // Props from Python
    const {
        entries = [],
        sessionId = "",
        botName = "Agent",
        isExpanded = true,
    } = props || {};

    // State
    const [filter, setFilter] = React.useState("");
    const [selectedTypes, setSelectedTypes] = React.useState([]);
    const [selectedEntry, setSelectedEntry] = React.useState(null);
    const [collapsed, setCollapsed] = React.useState(!isExpanded);

    // Entry type configuration
    const ENTRY_TYPES = {
        observation: { icon: "👁️", color: "#0ea5e9", bg: "#f0f9ff" },
        reasoning: { icon: "🧠", color: "#a855f7", bg: "#faf5ff" },
        decision: { icon: "✅", color: "#22c55e", bg: "#f0fdf4" },
        action: { icon: "⚡", color: "#f97316", bg: "#fff7ed" },
        insight: { icon: "💡", color: "#eab308", bg: "#fefce8" },
        switch: { icon: "🔄", color: "#3b82f6", bg: "#eff6ff" },
        extraction: { icon: "📋", color: "#6b7280", bg: "#f9fafb" },
    };

    // Filter entries
    const filteredEntries = React.useMemo(() => {
        if (!entries || entries.length === 0) return [];

        return entries.filter(entry => {
            const typeMatch = selectedTypes.length === 0 ||
                selectedTypes.includes(entry.entry_type?.toLowerCase());
            const textMatch = !filter ||
                entry.content?.toLowerCase().includes(filter.toLowerCase());
            return typeMatch && textMatch;
        });
    }, [entries, filter, selectedTypes]);

    // Toggle type filter
    const toggleType = (type) => {
        setSelectedTypes(prev =>
            prev.includes(type)
                ? prev.filter(t => t !== type)
                : [...prev, type]
        );
    };

    // Handlers
    const handleSummarize = () => {
        if (callAction) {
            callAction({ name: "summarize_journal", payload: { session_id: sessionId } });
        }
    };

    const handleViewFull = () => {
        if (callAction) {
            callAction({ name: "view_full_journal", payload: { session_id: sessionId } });
        }
    };

    // Styles
    const styles = {
        container: {
            width: "300px",
            backgroundColor: "#ffffff",
            borderRadius: "12px",
            boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
            overflow: "hidden",
            fontFamily: "system-ui, -apple-system, sans-serif",
        },
        header: {
            padding: "12px 16px",
            background: "linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)",
            borderBottom: "1px solid #fcd34d",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
        },
        headerTitle: {
            display: "flex",
            alignItems: "center",
            gap: "8px",
            fontWeight: "600",
            fontSize: "14px",
            color: "#92400e",
        },
        chevron: {
            fontSize: "12px",
            color: "#92400e",
            transition: "transform 0.2s",
            transform: collapsed ? "rotate(0deg)" : "rotate(180deg)",
        },
        content: {
            maxHeight: collapsed ? "0" : "500px",
            overflow: "hidden",
            transition: "max-height 0.3s ease",
        },
        searchContainer: {
            padding: "8px 12px",
            borderBottom: "1px solid #e5e7eb",
        },
        searchInput: {
            width: "100%",
            padding: "8px 12px",
            border: "1px solid #d1d5db",
            borderRadius: "6px",
            fontSize: "13px",
            outline: "none",
        },
        filterContainer: {
            padding: "8px 12px",
            display: "flex",
            flexWrap: "wrap",
            gap: "4px",
            borderBottom: "1px solid #e5e7eb",
        },
        filterBadge: (type, isSelected) => ({
            padding: "4px 8px",
            borderRadius: "12px",
            fontSize: "11px",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "4px",
            backgroundColor: isSelected ? ENTRY_TYPES[type]?.color || "#6b7280" : "#f3f4f6",
            color: isSelected ? "#ffffff" : "#374151",
            border: "1px solid transparent",
            transition: "all 0.2s",
        }),
        entriesContainer: {
            maxHeight: "280px",
            overflowY: "auto",
            padding: "8px",
        },
        entry: (type) => ({
            padding: "10px 12px",
            marginBottom: "8px",
            borderRadius: "8px",
            backgroundColor: ENTRY_TYPES[type]?.bg || "#f9fafb",
            borderLeft: `3px solid ${ENTRY_TYPES[type]?.color || "#6b7280"}`,
            cursor: "pointer",
            transition: "all 0.2s",
        }),
        entryHeader: {
            display: "flex",
            alignItems: "center",
            gap: "6px",
            marginBottom: "4px",
        },
        entryIcon: {
            fontSize: "14px",
        },
        entryType: (type) => ({
            fontSize: "11px",
            fontWeight: "600",
            textTransform: "uppercase",
            letterSpacing: "0.5px",
            color: ENTRY_TYPES[type]?.color || "#6b7280",
        }),
        entryMeta: {
            fontSize: "10px",
            color: "#9ca3af",
            marginLeft: "auto",
        },
        entryContent: {
            fontSize: "13px",
            color: "#374151",
            lineHeight: "1.4",
            overflow: "hidden",
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
        },
        emptyState: {
            padding: "24px",
            textAlign: "center",
            color: "#9ca3af",
            fontSize: "13px",
        },
        footer: {
            padding: "10px 12px",
            borderTop: "1px solid #e5e7eb",
            backgroundColor: "#f9fafb",
            display: "flex",
            gap: "8px",
        },
        button: (primary) => ({
            flex: 1,
            padding: "8px 12px",
            border: primary ? "none" : "1px solid #d1d5db",
            borderRadius: "6px",
            backgroundColor: primary ? "#f59e0b" : "#ffffff",
            color: primary ? "#ffffff" : "#374151",
            fontSize: "12px",
            fontWeight: "500",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "4px",
            transition: "all 0.2s",
        }),
        modal: {
            position: "fixed",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            backgroundColor: "#ffffff",
            borderRadius: "12px",
            boxShadow: "0 20px 40px rgba(0,0,0,0.2)",
            padding: "20px",
            maxWidth: "500px",
            width: "90%",
            maxHeight: "80vh",
            overflowY: "auto",
            zIndex: 1000,
        },
        overlay: {
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0,0,0,0.5)",
            zIndex: 999,
        },
        modalHeader: {
            display: "flex",
            alignItems: "center",
            gap: "8px",
            marginBottom: "12px",
            paddingBottom: "12px",
            borderBottom: "1px solid #e5e7eb",
        },
        modalClose: {
            marginLeft: "auto",
            cursor: "pointer",
            fontSize: "24px",
            color: "#6b7280",
            lineHeight: 1,
        },
        modalContent: {
            fontSize: "14px",
            lineHeight: "1.6",
            color: "#374151",
            whiteSpace: "pre-wrap",
        },
        statsBar: {
            padding: "6px 12px",
            backgroundColor: "#fef3c7",
            fontSize: "11px",
            color: "#92400e",
            display: "flex",
            justifyContent: "space-between",
        },
    };

    // Get icon for type
    const getIcon = (type) => ENTRY_TYPES[type?.toLowerCase()]?.icon || "📝";

    return (
        <>
            <div style={styles.container}>
                {/* Header */}
                <div style={styles.header} onClick={() => setCollapsed(!collapsed)}>
                    <div style={styles.headerTitle}>
                        <span>📔</span>
                        <span>Context Journal</span>
                    </div>
                    <span style={styles.chevron}>▼</span>
                </div>

                {/* Content */}
                <div style={styles.content}>
                    {/* Stats Bar */}
                    <div style={styles.statsBar}>
                        <span>{entries.length} total entries</span>
                        <span>{filteredEntries.length} shown</span>
                    </div>

                    {/* Search */}
                    <div style={styles.searchContainer}>
                        <input
                            type="text"
                            placeholder="Search journal..."
                            style={styles.searchInput}
                            value={filter}
                            onChange={(e) => setFilter(e.target.value)}
                        />
                    </div>

                    {/* Type Filters */}
                    <div style={styles.filterContainer}>
                        {Object.keys(ENTRY_TYPES).map(type => (
                            <div
                                key={type}
                                style={styles.filterBadge(type, selectedTypes.includes(type))}
                                onClick={() => toggleType(type)}
                            >
                                <span>{ENTRY_TYPES[type].icon}</span>
                                <span>{type}</span>
                            </div>
                        ))}
                    </div>

                    {/* Entries */}
                    <div style={styles.entriesContainer}>
                        {filteredEntries.length === 0 ? (
                            <div style={styles.emptyState}>
                                {entries.length === 0
                                    ? "No entries yet. Journal will populate as the conversation progresses."
                                    : "No entries match your filters."}
                            </div>
                        ) : (
                            filteredEntries.slice(-15).reverse().map((entry, i) => (
                                <div
                                    key={i}
                                    style={styles.entry(entry.entry_type?.toLowerCase())}
                                    onClick={() => setSelectedEntry(entry)}
                                >
                                    <div style={styles.entryHeader}>
                                        <span style={styles.entryIcon}>
                                            {getIcon(entry.entry_type)}
                                        </span>
                                        <span style={styles.entryType(entry.entry_type?.toLowerCase())}>
                                            {entry.entry_type}
                                        </span>
                                        <span style={styles.entryMeta}>
                                            {entry.bot_id} • T{entry.turn_number || 0}
                                        </span>
                                    </div>
                                    <div style={styles.entryContent}>
                                        {entry.content}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>

                    {/* Footer Buttons */}
                    <div style={styles.footer}>
                        <button style={styles.button(false)} onClick={handleSummarize}>
                            ✨ Summarize
                        </button>
                        <button style={styles.button(true)} onClick={handleViewFull}>
                            📄 View Full
                        </button>
                    </div>
                </div>
            </div>

            {/* Entry Detail Modal */}
            {selectedEntry && (
                <>
                    <div style={styles.overlay} onClick={() => setSelectedEntry(null)} />
                    <div style={styles.modal}>
                        <div style={styles.modalHeader}>
                            <span style={{ fontSize: "24px" }}>
                                {getIcon(selectedEntry.entry_type)}
                            </span>
                            <div>
                                <div style={{ fontWeight: "600", fontSize: "16px" }}>
                                    {selectedEntry.entry_type?.charAt(0).toUpperCase() +
                                        selectedEntry.entry_type?.slice(1)}
                                </div>
                                <div style={{ fontSize: "12px", color: "#6b7280" }}>
                                    by {selectedEntry.bot_id} • Turn {selectedEntry.turn_number || "?"}
                                </div>
                            </div>
                            <span style={styles.modalClose} onClick={() => setSelectedEntry(null)}>
                                ×
                            </span>
                        </div>
                        <div style={styles.modalContent}>
                            {selectedEntry.content}
                        </div>
                        {selectedEntry.metadata && Object.keys(selectedEntry.metadata).length > 0 && (
                            <div style={{ marginTop: "12px", padding: "8px", backgroundColor: "#f3f4f6", borderRadius: "6px", fontSize: "12px" }}>
                                <strong>Metadata:</strong>
                                <pre style={{ margin: "4px 0 0 0", whiteSpace: "pre-wrap" }}>
                                    {JSON.stringify(selectedEntry.metadata, null, 2)}
                                </pre>
                            </div>
                        )}
                    </div>
                </>
            )}
        </>
    );
}
