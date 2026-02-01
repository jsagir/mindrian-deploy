/**
 * JournalViewer - Live Conversation Journal Display
 *
 * Shows the running context journal in a collapsible sidebar panel.
 * Users can see thinking steps, insights, and decisions as they happen.
 *
 * IMPORTANT: Uses inline styles only (Chainlit-safe, no shadcn imports)
 */

export default function JournalViewer() {
    const { callAction } = window.Chainlit || {};

    // Props from Python
    const {
        entries = [],
        sessionId = "",
        isExpanded = false,
        lastUpdated = "",
        agentName = "Agent",
    } = props || {};

    // State for expansion
    const [expanded, setExpanded] = React.useState(isExpanded);
    const [selectedEntry, setSelectedEntry] = React.useState(null);

    // Styles
    const styles = {
        container: {
            width: '280px',
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            overflow: 'hidden',
            fontFamily: 'system-ui, -apple-system, sans-serif',
            marginTop: '12px',
        },
        header: {
            padding: '12px 16px',
            backgroundColor: '#fef3c7',
            borderBottom: '1px solid #fcd34d',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
        },
        headerTitle: {
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontWeight: '600',
            fontSize: '14px',
            color: '#92400e',
        },
        headerIcon: {
            fontSize: '16px',
        },
        expandIcon: {
            fontSize: '12px',
            color: '#92400e',
            transition: 'transform 0.2s',
        },
        content: {
            maxHeight: expanded ? '400px' : '0',
            overflow: 'hidden',
            transition: 'max-height 0.3s ease',
        },
        entriesContainer: {
            padding: '8px',
            maxHeight: '350px',
            overflowY: 'auto',
        },
        entry: (type) => ({
            padding: '10px 12px',
            marginBottom: '8px',
            borderRadius: '8px',
            backgroundColor: getEntryColor(type).bg,
            borderLeft: `3px solid ${getEntryColor(type).border}`,
            cursor: 'pointer',
            transition: 'all 0.2s ease',
        }),
        entryHeader: {
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            marginBottom: '4px',
        },
        entryIcon: {
            fontSize: '14px',
        },
        entryType: {
            fontSize: '11px',
            fontWeight: '600',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
        },
        entryAgent: {
            fontSize: '10px',
            color: '#6b7280',
            marginLeft: 'auto',
        },
        entryContent: {
            fontSize: '13px',
            color: '#374151',
            lineHeight: '1.4',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
        },
        entryTime: {
            fontSize: '10px',
            color: '#9ca3af',
            marginTop: '4px',
        },
        emptyState: {
            padding: '20px',
            textAlign: 'center',
            color: '#9ca3af',
            fontSize: '13px',
        },
        footer: {
            padding: '8px 12px',
            borderTop: '1px solid #e5e7eb',
            backgroundColor: '#f9fafb',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
        },
        footerText: {
            fontSize: '10px',
            color: '#6b7280',
        },
        viewAllButton: {
            padding: '4px 8px',
            fontSize: '11px',
            backgroundColor: '#f59e0b',
            color: '#ffffff',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
        },
        modal: {
            position: 'fixed',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            boxShadow: '0 20px 40px rgba(0,0,0,0.2)',
            padding: '20px',
            maxWidth: '500px',
            maxHeight: '80vh',
            overflowY: 'auto',
            zIndex: 1000,
        },
        overlay: {
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            zIndex: 999,
        },
        modalHeader: {
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '12px',
            paddingBottom: '12px',
            borderBottom: '1px solid #e5e7eb',
        },
        modalClose: {
            marginLeft: 'auto',
            cursor: 'pointer',
            fontSize: '20px',
            color: '#6b7280',
        },
        modalContent: {
            fontSize: '14px',
            lineHeight: '1.6',
            color: '#374151',
            whiteSpace: 'pre-wrap',
        },
    };

    // Helper to get colors by entry type
    function getEntryColor(type) {
        const colors = {
            observation: { bg: '#f0f9ff', border: '#0ea5e9', icon: '👁️' },
            reasoning: { bg: '#faf5ff', border: '#a855f7', icon: '🧠' },
            decision: { bg: '#f0fdf4', border: '#22c55e', icon: '✅' },
            action: { bg: '#fff7ed', border: '#f97316', icon: '⚡' },
            insight: { bg: '#fefce8', border: '#eab308', icon: '💡' },
            switch: { bg: '#f0f9ff', border: '#3b82f6', icon: '🔄' },
            extraction: { bg: '#f5f5f5', border: '#6b7280', icon: '📋' },
        };
        return colors[type] || colors.observation;
    }

    // Get icon for entry type
    function getEntryIcon(type) {
        return getEntryColor(type).icon;
    }

    // Handle entry click
    const handleEntryClick = (entry) => {
        setSelectedEntry(entry);
    };

    // Handle view all
    const handleViewAll = () => {
        if (callAction) {
            callAction({
                name: 'view_full_journal',
                payload: { session_id: sessionId }
            });
        }
    };

    return (
        <>
            <div style={styles.container}>
                {/* Header - clickable to expand/collapse */}
                <div
                    style={styles.header}
                    onClick={() => setExpanded(!expanded)}
                >
                    <div style={styles.headerTitle}>
                        <span style={styles.headerIcon}>📔</span>
                        <span>Conversation Journal</span>
                    </div>
                    <span style={{
                        ...styles.expandIcon,
                        transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)'
                    }}>
                        ▼
                    </span>
                </div>

                {/* Content - collapsible */}
                <div style={styles.content}>
                    <div style={styles.entriesContainer}>
                        {entries.length === 0 ? (
                            <div style={styles.emptyState}>
                                No entries yet. Journal will populate as the conversation progresses.
                            </div>
                        ) : (
                            entries.slice(-10).reverse().map((entry, i) => (
                                <div
                                    key={i}
                                    style={styles.entry(entry.type)}
                                    onClick={() => handleEntryClick(entry)}
                                >
                                    <div style={styles.entryHeader}>
                                        <span style={styles.entryIcon}>
                                            {getEntryIcon(entry.type)}
                                        </span>
                                        <span style={{
                                            ...styles.entryType,
                                            color: getEntryColor(entry.type).border
                                        }}>
                                            {entry.type}
                                        </span>
                                        <span style={styles.entryAgent}>
                                            {entry.agent}
                                        </span>
                                    </div>
                                    <div style={styles.entryContent}>
                                        {entry.content}
                                    </div>
                                    {entry.timestamp && (
                                        <div style={styles.entryTime}>
                                            {entry.timestamp}
                                        </div>
                                    )}
                                </div>
                            ))
                        )}
                    </div>

                    {/* Footer */}
                    {entries.length > 0 && (
                        <div style={styles.footer}>
                            <span style={styles.footerText}>
                                {entries.length} entries
                            </span>
                            <button
                                style={styles.viewAllButton}
                                onClick={handleViewAll}
                            >
                                View Full Journal
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* Modal for expanded entry view */}
            {selectedEntry && (
                <>
                    <div
                        style={styles.overlay}
                        onClick={() => setSelectedEntry(null)}
                    />
                    <div style={styles.modal}>
                        <div style={styles.modalHeader}>
                            <span style={{ fontSize: '20px' }}>
                                {getEntryIcon(selectedEntry.type)}
                            </span>
                            <span style={{ fontWeight: '600' }}>
                                {selectedEntry.type.charAt(0).toUpperCase() + selectedEntry.type.slice(1)}
                            </span>
                            <span style={{ color: '#6b7280', fontSize: '13px' }}>
                                by {selectedEntry.agent}
                            </span>
                            <span
                                style={styles.modalClose}
                                onClick={() => setSelectedEntry(null)}
                            >
                                ×
                            </span>
                        </div>
                        <div style={styles.modalContent}>
                            {selectedEntry.content}
                        </div>
                        {selectedEntry.timestamp && (
                            <div style={{ ...styles.entryTime, marginTop: '12px' }}>
                                {selectedEntry.timestamp} — Turn {selectedEntry.turn || '?'}
                            </div>
                        )}
                    </div>
                </>
            )}
        </>
    );
}
