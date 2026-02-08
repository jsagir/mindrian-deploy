/**
 * EntryPointSelector - Triple-Mode Welcome Flow
 *
 * Displays three entry point cards for users to select their journey:
 * - Brainstorming (exploration)
 * - Document Review (validation)
 * - Build Venture (execution)
 *
 * FIXED: Uses global callAction (Chainlit injects as global, NOT window.Chainlit)
 * FIXED: Consolidated to single "select_entry_point" callback
 */

export default function EntryPointSelector() {
    const { showWelcome = true, disabled = false } = props || {};

    const entryPoints = [
        {
            id: "brainstorming",
            icon: "🧠",
            label: "Explore Ideas",
            description: "Find problems worth solving",
            color: "#8B5CF6"
        },
        {
            id: "document_review",
            icon: "📄",
            label: "Get Feedback",
            description: "Validate your thinking",
            color: "#3B82F6"
        },
        {
            id: "build_venture",
            icon: "🚀",
            label: "Build Venture",
            description: "Execute on your opportunity",
            color: "#F97316"
        }
    ];

    const handleSelect = (entryPointId) => {
        if (disabled) return;
        // Chainlit injects callAction via window.Chainlit
        const { callAction } = window.Chainlit || {};
        if (typeof callAction === 'function') {
            callAction({
                name: "select_entry_point",
                payload: { entry_point: entryPointId }
            });
        } else {
            console.warn('[EntryPointSelector] callAction not available');
        }
    };

    const styles = {
        container: {
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            padding: '20px',
            maxWidth: '600px',
            margin: '0 auto',
        },
        header: {
            textAlign: 'center',
            marginBottom: '8px',
        },
        title: {
            fontSize: '24px',
            fontWeight: '700',
            color: '#1f2937',
            marginBottom: '8px',
        },
        subtitle: {
            fontSize: '14px',
            color: '#6b7280',
        },
        grid: {
            display: 'flex',
            flexDirection: 'row',
            flexWrap: 'wrap',
            justifyContent: 'center',
            gap: '16px',
        },
        // Each card takes ~30% width on desktop, full width on mobile
        cardWrapper: {
            flex: '1 1 180px',
            maxWidth: '200px',
            minWidth: '150px',
        },
        card: {
            padding: '20px 16px',
            borderRadius: '12px',
            border: '2px solid transparent',
            cursor: disabled ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s ease',
            textAlign: 'center',
            backgroundColor: '#ffffff',
            boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        },
        icon: {
            fontSize: '32px',
            marginBottom: '12px',
            display: 'block',
        },
        label: {
            fontSize: '16px',
            fontWeight: '600',
            color: '#1f2937',
            marginBottom: '4px',
        },
        description: {
            fontSize: '12px',
            color: '#6b7280',
        },
        footer: {
            textAlign: 'center',
            fontSize: '13px',
            color: '#9ca3af',
            marginTop: '8px',
        }
    };

    const [hoveredId, setHoveredId] = React.useState(null);

    return (
        <div style={styles.container}>
            {showWelcome && (
                <div style={styles.header}>
                    <div style={styles.title}>Welcome to Mindrian</div>
                    <div style={styles.subtitle}>Where are you today?</div>
                </div>
            )}

            <div style={styles.grid}>
                {entryPoints.map(ep => (
                    <div key={ep.id} style={styles.cardWrapper}>
                        <div
                            onClick={() => handleSelect(ep.id)}
                            onMouseEnter={() => setHoveredId(ep.id)}
                            onMouseLeave={() => setHoveredId(null)}
                            style={{
                                ...styles.card,
                                borderColor: hoveredId === ep.id ? ep.color : 'transparent',
                                transform: hoveredId === ep.id ? 'translateY(-2px)' : 'none',
                                boxShadow: hoveredId === ep.id ? '0 4px 12px rgba(0,0,0,0.15)' : '0 2px 8px rgba(0,0,0,0.08)',
                                opacity: disabled ? 0.6 : 1,
                            }}
                        >
                            <span style={styles.icon}>{ep.icon}</span>
                            <div style={styles.label}>{ep.label}</div>
                            <div style={styles.description}>{ep.description}</div>
                        </div>
                    </div>
                ))}
            </div>

            <div style={styles.footer}>
                Or just tell me what's on your mind.
            </div>
        </div>
    );
}
