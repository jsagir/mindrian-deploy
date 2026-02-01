/**
 * WorkshopRoadmap - Chainlit-Safe Interactive Phase Navigation
 *
 * A custom sidebar component that replaces cl.TaskList with:
 * - Visual progress bar
 * - Click-to-navigate on completed phases
 * - Phase context summaries on hover
 * - Back/Next navigation
 * - AI-extracted insights per phase
 *
 * IMPORTANT: Uses inline styles only (no shadcn imports for Chainlit compatibility)
 */

export default function WorkshopRoadmap() {
    // Chainlit APIs
    const { callAction, updateElement } = window.Chainlit || {};

    // Props from Python
    const {
        phases = [],
        currentPhase = 0,
        botName = "Workshop",
        botIcon = "🎯",
        phaseContext = {},        // AI-extracted context per phase
        canGoBack = true,
        showInsights = true,
        completedInsights = [],   // Summary of what user accomplished
    } = props || {};

    // Calculations
    const totalPhases = phases.length;
    const completedPhases = phases.filter(p => p.status === 'done' || p.status === 'completed').length;
    const progressPercent = totalPhases > 0 ? (completedPhases / totalPhases) * 100 : 0;

    // Styles
    const styles = {
        container: {
            width: '300px',
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            overflow: 'hidden',
            fontFamily: 'system-ui, -apple-system, sans-serif',
        },
        header: {
            padding: '16px 20px',
            borderBottom: '1px solid #e5e7eb',
            background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
        },
        headerTitle: {
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '12px',
        },
        headerIcon: {
            fontSize: '20px',
        },
        headerText: {
            fontWeight: '600',
            fontSize: '16px',
            color: '#1e293b',
        },
        progressContainer: {
            marginTop: '8px',
        },
        progressLabel: {
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '12px',
            color: '#64748b',
            marginBottom: '6px',
        },
        progressBar: {
            height: '8px',
            backgroundColor: '#e2e8f0',
            borderRadius: '4px',
            overflow: 'hidden',
        },
        progressFill: {
            height: '100%',
            backgroundColor: '#6366f1',
            borderRadius: '4px',
            transition: 'width 0.4s ease',
            width: `${progressPercent}%`,
        },
        phaseList: {
            padding: '12px',
            maxHeight: '280px',
            overflowY: 'auto',
        },
        phaseItem: (isDone, isCurrent, isClickable) => ({
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '10px 12px',
            marginBottom: '4px',
            borderRadius: '8px',
            cursor: isClickable ? 'pointer' : 'default',
            transition: 'all 0.2s ease',
            backgroundColor: isCurrent ? '#eef2ff' : isDone ? '#f0fdf4' : '#f8fafc',
            border: isCurrent ? '2px solid #6366f1' : '1px solid transparent',
            opacity: !isDone && !isCurrent ? 0.6 : 1,
        }),
        phaseIcon: {
            flexShrink: 0,
            width: '24px',
            height: '24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: '50%',
        },
        phaseName: (isCurrent) => ({
            fontSize: '14px',
            fontWeight: isCurrent ? '600' : '400',
            color: isCurrent ? '#4338ca' : '#374151',
            flex: 1,
        }),
        phaseNumber: {
            fontSize: '11px',
            color: '#9ca3af',
            marginLeft: 'auto',
        },
        insightBox: {
            margin: '0 12px 12px',
            padding: '12px',
            backgroundColor: '#fefce8',
            borderRadius: '8px',
            border: '1px solid #fef08a',
        },
        insightTitle: {
            fontSize: '11px',
            fontWeight: '600',
            color: '#a16207',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            marginBottom: '6px',
        },
        insightText: {
            fontSize: '13px',
            color: '#713f12',
            lineHeight: '1.4',
        },
        navContainer: {
            padding: '12px 16px',
            borderTop: '1px solid #e5e7eb',
            display: 'flex',
            gap: '8px',
            backgroundColor: '#f8fafc',
        },
        navButton: (isPrimary, isDisabled) => ({
            flex: 1,
            padding: '10px 16px',
            border: isPrimary ? 'none' : '1px solid #d1d5db',
            borderRadius: '8px',
            backgroundColor: isDisabled ? '#e5e7eb' : isPrimary ? '#6366f1' : '#ffffff',
            color: isDisabled ? '#9ca3af' : isPrimary ? '#ffffff' : '#374151',
            fontSize: '14px',
            fontWeight: '500',
            cursor: isDisabled ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s ease',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '4px',
        }),
    };

    // Handlers
    const handlePhaseClick = (index) => {
        if (index <= currentPhase && callAction) {
            callAction({
                name: 'jump_to_phase',
                payload: { phase: index }
            });
        }
    };

    const handlePrevPhase = () => {
        if (currentPhase > 0 && callAction) {
            callAction({ name: 'prev_phase', payload: {} });
        }
    };

    const handleNextPhase = () => {
        if (currentPhase < totalPhases - 1 && callAction) {
            callAction({ name: 'next_phase', payload: {} });
        }
    };

    // Get phase icon
    const getPhaseIcon = (status, isCurrent) => {
        if (status === 'done' || status === 'completed') {
            return <span style={{ color: '#22c55e', fontSize: '16px' }}>✓</span>;
        }
        if (isCurrent) {
            return <span style={{ color: '#6366f1', fontSize: '14px' }}>●</span>;
        }
        return <span style={{ color: '#d1d5db', fontSize: '14px' }}>○</span>;
    };

    // Get current phase insight
    const currentInsight = phaseContext[currentPhase] || completedInsights[currentPhase];

    return (
        <div style={styles.container}>
            {/* Header */}
            <div style={styles.header}>
                <div style={styles.headerTitle}>
                    <span style={styles.headerIcon}>{botIcon}</span>
                    <span style={styles.headerText}>{botName}</span>
                </div>

                {/* Progress Bar */}
                <div style={styles.progressContainer}>
                    <div style={styles.progressLabel}>
                        <span>Phase {currentPhase + 1} of {totalPhases}</span>
                        <span>{Math.round(progressPercent)}%</span>
                    </div>
                    <div style={styles.progressBar}>
                        <div style={styles.progressFill} />
                    </div>
                </div>
            </div>

            {/* Phase List */}
            <div style={styles.phaseList}>
                {phases.map((phase, i) => {
                    const isDone = phase.status === 'done' || phase.status === 'completed';
                    const isCurrent = i === currentPhase;
                    const isClickable = i <= currentPhase;

                    return (
                        <div
                            key={i}
                            style={styles.phaseItem(isDone, isCurrent, isClickable)}
                            onClick={() => isClickable && handlePhaseClick(i)}
                            title={phaseContext[i] || phase.name}
                        >
                            <div style={{
                                ...styles.phaseIcon,
                                backgroundColor: isDone ? '#dcfce7' : isCurrent ? '#e0e7ff' : '#f3f4f6'
                            }}>
                                {getPhaseIcon(phase.status, isCurrent)}
                            </div>
                            <span style={styles.phaseName(isCurrent)}>{phase.name}</span>
                            <span style={styles.phaseNumber}>{i + 1}</span>
                        </div>
                    );
                })}
            </div>

            {/* AI Insight Box (if available) */}
            {showInsights && currentInsight && (
                <div style={styles.insightBox}>
                    <div style={styles.insightTitle}>💡 Phase Insight</div>
                    <div style={styles.insightText}>{currentInsight}</div>
                </div>
            )}

            {/* Navigation Buttons */}
            <div style={styles.navContainer}>
                <button
                    style={styles.navButton(false, !canGoBack || currentPhase === 0)}
                    onClick={handlePrevPhase}
                    disabled={!canGoBack || currentPhase === 0}
                >
                    ← Back
                </button>

                {currentPhase < totalPhases - 1 ? (
                    <button
                        style={styles.navButton(true, false)}
                        onClick={handleNextPhase}
                    >
                        Next →
                    </button>
                ) : (
                    <button
                        style={styles.navButton(true, false)}
                        onClick={() => callAction?.({ name: 'synthesize_conversation', payload: {} })}
                    >
                        ✓ Complete
                    </button>
                )}
            </div>
        </div>
    );
}
