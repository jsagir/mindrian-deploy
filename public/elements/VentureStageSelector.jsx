/**
 * VentureStageSelector - Build Venture Stage Selection
 *
 * Stage selector for Build Venture entry point:
 * - Pre-opportunity (routes to brainstorming)
 * - Opportunity identified (JTBD, Ackoff)
 * - Well-defined problem (BMC, S-Curve)
 * - Ready to build (Execution)
 *
 * FIXED: Uses global callAction (NOT window.Chainlit)
 * FIXED: Consolidated to "mode_or_stage" callback
 */

export default function VentureStageSelector() {
    const { disabled = false, currentStage = null } = props || {};

    const stages = [
        {
            id: "pre_opportunity",
            icon: "🔍",
            label: "Pre-Opportunity",
            description: "Still looking for problems to solve",
            action: "Route to exploration mode",
            color: "#8b5cf6"
        },
        {
            id: "opportunity_identified",
            icon: "💡",
            label: "Opportunity Identified",
            description: "Found a problem, need to understand it deeply",
            action: "JTBD, Problem Validation",
            color: "#3b82f6"
        },
        {
            id: "well_defined_problem",
            icon: "🎯",
            label: "Well-Defined Problem",
            description: "Problem is clear, designing the business",
            action: "BMC, S-Curve, BONO",
            color: "#10b981"
        },
        {
            id: "ready_to_build",
            icon: "🚀",
            label: "Ready to Build",
            description: "Problem validated, solution designed",
            action: "Execution Planning",
            color: "#f97316"
        }
    ];

    const handleSelect = (stageId) => {
        if (disabled) return;
        // callAction is a global injected by Chainlit
        if (typeof callAction === 'function') {
            callAction({
                name: "mode_or_stage",
                payload: { stage: stageId }
            });
        }
    };

    const styles = {
        container: {
            padding: '16px',
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            border: '1px solid #e5e7eb',
        },
        header: {
            marginBottom: '16px',
        },
        title: {
            fontSize: '15px',
            fontWeight: '600',
            color: '#1f2937',
            marginBottom: '4px',
        },
        subtitle: {
            fontSize: '13px',
            color: '#6b7280',
        },
        stageList: {
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
        },
        stageCard: {
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px',
            borderRadius: '8px',
            border: '2px solid transparent',
            cursor: disabled ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s ease',
            backgroundColor: '#f9fafb',
        },
        stageIcon: {
            fontSize: '24px',
            width: '40px',
            height: '40px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: '8px',
            backgroundColor: '#ffffff',
        },
        stageInfo: {
            flex: 1,
        },
        stageLabel: {
            fontSize: '14px',
            fontWeight: '600',
            color: '#1f2937',
        },
        stageDesc: {
            fontSize: '12px',
            color: '#6b7280',
            marginTop: '2px',
        },
        stageAction: {
            fontSize: '11px',
            color: '#9ca3af',
            marginTop: '4px',
        },
        arrow: {
            fontSize: '18px',
            color: '#9ca3af',
        }
    };

    const [hoveredId, setHoveredId] = React.useState(null);

    return (
        <div style={styles.container}>
            <div style={styles.header}>
                <div style={styles.title}>📍 Where are you in your journey?</div>
                <div style={styles.subtitle}>Select your current stage:</div>
            </div>

            <div style={styles.stageList}>
                {stages.map(stage => (
                    <div
                        key={stage.id}
                        onClick={() => handleSelect(stage.id)}
                        onMouseEnter={() => setHoveredId(stage.id)}
                        onMouseLeave={() => setHoveredId(null)}
                        style={{
                            ...styles.stageCard,
                            borderColor: hoveredId === stage.id ? stage.color :
                                        currentStage === stage.id ? stage.color : 'transparent',
                            backgroundColor: currentStage === stage.id ? `${stage.color}10` : '#f9fafb',
                            opacity: disabled ? 0.6 : 1,
                        }}
                    >
                        <div style={{
                            ...styles.stageIcon,
                            boxShadow: hoveredId === stage.id ? `0 0 0 2px ${stage.color}20` : 'none'
                        }}>
                            {stage.icon}
                        </div>
                        <div style={styles.stageInfo}>
                            <div style={styles.stageLabel}>{stage.label}</div>
                            <div style={styles.stageDesc}>{stage.description}</div>
                            <div style={styles.stageAction}>→ {stage.action}</div>
                        </div>
                        <span style={styles.arrow}>›</span>
                    </div>
                ))}
            </div>
        </div>
    );
}
