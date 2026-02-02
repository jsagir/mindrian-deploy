/**
 * ModeToggle - Workshop/Sandbox Mode Switch
 *
 * Simple toggle button to switch between:
 * - Workshop: Guided, phase-by-phase
 * - Sandbox: Free exploration
 *
 * FIXED: Uses global callAction/updateElement (NOT window.Chainlit)
 * FIXED: Consolidated to "mode_or_stage" callback
 */

export default function ModeToggle() {
    const {
        currentMode = "sandbox",
        entryPoint = "brainstorming",
        disabled = false
    } = props || {};

    const modes = {
        workshop: {
            icon: "🎯",
            label: "Workshop",
            description: "Guided, phase-by-phase"
        },
        sandbox: {
            icon: "🔬",
            label: "Sandbox",
            description: "Free exploration"
        }
    };

    const handleToggle = () => {
        if (disabled) return;
        const newMode = currentMode === "workshop" ? "sandbox" : "workshop";

        // callAction is a global injected by Chainlit
        if (typeof callAction === 'function') {
            callAction({
                name: "mode_or_stage",
                payload: { mode: newMode }
            });
        }
        // updateElement is a global for optimistic UI
        if (typeof updateElement === 'function') {
            updateElement({ ...props, currentMode: newMode });
        }
    };

    const current = modes[currentMode] || modes.sandbox;
    const other = modes[currentMode === "workshop" ? "sandbox" : "workshop"];

    const styles = {
        container: {
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px 16px',
            backgroundColor: '#f9fafb',
            borderRadius: '8px',
            border: '1px solid #e5e7eb',
        },
        info: {
            flex: 1,
        },
        modeLabel: {
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '14px',
            fontWeight: '600',
            color: '#1f2937',
        },
        modeDesc: {
            fontSize: '12px',
            color: '#6b7280',
            marginTop: '2px',
        },
        button: {
            padding: '6px 12px',
            borderRadius: '6px',
            border: 'none',
            fontSize: '13px',
            fontWeight: '500',
            cursor: disabled ? 'not-allowed' : 'pointer',
            backgroundColor: disabled ? '#e5e7eb' : '#eef2ff',
            color: disabled ? '#9ca3af' : '#4f46e5',
            transition: 'all 0.2s ease',
        }
    };

    const [isHovered, setIsHovered] = React.useState(false);

    return (
        <div style={styles.container}>
            <div style={styles.info}>
                <div style={styles.modeLabel}>
                    <span>{current.icon}</span>
                    <span>{current.label} Mode</span>
                </div>
                <div style={styles.modeDesc}>{current.description}</div>
            </div>

            <button
                onClick={handleToggle}
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
                disabled={disabled}
                style={{
                    ...styles.button,
                    backgroundColor: isHovered && !disabled ? '#ddd6fe' : styles.button.backgroundColor
                }}
            >
                Switch to {other.label}
            </button>
        </div>
    );
}
