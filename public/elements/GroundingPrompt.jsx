/**
 * GroundingPrompt - PWS Grounding Intervention Display
 *
 * Styled callout box for grounding checkpoints:
 * - pattern_check: Patterns emerging?
 * - synthesis: Ready to synthesize?
 * - bank_prompt: Save an opportunity?
 *
 * FIXED: Uses global callAction (NOT window.Chainlit)
 * FIXED: Consolidated to "grounding_response" callback
 */

export default function GroundingPrompt() {
    const {
        reason = "pattern_check",
        turnCount = 0,
        topics = [],
        prompt = ""
    } = props || {};

    const reasonConfig = {
        pattern_check: {
            icon: "🔍",
            title: "Pattern Check",
            color: "#f59e0b",
            bgColor: "#fffbeb"
        },
        synthesis: {
            icon: "🧩",
            title: "Synthesis Time",
            color: "#8b5cf6",
            bgColor: "#f5f3ff"
        },
        bank_prompt: {
            icon: "🏦",
            title: "Bank an Opportunity",
            color: "#10b981",
            bgColor: "#ecfdf5"
        },
        problem_validation: {
            icon: "⚠️",
            title: "Problem Validation Required",
            color: "#ef4444",
            bgColor: "#fef2f2"
        }
    };

    const config = reasonConfig[reason] || reasonConfig.pattern_check;

    const handleResponse = (action) => {
        // callAction is a global injected by Chainlit
        if (typeof callAction === 'function') {
            callAction({
                name: "grounding_response",
                payload: { action, reason, topics }
            });
        }
    };

    const styles = {
        container: {
            borderLeft: `4px solid ${config.color}`,
            backgroundColor: config.bgColor,
            padding: '16px',
            borderRadius: '0 8px 8px 0',
            marginBottom: '12px',
        },
        header: {
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '12px',
        },
        icon: {
            fontSize: '20px',
        },
        title: {
            fontWeight: '600',
            fontSize: '14px',
            color: config.color,
        },
        turnBadge: {
            marginLeft: 'auto',
            fontSize: '11px',
            padding: '2px 8px',
            borderRadius: '10px',
            backgroundColor: 'rgba(0,0,0,0.1)',
            color: '#6b7280',
        },
        content: {
            fontSize: '14px',
            lineHeight: '1.6',
            color: '#374151',
            whiteSpace: 'pre-wrap',
        },
        topicsSection: {
            marginTop: '12px',
            fontSize: '12px',
            color: '#6b7280',
        },
        topicList: {
            display: 'flex',
            flexWrap: 'wrap',
            gap: '6px',
            marginTop: '4px',
        },
        topicTag: {
            padding: '2px 8px',
            backgroundColor: 'rgba(0,0,0,0.05)',
            borderRadius: '4px',
            fontSize: '11px',
        },
        actions: {
            display: 'flex',
            gap: '8px',
            marginTop: '16px',
            flexWrap: 'wrap',
        },
        primaryBtn: {
            padding: '8px 16px',
            borderRadius: '6px',
            border: 'none',
            fontSize: '13px',
            fontWeight: '500',
            cursor: 'pointer',
            backgroundColor: config.color,
            color: '#ffffff',
        },
        secondaryBtn: {
            padding: '8px 16px',
            borderRadius: '6px',
            border: '1px solid #d1d5db',
            fontSize: '13px',
            fontWeight: '500',
            cursor: 'pointer',
            backgroundColor: 'transparent',
            color: '#6b7280',
        },
        bankBtn: {
            padding: '8px 16px',
            borderRadius: '6px',
            border: 'none',
            fontSize: '13px',
            fontWeight: '500',
            cursor: 'pointer',
            backgroundColor: '#10b981',
            color: '#ffffff',
        }
    };

    return (
        <div style={styles.container}>
            <div style={styles.header}>
                <span style={styles.icon}>{config.icon}</span>
                <span style={styles.title}>{config.title}</span>
                {turnCount > 0 && (
                    <span style={styles.turnBadge}>Turn {turnCount}</span>
                )}
            </div>

            <div style={styles.content}>{prompt}</div>

            {topics.length > 0 && (
                <div style={styles.topicsSection}>
                    Topics explored:
                    <div style={styles.topicList}>
                        {topics.slice(0, 5).map((topic, i) => (
                            <span key={i} style={styles.topicTag}>{topic}</span>
                        ))}
                        {topics.length > 5 && (
                            <span style={styles.topicTag}>+{topics.length - 5} more</span>
                        )}
                    </div>
                </div>
            )}

            <div style={styles.actions}>
                <button onClick={() => handleResponse('acknowledge')} style={styles.primaryBtn}>
                    Got it, let me think...
                </button>
                <button onClick={() => handleResponse('skip')} style={styles.secondaryBtn}>
                    Continue exploring
                </button>
                {reason === "bank_prompt" && (
                    <button onClick={() => handleResponse('bank')} style={styles.bankBtn}>
                        🏦 Bank Now
                    </button>
                )}
            </div>
        </div>
    );
}
