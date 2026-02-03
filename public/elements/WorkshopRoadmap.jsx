/**
 * WorkshopRoadmap - Simple Numbered Roadmap (Larry's Preference)
 *
 * "Just show a roadmap, call it a day."
 * - No checkmarks ✓
 * - No lines between steps
 * - No spinning wheels
 * - Simple numbered list showing where user is going
 *
 * IMPORTANT: Uses inline styles only (no shadcn imports for Chainlit compatibility)
 */

export default function WorkshopRoadmap() {
    // Chainlit APIs
    const { callAction } = window.Chainlit || {};

    // Props from Python
    const {
        phases = [],
        currentPhase = 0,
        botName = "Workshop",
    } = props || {};

    const totalPhases = phases.length;

    // Styles - intentionally minimal
    const styles = {
        container: {
            width: '260px',
            backgroundColor: '#ffffff',
            borderRadius: '8px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
            fontFamily: 'system-ui, -apple-system, sans-serif',
            padding: '16px',
        },
        title: {
            fontSize: '14px',
            fontWeight: '600',
            color: '#374151',
            marginBottom: '16px',
            paddingBottom: '8px',
            borderBottom: '1px solid #e5e7eb',
        },
        phaseList: {
            listStyle: 'none',
            padding: 0,
            margin: 0,
        },
        phaseItem: (isCurrent, isPast) => ({
            display: 'flex',
            alignItems: 'flex-start',
            gap: '12px',
            padding: '8px 0',
            cursor: isPast ? 'pointer' : 'default',
        }),
        phaseNumber: (isCurrent, isPast) => ({
            width: '24px',
            height: '24px',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '12px',
            fontWeight: '600',
            flexShrink: 0,
            backgroundColor: isCurrent ? '#4f46e5' : isPast ? '#e5e7eb' : '#f9fafb',
            color: isCurrent ? '#ffffff' : isPast ? '#6b7280' : '#9ca3af',
        }),
        phaseName: (isCurrent, isPast) => ({
            fontSize: '14px',
            fontWeight: isCurrent ? '600' : '400',
            color: isCurrent ? '#1f2937' : isPast ? '#6b7280' : '#9ca3af',
            lineHeight: '24px',
        }),
        navRow: {
            display: 'flex',
            gap: '8px',
            marginTop: '16px',
            paddingTop: '12px',
            borderTop: '1px solid #e5e7eb',
        },
        navButton: (isPrimary) => ({
            flex: 1,
            padding: '8px 12px',
            border: isPrimary ? 'none' : '1px solid #d1d5db',
            borderRadius: '6px',
            backgroundColor: isPrimary ? '#4f46e5' : '#ffffff',
            color: isPrimary ? '#ffffff' : '#374151',
            fontSize: '13px',
            fontWeight: '500',
            cursor: 'pointer',
        }),
    };

    const handlePhaseClick = (index) => {
        if (index < currentPhase && callAction) {
            callAction({ name: 'jump_to_phase', payload: { phase: index } });
        }
    };

    const handleNext = () => {
        if (currentPhase < totalPhases - 1 && callAction) {
            callAction({ name: 'next_phase', payload: {} });
        }
    };

    const handleBack = () => {
        if (currentPhase > 0 && callAction) {
            callAction({ name: 'prev_phase', payload: {} });
        }
    };

    return (
        <div style={styles.container}>
            <div style={styles.title}>{botName} Roadmap</div>

            <ul style={styles.phaseList}>
                {phases.map((phase, i) => {
                    const isCurrent = i === currentPhase;
                    const isPast = i < currentPhase;

                    return (
                        <li
                            key={i}
                            style={styles.phaseItem(isCurrent, isPast)}
                            onClick={() => isPast && handlePhaseClick(i)}
                        >
                            <span style={styles.phaseNumber(isCurrent, isPast)}>
                                {i + 1}
                            </span>
                            <span style={styles.phaseName(isCurrent, isPast)}>
                                {phase.name}
                            </span>
                        </li>
                    );
                })}
            </ul>

            <div style={styles.navRow}>
                {currentPhase > 0 && (
                    <button style={styles.navButton(false)} onClick={handleBack}>
                        ← Back
                    </button>
                )}
                {currentPhase < totalPhases - 1 ? (
                    <button style={styles.navButton(true)} onClick={handleNext}>
                        Next →
                    </button>
                ) : (
                    <button
                        style={styles.navButton(true)}
                        onClick={() => callAction?.({ name: 'synthesize_conversation', payload: {} })}
                    >
                        Complete
                    </button>
                )}
            </div>
        </div>
    );
}
